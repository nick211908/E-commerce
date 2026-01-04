from beanie import Document, Indexed, DecimalAnnotation
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from decimal import Decimal

class ProductSize(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"

class ProductVariant(BaseModel):
    sku: str = Field(..., description="Stock Keeping Unit, unique per variant")
    size: ProductSize
    color: str
    stock_quantity: int = Field(..., ge=0)
    price_adjustment: DecimalAnnotation = Decimal("0.00")

class Product(Document):
    title: str
    description: str
    base_price: DecimalAnnotation
    slug: Indexed(str, unique=True)
    images: List[str] = []
    variants: List[ProductVariant] = []
    is_published: bool = True
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "products"
