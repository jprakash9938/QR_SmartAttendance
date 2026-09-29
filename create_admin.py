import asyncio
import os
import sys

# Add the project root to sys.path so app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import async_session_factory
from app.models.models import User, UserRole
from app.core.security import hash_password
from sqlalchemy import select

async def create_admin(name: str, email: str, password: str):
    async with async_session_factory() as session:
        # Check if email exists
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User with email {email} already exists.")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin user {email} created successfully!")

if __name__ == "__main__":
    name = "Admin"
    email = "gyanaranjan7591@gmail.com"
    password = "Gyana@7591"
    
    asyncio.run(create_admin(name, email, password))
