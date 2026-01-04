from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import get_settings

from app.auth.models import User
from app.product.models import Product
from app.cart.models import Cart
from app.order.models import Order

async def init_db():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGO_URI)
    
    # We will pass the specific database name from the URI or config
    # Beanie requires the database object, not just client
    database = client.get_default_database()
    
    # We will register models later when they are created
    await init_beanie(
        database=database,
        document_models=[
            User,
            Product,
            Cart,
            Order
        ]
    )
