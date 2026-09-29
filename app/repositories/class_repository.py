"""Repository layer for Class database operations."""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Class


class ClassRepository:
    """Data access layer for Class model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, class_id: int) -> Class | None:
        """Get class by ID."""
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def get_by_teacher(self, teacher_id: int) -> List[Class]:
        """Get all classes for a teacher."""
        result = await self.db.execute(
            select(Class).where(Class.teacher_id == teacher_id).order_by(Class.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, class_: Class) -> Class:
        """Create a new class."""
        self.db.add(class_)
        await self.db.commit()
        await self.db.refresh(class_)
        return class_
