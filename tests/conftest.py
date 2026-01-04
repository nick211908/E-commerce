import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.auth.models import User
from app.product.models import Product
from app.cart.models import Cart
from app.order.models import Order
from app.core.config import get_settings
import asyncio

settings = get_settings()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Initialize test database."""
    # Use a separate test database
    settings.MONGO_URI = settings.MONGO_URI.replace("tshirt_store", "tshirt_store_test")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client.get_default_database()
    
    await init_beanie(
        database=database,
        document_models=[
            User,
            Product,
            Cart,
            Order
        ]
    )
    yield database
    # Cleanup after tests
    await client.drop_database("tshirt_store_test")

@pytest.fixture
async def client(test_db):
    """Async client fixture."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
