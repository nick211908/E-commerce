from httpx import AsyncClient
from app.auth.models import User, UserRole
from app.auth.security import get_password_hash
import uuid

async def create_user_token(client: AsyncClient, role: UserRole = UserRole.USER) -> str:
    email = f"user_{uuid.uuid4()}@example.com"
    password = "password123"
    fullname = "Test User"
    
    # Insert user directly
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=fullname,
        role=role
    )
    await user.insert()
    
    response = await client.post("/auth/token", data={
        "username": email,
        "password": password
    })
    return response.json()["access_token"]

async def create_product(client: AsyncClient, admin_token: str, sku: str = "SKU-1"):
    headers = {"Authorization": f"Bearer {admin_token}"}
    slug = f"prod-{uuid.uuid4()}"
    payload = {
        "title": "Test Product",
        "description": "Desc",
        "base_price": 10.0,
        "slug": slug,
        "variants": [
            {
                "sku": sku,
                "size": "M",
                "color": "Red",
                "stock_quantity": 100
            }
        ],
        "is_published": True
    }
    response = await client.post("/products/", json=payload, headers=headers)
    return response.json()
