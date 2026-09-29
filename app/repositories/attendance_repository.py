"""Repository layer for Attendance database operations."""

import math
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Attendance, AttendanceSession, AttendanceStatus, Class


class AttendanceRepository:
    """Data access layer for Attendance model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, attendance_id: int) -> Attendance | None:
        """Get attendance record by ID."""
        result = await self.db.execute(
            select(Attendance)
            .options(
                selectinload(Attendance.session).selectinload(AttendanceSession.class_)
            )
            .where(Attendance.id == attendance_id)
        )
        return result.scalar_one_or_none()

    async def get_by_student_and_session(
        self, student_id: int, session_id: int
    ) -> Attendance | None:
        """Check if student already has attendance for this session."""
        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.student_id == student_id,
                    Attendance.session_id == session_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, attendance: Attendance) -> Attendance:
        """Create a new attendance record.

        The database UNIQUE(student_id, session_id) constraint is the
        final protection against duplicates even under race conditions.
        """
        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def get_student_attendance(
        self,
        student_id: int,
        class_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Attendance], int]:
        """Get paginated attendance records for a student with filters."""
        query = (
            select(Attendance)
            .join(AttendanceSession, Attendance.session_id == AttendanceSession.id)
            .options(
                selectinload(Attendance.session).selectinload(AttendanceSession.class_)
            )
            .where(Attendance.student_id == student_id)
        )
        count_query = (
            select(func.count())
            .select_from(Attendance)
            .join(AttendanceSession, Attendance.session_id == AttendanceSession.id)
            .where(Attendance.student_id == student_id)
        )

        if class_id is not None:
            query = query.where(AttendanceSession.class_id == class_id)
            count_query = count_query.where(AttendanceSession.class_id == class_id)

        if date_from is not None:
            query = query.where(Attendance.marked_at >= date_from)
            count_query = count_query.where(Attendance.marked_at >= date_from)

        if date_to is not None:
            query = query.where(Attendance.marked_at <= date_to)
            count_query = count_query.where(Attendance.marked_at <= date_to)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Attendance.marked_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_today_attendance(self, student_id: int, today_start: datetime, today_end: datetime) -> List[Attendance]:
        """Get today's attendance records for a student."""
        result = await self.db.execute(
            select(Attendance)
            .options(
                selectinload(Attendance.session).selectinload(AttendanceSession.class_)
            )
            .where(
                and_(
                    Attendance.student_id == student_id,
                    Attendance.marked_at >= today_start,
                    Attendance.marked_at <= today_end,
                )
            )
            .order_by(Attendance.marked_at.desc())
        )
        return list(result.scalars().all())

    async def get_session_attendance(
        self, session_id: int
    ) -> List[Attendance]:
        """Get all attendance records for a session (for teacher dashboard)."""
        result = await self.db.execute(
            select(Attendance)
            .options(selectinload(Attendance.student))
            .where(Attendance.session_id == session_id)
            .order_by(Attendance.marked_at.asc())
        )
        return list(result.scalars().all())

    async def get_session_attendance_count(self, session_id: int) -> int:
        """Get count of attendance records for a session."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Attendance)
            .where(Attendance.session_id == session_id)
        )
        return result.scalar() or 0
