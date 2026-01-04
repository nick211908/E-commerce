from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.config import get_settings

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.product.router import router as product_router
from app.cart.router import router as cart_router
from app.order.router import router as order_router
from app.payment.router import router as payment_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

settings = get_settings()
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(cart_router, prefix="/cart", tags=["Cart"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])
app.include_router(payment_router, prefix="/stripe", tags=["Payment"])

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return {"message": "Welcome to the T-Shirt Store Backend"}
