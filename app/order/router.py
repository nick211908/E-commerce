from fastapi import APIRouter, Depends, HTTPException, status
from app.order.models import Order, OrderItem, ShippingAddress, OrderStatus
from app.cart.models import Cart
from app.product.models import Product
from app.auth.dependencies import get_current_active_user, User
from typing import List
from pydantic import BaseModel

from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class OrderCreate(BaseModel):
    shipping_address: ShippingAddress

from app.core.config import get_settings
import stripe

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateOrderResponse(BaseModel):
    order: Order
    client_secret: str

@router.post("/", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    user: User = Depends(get_current_active_user)
):
    # Start Transaction
    # note: Transactions require a MongoDB Replica Set
    client = Order.get_motor_client()
    async with client.start_session() as session:
        async with session.start_transaction():
            try:
                # 1. Fetch Cart
                cart = await Cart.find_one(Cart.user_id == user.id, session=session)
                if not cart or not cart.items:
                    raise HTTPException(status_code=400, detail="Cart is empty")

                order_items = []
                total_amount = Decimal("0.00")
                
                # 2. Process Items & Reserve Stock
                for item in cart.items:
                    # using config.get_settings().MONGO_URI might be needed if client is lost, but get_motor_client works
                    product = await Product.get(item.product_id, session=session)
                    if not product:
                        raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
                    
                    variant = next((v for v in product.variants if v.sku == item.variant_sku), None)
                    if not variant:
                        raise HTTPException(status_code=400, detail=f"Variant {item.variant_sku} not found")

                    # Atomic Decrement with session
                    result = await Product.find_one(
                        Product.id == product.id,
                        {"variants": {"$elemMatch": {"sku": item.variant_sku, "stock_quantity": {"$gte": item.quantity}}}}
                    , session=session).update(
                        {"$inc": {"variants.$.stock_quantity": -item.quantity}},
                        session=session
                    )

                    if result.modified_count == 0:
                        raise HTTPException(status_code=409, detail=f"Insufficient stock for {product.title} ({variant.size}/{variant.color})")
                    
                    # Calculate Price
                    # Convert float base_price to Decimal if needed, though model says DecimalAnnotation
                    # assuming it acts like Decimal or float compatible
                    price = Decimal(str(product.base_price)) + Decimal(str(variant.price_adjustment))
                    total_amount += price * Decimal(item.quantity)

                    # Add to Order Items (Snapshot)
                    order_items.append(OrderItem(
                        product_id=product.id,
                        variant_sku=item.variant_sku,
                        title=product.title,
                        size=variant.size,
                        color=variant.color,
                        unit_price=float(price), # Store as float for simple JSON serialization if needed
                        quantity=item.quantity
                    ))

                # 3. Create Stripe Payment Intent (External Call - keep outside transaction risk or handle carefully)
                # Ideally, we should create the intent *before* committing stock changes permanently or handle failures.
                # However, since we are in a transaction, if stripe fails, we abort and stock is safe.
                amount_cents = int(float(total_amount) * 100)
                
                try:
                    intent = stripe.PaymentIntent.create(
                        amount=amount_cents,
                        currency="usd",
                        metadata={"user_id": str(user.id)},
                        automatic_payment_methods={"enabled": True},
                    )
                except Exception as e:
                    logger.error(f"Stripe Error: {e}")
                    raise HTTPException(status_code=500, detail=f"Payment Gateway Error")

                # 4. Create Order
                order = Order(
                    user_id=user.id,
                    status=OrderStatus.PENDING,
                    items=order_items,
                    total_amount=float(total_amount),
                    shipping_address=order_in.shipping_address,
                    payment_intent_id=intent.id
                )
                await order.insert(session=session)
                
                # 5. Clear Cart
                await cart.delete(session=session)
                
                # Update metadata
                stripe.PaymentIntent.modify(
                    intent.id,
                    metadata={"order_id": str(order.id)}
                )
                
                return CreateOrderResponse(order=order, client_secret=intent.client_secret)

            except Exception as e:
                logger.error(f"Order creation failed: {e}")
                # Transaction will automatically abort when existing 'async with session.start_transaction()' block with error
                raise e

@router.get("/", response_model=List[Order])
async def list_orders(user: User = Depends(get_current_active_user)):
    return await Order.find(Order.user_id == user.id).sort(-Order.created_at).to_list()
