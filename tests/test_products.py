import pytest
from httpx import AsyncClient
from app.auth.models import User, UserRole
from app.auth.security import get_password_hash
from decimal import Decimal

@pytest.fixture
async def admin_token(client: AsyncClient):
    # Create admin user directly in DB
    admin_data = {
        "email": "admin@example.com",
        "password": "adminpass",
        "full_name": "Admin User",
        "role": UserRole.ADMIN
    }
    user = User(
        email=admin_data["email"],
        password_hash=get_password_hash(admin_data["password"]),
        full_name=admin_data["full_name"],
        role=admin_data["role"]
    )
    await user.insert()
    
    # Login to get token
    response = await client.post("/auth/token", data={
        "username": admin_data["email"],
        "password": admin_data["password"]
    })
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "title": "Test T-Shirt",
        "description": "A cool t-shirt",
        "base_price": 29.99,
        "slug": "test-t-shirt",
        "variants": [
            {
                "sku": "TS-BLK-M",
                "size": "M",
                "color": "Black",
                "stock_quantity": 100
            }
        ],
        "is_published": True
    }
    
    response = await client.post("/products/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == payload["slug"]
    assert len(data["variants"]) == 1

@pytest.mark.asyncio
async def test_create_product_duplicate_slug(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "title": "Test T-Shirt",
        "description": "A cool t-shirt",
        "base_price": 29.99,
        "slug": "unique-slug",
        "variants": []
    }
    await client.post("/products/", json=payload, headers=headers)
    
    # Try again
    response = await client.post("/products/", json=payload, headers=headers)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, admin_token: str):
    # Create published product
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/products/", json={
        "title": "P1", "description": "D1", "base_price": 10.0, "slug": "p1", "variants": []
    }, headers=headers)
    
    response = await client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    slug = "single-product"
    await client.post("/products/", json={
        "title": "P", "description": "D", "base_price": 10.0, "slug": slug, "variants": []
    }, headers=headers)
    
    response = await client.get(f"/products/{slug}")
    assert response.status_code == 200
    assert response.json()["slug"] == slug

@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient):
    response = await client.get("/products/non-existent")
    assert response.status_code == 404
