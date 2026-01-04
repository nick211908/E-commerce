from fastapi import APIRouter, Depends, HTTPException, status
from app.cart.models import Cart, CartItem
from app.auth.dependencies import get_current_active_user, User
from app.product.models import Product
from pydantic import BaseModel
from beanie import PydanticObjectId
from datetime import datetime

router = APIRouter()

class AddToCartRequest(BaseModel):
    product_id: str
    variant_sku: str
    quantity: int

class CartResponse(BaseModel):
    id: str
    items: list
    updated_at: datetime

@router.get("/", response_model=Cart)
async def get_cart(user: User = Depends(get_current_active_user)):
    cart = await Cart.find_one(Cart.user_id == user.id)
    if not cart:
        cart = Cart(user_id=user.id)
        await cart.insert()
    return cart

@router.post("/items", response_model=Cart)
async def add_item_to_cart(
    item_in: AddToCartRequest,
    user: User = Depends(get_current_active_user)
):
    # Validate Product and Variant existence
    try:
        product_id = PydanticObjectId(item_in.product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Find variant
    variant = next((v for v in product.variants if v.sku == item_in.variant_sku), None)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    if variant.stock_quantity < item_in.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    cart = await Cart.find_one(Cart.user_id == user.id)
    if not cart:
        cart = Cart(user_id=user.id)
    
    # Check if item exists in cart
    existing_item = next(
        (i for i in cart.items if i.product_id == product_id and i.variant_sku == item_in.variant_sku),
        None
    )

    if existing_item:
        existing_item.quantity += item_in.quantity
        # Optional: Check if new total quantity exceeds stock
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
    return cart

@router.delete("/items/{product_id}/{variant_sku}", response_model=Cart)
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
    return cart
