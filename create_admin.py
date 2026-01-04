import asyncio
from app.core.database import init_db
from app.auth.models import User, UserRole
from app.auth.security import get_password_hash

async def create_admin():
    print("Initializing database connection...")
    await init_db()
    
    import os
    email = os.getenv("ADMIN_EMAIL", "pandeyayush4101@gmail.com")
    
    # Securely get password
    env_password = os.getenv("ADMIN_PASSWORD")
    if env_password:
        password = env_password
    else:
        # Fallback to input if running interactively, else error or use a secure default if really needed (not recommended)
        try:
            from getpass import getpass
            password = getpass(f"Enter password for {email}: ")
        except:
             print("Error: ADMIN_PASSWORD environment variable not set and non-interactive mode.")
             return
    
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
