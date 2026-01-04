from fastapi import APIRouter, Depends, HTTPException, status
from app.cart.models import Cart, CartItem
from app.auth.dependencies import get_current_active_user, User
from app.product.models import Product
from pydantic import BaseModel
from beanie import PydanticObjectId
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

router = APIRouter()

class AddToCartRequest(BaseModel):
    product_id: str
    variant_sku: str
    quantity: int

class CartItemDetail(BaseModel):
    product_id: str
    variant_sku: str
    quantity: int
    added_at: datetime
    title: str
    price: float
    image: Optional[str] = None

class CartDetailResponse(BaseModel):
    id: str
    user_id: str
    items: List[CartItemDetail]
    updated_at: datetime
    total_price: float

async def get_cart_with_details(cart: Cart) -> CartDetailResponse:
    if not cart.items:
        return CartDetailResponse(
            id=str(cart.id),
            user_id=str(cart.user_id),
            items=[],
            updated_at=cart.updated_at,
            total_price=0.0
        )

    product_ids = list(set([item.product_id for item in cart.items]))
    products = await Product.find({"_id": {"$in": product_ids}}).to_list()
    product_map = {p.id: p for p in products}

    detailed_items = []
    total_cart_price = Decimal("0.00")

    for item in cart.items:
        product = product_map.get(item.product_id)
        if not product:
            continue 

        variant = next((v for v in product.variants if v.sku == item.variant_sku), None)
        price_adj = variant.price_adjustment if variant else Decimal("0.00")
        final_price = product.base_price + price_adj
        
        image = product.images[0] if product.images else None

        detailed_items.append(CartItemDetail(
            product_id=str(item.product_id),
            variant_sku=item.variant_sku,
            quantity=item.quantity,
            added_at=item.added_at,
            title=product.title,
            price=float(final_price),
            image=image
        ))
        
        total_cart_price += final_price * item.quantity

    return CartDetailResponse(
        id=str(cart.id),
        user_id=str(cart.user_id),
        items=detailed_items,
        updated_at=cart.updated_at,
        total_price=float(total_cart_price)
    )

@router.get("/", response_model=CartDetailResponse)
async def get_cart(user: User = Depends(get_current_active_user)):
    cart = await Cart.find_one(Cart.user_id == user.id)
    if not cart:
        cart = Cart(user_id=user.id)
        await cart.insert()
    return await get_cart_with_details(cart)

@router.post("/items", response_model=CartDetailResponse)
async def add_item_to_cart(
    item_in: AddToCartRequest,
    user: User = Depends(get_current_active_user)
):
    try:
        product_id = PydanticObjectId(item_in.product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    variant = next((v for v in product.variants if v.sku == item_in.variant_sku), None)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    if variant.stock_quantity < item_in.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    cart = await Cart.find_one(Cart.user_id == user.id)
    if not cart:
        cart = Cart(user_id=user.id)
    
    existing_item = next(
        (i for i in cart.items if i.product_id == product_id and i.variant_sku == item_in.variant_sku),
        None
    )

    if existing_item:
        existing_item.quantity += item_in.quantity
        if existing_item.quantity > variant.stock_quantity:
             raise HTTPException(status_code=400, detail="Total quantity exceeds stock")
    else:
        new_item = CartItem(
            product_id=product_id,
            variant_sku=item_in.variant_sku,
            quantity=item_in.quantity
        )
        cart.items.append(new_item)
    
    cart.updated_at = datetime.utcnow()
    await cart.save()
    return await get_cart_with_details(cart)

@router.delete("/items/{product_id}/{variant_sku}", response_model=CartDetailResponse)
async def remove_item_from_cart(
    product_id: str,
    variant_sku: str,
    user: User = Depends(get_current_active_user)
):
    cart = await Cart.find_one(Cart.user_id == user.id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    try:
        pid = PydanticObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")

    cart.items = [
        item for item in cart.items 
        if not (item.product_id == pid and item.variant_sku == variant_sku)
    ]
    
    cart.updated_at = datetime.utcnow()
    await cart.save()
    return await get_cart_with_details(cart)
