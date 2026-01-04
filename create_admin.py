import asyncio
from app.core.database import init_db
from app.auth.models import User, UserRole
from app.auth.security import get_password_hash

async def create_admin():
    print("Initializing database connection...")
    await init_db()
    
    email = "pandeyayush4101@gmail.com"
    password = "ayush@123"
    
    print(f"Checking for existing admin user: {email}")
    # Check if exists
    user = await User.find_one(User.email == email)
    if user:
        print(f"Admin user {email} already exists.")
        # Optional: ensure role is ADMIN
        if user.role != UserRole.ADMIN:
            print("Upgrading existing user to ADMIN.")
            user.role = UserRole.ADMIN
            await user.save()
        return

    print("Creating new admin user...")
    admin_user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name="Super Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    await admin_user.insert()
    print(f"Admin user created successfully!")
    print(f"Email: {email}")
    print(f"Password: {password}")

if __name__ == "__main__":
    asyncio.run(create_admin())
