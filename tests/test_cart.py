import pytest
from httpx import AsyncClient
from app.auth.models import UserRole
from tests.utils import create_user_token, create_product

@pytest.mark.asyncio
async def test_add_to_cart(client: AsyncClient):
    # Setup
    admin_token = await create_user_token(client, UserRole.ADMIN)
    user_token = await create_user_token(client, UserRole.USER)
    product = await create_product(client, admin_token, sku="CART-SKU")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "product_id": product["id"],
        "variant_sku": "CART-SKU",
        "quantity": 2
    }
    
    response = await client.post("/cart/items", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2

@pytest.mark.asyncio
async def test_get_cart(client: AsyncClient):
    user_token = await create_user_token(client, UserRole.USER)
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = await client.get("/cart/", headers=headers)
    assert response.status_code == 200
    # Should be empty initially
    assert len(response.json()["items"]) == 0

@pytest.mark.asyncio
async def test_remove_from_cart(client: AsyncClient):
    # Setup
    admin_token = await create_user_token(client, UserRole.ADMIN)
    user_token = await create_user_token(client, UserRole.USER)
    product = await create_product(client, admin_token, sku="DEL-SKU")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    # Add item
    await client.post("/cart/items", json={
        "product_id": product["id"],
        "variant_sku": "DEL-SKU",
        "quantity": 1
    }, headers=headers)
    
    # Remove item
    response = await client.delete(f"/cart/items/{product['id']}/DEL-SKU", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0
