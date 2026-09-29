"""Repository layer for AttendanceSession database operations."""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import AttendanceSession, SessionStatus


class SessionRepository:
    """Data access layer for AttendanceSession model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, session_id: int) -> AttendanceSession | None:
        """Get session by ID with class relationship loaded."""
        result = await self.db.execute(
            select(AttendanceSession)
            .options(selectinload(AttendanceSession.class_))
            .where(AttendanceSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_teacher(self, teacher_id: int) -> List[AttendanceSession]:
        """Get all sessions for classes owned by a teacher."""
        from app.models.models import Class

        result = await self.db.execute(
            select(AttendanceSession)
            .join(Class, AttendanceSession.class_id == Class.id)
            .where(Class.teacher_id == teacher_id)
            .order_by(AttendanceSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, session: AttendanceSession) -> AttendanceSession:
        """Create a new attendance session."""
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update_status(
        self, session_id: int, status: SessionStatus
    ) -> AttendanceSession | None:
        """Update session status."""
        session = await self.get_by_id(session_id)
        if session:
            session.status = status
            await self.db.commit()
            await self.db.refresh(session)
        return session
