# Backend API Documentation

This API powers the E-commerce backend.

## Base URL
`http://localhost:8000` (Local development)

## Authentication
Most endpoints responsible for user data require authentication via Bearer Token.

### Register User
**POST** `/auth/register`
- **Request Body** (`application/json`):
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword",
    "full_name": "John Doe"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "id": "user_id_string",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "USER",
    "is_active": true
  }
  ```

### Login (Get Token)
**POST** `/auth/token`
- **Request Body** (`application/x-www-form-urlencoded`):
  - `username`: Email address
  - `password`: Password
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "jwt_token_string",
    "token_type": "bearer"
  }
  ```

---

## Products

### List Products
**GET** `/products/?skip=0&limit=20`
- **Query Params**:
  - `skip`: Number of items to skip (default 0)
  - `limit`: Max items to return (default 20)
- **Response** (`200 OK`):
  ```json
  [
    {
      "id": "product_id",
      "title": "T-Shirt",
      "description": "A cool t-shirt",
      "base_price": 20.00,
      "slug": "t-shirt",
      "variants": [
        {
          "sku": "TSHIRT-BLK-S",
          "size": "S",
          "color": "Black",
          "stock_quantity": 100,
          "price_adjustment": 0.00
        }
      ],
      "is_published": true,
      "created_at": "timestamp"
    }
  ]
  ```

### Get Product Details
**GET** `/products/{slug}`
- **Path Params**:
  - `slug`: Product slug (e.g., `t-shirt`)
- **Response** (`200 OK`): Same as single product object above.

### Create Product (Admin Only)
**POST** `/products/`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Request Body**:
  ```json
  {
    "title": "New Product",
    "description": "Product description",
    "base_price": 25.50,
    "slug": "new-product",
    "variants": [
      {
        "sku": "NEW-S",
        "size": "S",
        "color": "Red",
        "stock_quantity": 50,
        "price_adjustment": 0
      }
    ],
    "is_published": true
  }
  ```
- **Response** (`201 Created`): Created product object.

---

## Cart

### Get Cart
**GET** `/cart/`
- **Headers**: `Authorization: Bearer <user_token>`
- **Response** (`200 OK`):
  ```json
  {
    "id": "cart_id",
    "user_id": "user_id",
    "items": [
      {
        "product_id": "product_id",
        "variant_sku": "SKU-123",
        "quantity": 2,
        "added_at": "timestamp"
      }
    ],
    "updated_at": "timestamp"
  }
  ```

### Add Item to Cart
**POST** `/cart/items`
- **Headers**: `Authorization: Bearer <user_token>`
- **Request Body**:
  ```json
  {
    "product_id": "product_id_string",
    "variant_sku": "SKU-123",
    "quantity": 1
  }
  ```
- **Response** (`200 OK`): Updated cart object.

### Remove Item from Cart
**DELETE** `/cart/items/{product_id}/{variant_sku}`
- **Headers**: `Authorization: Bearer <user_token>`
- **Response** (`200 OK`): Updated cart object.

---

## Orders

### Create Order
**POST** `/orders/`
- **Headers**: `Authorization: Bearer <user_token>`
- **Request Body**:
  ```json
  {
    "shipping_address": {
      "full_name": "Jane Doe",
      "address_line_1": "123 Main St",
      "address_line_2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "zip_code": "10001",
      "country": "USA"
    }
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "id": "order_id",
    "user_id": "user_id",
    "status": "PENDING",
    "items": [
      {
        "product_id": "pid",
        "variant_sku": "sku",
        "title": "Product Title",
        "size": "M",
        "color": "Blue",
        "unit_price": 20.00,
        "quantity": 1
      }
    ],
    "total_amount": 20.00,
    "currency": "USD",
    "shipping_address": { ... },
    "created_at": "timestamp"
  }
  ```

### List My Orders
**GET** `/orders/`
- **Headers**: `Authorization: Bearer <user_token>`
- **Response** (`200 OK`): List of order objects.

---

## Payment

### Stripe Webhook
**POST** `/stripe/webhook`
- Used by Stripe to notify backend of payment events (e.g., `payment_intent.succeeded`).
