import pytest
from httpx import AsyncClient
from app.auth.models import UserRole
from tests.utils import create_user_token, create_product

@pytest.mark.asyncio
async def test_create_order(client: AsyncClient):
    # Setup
    admin_token = await create_user_token(client, UserRole.ADMIN)
    user_token = await create_user_token(client, UserRole.USER)
    product = await create_product(client, admin_token, sku="ORDER-SKU")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Add to cart
    await client.post("/cart/items", json={
        "product_id": product["id"],
        "variant_sku": "ORDER-SKU",
        "quantity": 1
    }, headers=headers)
    
    # Checkout
    payload = {
        "shipping_address": {
            "full_name": "Buyer",
            "address_line1": "123 St",
            "city": "City",
            "postal_code": "10001",
            "country": "US"
        }
    }
    response = await client.post("/orders/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert len(data["items"]) == 1

@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient):
    user_token = await create_user_token(client, UserRole.USER)
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = await client.get("/orders/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
