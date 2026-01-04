from beanie import Document, Indexed, PydanticObjectId
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class CartItem(BaseModel):
    product_id: PydanticObjectId
    variant_sku: str
    quantity: int = Field(..., gt=0)
    added_at: datetime = datetime.utcnow()

class Cart(Document):
    user_id: Indexed(PydanticObjectId, unique=True)
    items: List[CartItem] = []
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "carts"
        indexes = [
            # TTL index for automatic expiration after 7 days (604800 seconds)
            [("updated_at", 1), ("expireAfterSeconds", 604800)]
        ]
