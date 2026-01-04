from beanie import Document, Indexed
from pydantic import EmailStr
from datetime import datetime
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class User(Document):
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None

    class Settings:
        name = "users"
