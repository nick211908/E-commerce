from fastapi import APIRouter, Depends, HTTPException, status
from app.order.models import Order, OrderItem, ShippingAddress, OrderStatus
from app.cart.models import Cart
from app.product.models import Product
from app.auth.dependencies import get_current_active_user, User
from typing import List
from pydantic import BaseModel

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
    # 1. Fetch Cart
    cart = await Cart.find_one(Cart.user_id == user.id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order_items = []
    total_amount = 0
    reserved_items = []

    # 2. Process Items & Reserve Stock
    try:
        for item in cart.items:
            product = await Product.get(item.product_id)
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            
            variant = next((v for v in product.variants if v.sku == item.variant_sku), None)
            if not variant:
                raise HTTPException(status_code=400, detail=f"Variant {item.variant_sku} not found")

            # Atomic Decrement
            # Filter matches: ID, SKU, and Stock >= Qty
            result = await Product.find_one(
                Product.id == product.id,
                {"variants": {"$elemMatch": {"sku": item.variant_sku, "stock_quantity": {"$gte": item.quantity}}}}
            ).update(
                {"$inc": {"variants.$.stock_quantity": -item.quantity}}
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=409, detail=f"Insufficient stock for {product.title} ({variant.size}/{variant.color})")
            
            # Record reservation for rollback
            reserved_items.append({
                "product_id": product.id,
                "variant_sku": item.variant_sku,
                "quantity": item.quantity
            })

            # Calculate Price
            price = product.base_price + variant.price_adjustment
            total_amount += price * item.quantity

            # Add to Order Items (Snapshot)
            order_items.append(OrderItem(
                product_id=product.id,
                variant_sku=item.variant_sku,
                title=product.title,
                size=variant.size,
                color=variant.color,
                unit_price=price,
                quantity=item.quantity
            ))

        # 3. Create Stripe Payment Intent
        # Stripe expects amount in cents
        amount_cents = int(total_amount * 100)
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                metadata={"user_id": str(user.id)},
                automatic_payment_methods={"enabled": True},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stripe Error: {str(e)}")

        # 4. Create Order
        order = Order(
            user_id=user.id,
            status=OrderStatus.PENDING,
            items=order_items,
            total_amount=total_amount,
            shipping_address=order_in.shipping_address,
            payment_intent_id=intent.id
        )
        await order.insert()
        
        # Update metadata with order_id after creation
        stripe.PaymentIntent.modify(
            intent.id,
            metadata={"order_id": str(order.id)}
        )

        # 5. Clear Cart
        await cart.delete()
        
        return CreateOrderResponse(order=order, client_secret=intent.client_secret)

    except Exception as e:
        # Rollback Inventory
        for res in reserved_items:
            await Product.find_one(
                Product.id == res["product_id"],
                {"variants.sku": res["variant_sku"]}
            ).update(
                {"$inc": {"variants.$.stock_quantity": res["quantity"]}}
            )
        raise e

@router.get("/", response_model=List[Order])
async def list_orders(user: User = Depends(get_current_active_user)):
    return await Order.find(Order.user_id == user.id).sort(-Order.created_at).to_list()
