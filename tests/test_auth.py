import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    payload = {
        "email": "test@example.com",
        "password": "strongpassword123",
        "full_name": "Test User"
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "role" in data

@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient):
    # Register first user
    payload = {
        "email": "duplicate@example.com",
        "password": "strongpassword123",
        "full_name": "Test User"
    }
    await client.post("/auth/register", json=payload)
    
    # Try to register again
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    # Register user
    email = "login@example.com"
    password = "loginpassword123"
    await client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Login User"
    })
    
    # Login
    response = await client.post("/auth/token", data={
        "username": email,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    # Register user
    email = "wrongpass@example.com"
    password = "correctpassword"
    await client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "User"
    })
    
    # Login with wrong password
    response = await client.post("/auth/token", data={
        "username": email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401
