"""Repository layer for User database operations.

All database access goes through repositories to keep business logic
in services and SQL injection protection via ORM parameterized queries.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User


class UserRepository:
    """Data access layer for User model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        result = await self.db.execute(select(User.id).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def get_all(self):
        """Get all users."""
        result = await self.db.execute(select(User).order_by(User.created_at.desc()))
        return result.scalars().all()
