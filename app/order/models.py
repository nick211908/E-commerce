from beanie import Document, Indexed, PydanticObjectId, DecimalAnnotation
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import List, Optional
from decimal import Decimal

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class ShippingAddress(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str

class OrderItem(BaseModel):
    product_id: PydanticObjectId
    variant_sku: str
    title: str
    size: str
    color: str
    unit_price: DecimalAnnotation
    quantity: int

class Order(Document):
    user_id: Indexed(PydanticObjectId)
    status: OrderStatus = OrderStatus.PENDING
    items: List[OrderItem] = []
    total_amount: DecimalAnnotation
    currency: str = "USD"
    shipping_address: ShippingAddress
    payment_intent_id: Optional[str] = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "orders"
