from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from app.product.models import Product, ProductVariant
from app.auth.dependencies import get_current_admin_user
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from beanie import PydanticObjectId
import shutil
import os
import uuid

router = APIRouter()

# Schemas for Request/Response
class ProductVariantCreate(BaseModel):
    sku: str
    size: str
    color: str
    stock_quantity: int
    price_adjustment: Optional[Decimal] = Decimal("0.00")

class ProductCreate(BaseModel):
    title: str
    description: str
    base_price: Decimal
    slug: str
    variants: List[ProductVariantCreate] = []
    images: List[str] = []
    is_published: bool = True

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    variants: Optional[List[ProductVariantCreate]] = None
    images: Optional[List[str]] = None
    is_published: Optional[bool] = None

# Routes

@router.post("/upload")
async def upload_image(file: UploadFile = File(...), admin = Depends(get_current_admin_user)):
    file.filename = f"{uuid.uuid4()}.jpg"
    upload_dir = "app/static/uploads"
    file_path = f"{upload_dir}/{file.filename}"
    
    # Ensure directory exists (redundant if created via mkdir but safe)
    os.makedirs(upload_dir, exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/uploads/{file.filename}"}
@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product_in: ProductCreate, admin = Depends(get_current_admin_user)):
    existing_product = await Product.find_one(Product.slug == product_in.slug)
    if existing_product:
        raise HTTPException(status_code=400, detail="Product slug already exists")
    
    # Check for duplicate SKUs in request
    skus = [v.sku for v in product_in.variants]
    if len(skus) != len(set(skus)):
        raise HTTPException(status_code=400, detail="Duplicate SKUs in variants")

    if not product_in.variants:
        raise HTTPException(status_code=400, detail="At least one variant is required")

    product = Product(**product_in.dict())
    await product.insert()
    return product

@router.get("/", response_model=List[Product])
async def list_products(skip: int = 0, limit: int = 20):
    return await Product.find(Product.is_published == True).skip(skip).limit(limit).to_list()

@router.get("/{slug}", response_model=Product)
async def get_product(slug: str):
    product = await Product.find_one(Product.slug == slug, Product.is_published == True)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_in: ProductUpdate,
    admin = Depends(get_current_admin_user)
):
    try:
        pid = PydanticObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product = await Product.get(pid)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_in.dict(exclude_unset=True)
    
    # If variants are being updated, we might want to validate them similar to create
    # For now, we trust the admin input or basic pydantic validation
    if product_in.variants is not None and len(product_in.variants) == 0:
        raise HTTPException(status_code=400, detail="Cannot remove all variants. Delete the product instead.")
    
    await product.set(update_data)
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    admin = Depends(get_current_admin_user)
):
    try:
        pid = PydanticObjectId(product_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid product ID")

    product = await Product.get(pid)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    
    # Delete associated images
    if product.images:
        for image_url in product.images:
            try:
                # Remove '/static/uploads/' prefix to get filename
                if image_url.startswith("/static/uploads/"):
                    filename = image_url.replace("/static/uploads/", "")
                    file_path = f"app/static/uploads/{filename}"
                    if os.path.exists(file_path):
                        os.remove(file_path)
            except Exception as e:
                print(f"Error deleting image {image_url}: {e}")

    await product.delete()
    return None
