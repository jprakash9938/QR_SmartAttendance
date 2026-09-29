"""Attendance service — business logic for marking and querying attendance."""

import math
from datetime import datetime, time, timezone
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.models import Attendance, AttendanceSession, AttendanceStatus, SessionStatus, User, ClassRoster
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.schemas import (
    AttendanceCountResponse,
    AttendanceDetailResponse,
    AttendanceMarkRequest,
    AttendanceMarkResponse,
    AttendanceResponse,
    AttendanceStudentInfo,
    PaginatedResponse,
    SessionAttendanceListResponse,
)
from app.services.qr_service import QRTokenService
from app.services.session_service import SessionService


class AttendanceService:
    """Service handling attendance marking and queries.

    The mark_attendance method implements the full validation chain:
    Student authenticated → Session exists → Session active →
    Server time valid → QR token valid → Token belongs to session →
    Token not expired → Not duplicate → Create → Commit
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.session_service = SessionService(db)
        self.qr_service = QRTokenService(db)

    async def mark_attendance(
        self, data: AttendanceMarkRequest, student_id: int
    ) -> AttendanceMarkResponse:
        """Mark attendance for a student.

        Full validation sequence per requirements.
        The database UNIQUE constraint is the final protection against
        concurrent duplicate requests.
        """
        # 1. Session exists
        session = await self.session_service.get_session_for_attendance(data.session_id)

        # 2. Session is active
        if session.status != SessionStatus.ACTIVE:
            if session.status == SessionStatus.COMPLETED:
                return AttendanceMarkResponse(
                    success=False,
                    message="Attendance session has ended",
                    session_id=data.session_id,
                )
            return AttendanceMarkResponse(
                success=False,
                message="Attendance session is not active",
                session_id=data.session_id,
            )

        from app.models.models import utcnow

        # 3. Current server time is within session window
        now = utcnow()
        if now < session.start_time:
            return AttendanceMarkResponse(
                success=False,
                message="Attendance session has not started yet",
                session_id=data.session_id,
            )
        if now > session.end_time:
            return AttendanceMarkResponse(
                success=False,
                message="Attendance session has ended",
                session_id=data.session_id,
            )

        # 4-6. QR token validation (exists, belongs to session, not expired)
        try:
            await self.qr_service.validate_token(data.session_id, data.token)
        except BadRequestException as e:
            return AttendanceMarkResponse(
                success=False,
                message=e.detail,
                session_id=data.session_id,
            )

        # 6.5 Validate student is in class roster
        # First, fetch student email
        student_result = await self.db.execute(select(User).where(User.id == student_id))
        student = student_result.scalar_one_or_none()
        if not student:
            return AttendanceMarkResponse(
                success=False,
                message="Student not found",
                session_id=data.session_id,
            )

        # Check roster
        roster_result = await self.db.execute(
            select(ClassRoster).where(
                ClassRoster.class_id == session.class_id,
                ClassRoster.student_email == student.email
            )
        )
        roster_entry = roster_result.scalar_one_or_none()
        if not roster_entry:
            return AttendanceMarkResponse(
                success=False,
                message="You are not enrolled in this class roster",
                session_id=data.session_id,
            )

        # 7. Check if student already attended (application-level check)
        existing = await self.attendance_repo.get_by_student_and_session(
            student_id, data.session_id
        )
        if existing:
            return AttendanceMarkResponse(
                success=False,
                message="Attendance already marked for this session",
                session_id=data.session_id,
            )

        # 8. Create attendance record
        attendance = Attendance(
            student_id=student_id,
            session_id=data.session_id,
            status=AttendanceStatus.PRESENT,
        )

        try:
            attendance = await self.attendance_repo.create(attendance)
        except IntegrityError:
            # Database-level UNIQUE constraint caught a race condition
            await self.db.rollback()
            return AttendanceMarkResponse(
                success=False,
                message="Attendance already marked for this session",
                session_id=data.session_id,
            )

        # Send email notification asynchronously
        import asyncio
        from app.services.email_service import get_email_service
        email_service = get_email_service()
        
        # We need class name for email
        class_name = session.class_.name if session.class_ else "Unknown Class"
        marked_time_str = attendance.marked_at.strftime("%I:%M %p")
        marked_date_str = attendance.marked_at.strftime("%Y-%m-%d")
        
        asyncio.create_task(
            email_service.send_attendance_confirmation(
                student_name=student.name,
                student_email=student.email,
                class_name=class_name,
                attendance_date=marked_date_str,
                attendance_time=marked_time_str,
            )
        )

        return AttendanceMarkResponse(
            success=True,
            message="Attendance marked successfully",
            session_id=data.session_id,
            marked_at=attendance.marked_at,
        )

    async def get_student_attendance(
        self,
        student_id: int,
        class_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """Get paginated attendance history for a student."""
        items, total = await self.attendance_repo.get_student_attendance(
            student_id=student_id,
            class_id=class_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )

        attendance_list = []
        for att in items:
            detail = AttendanceDetailResponse(
                id=att.id,
                student_id=att.student_id,
                session_id=att.session_id,
                marked_at=att.marked_at,
                status=att.status,
                class_name=att.session.class_.name if att.session and att.session.class_ else None,
                class_id=att.session.class_id if att.session else None,
            )
            attendance_list.append(detail)

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return PaginatedResponse(
            items=attendance_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_student_attendance_by_id(
        self, attendance_id: int, student_id: int
    ) -> AttendanceDetailResponse:
        """Get a specific attendance record for a student.

        Validates the record belongs to the requesting student.
        """
        attendance = await self.attendance_repo.get_by_id(attendance_id)
        if not attendance:
            raise NotFoundException(detail="Attendance record not found")
        if attendance.student_id != student_id:
            raise ForbiddenException(detail="Access denied")

        return AttendanceDetailResponse(
            id=attendance.id,
            student_id=attendance.student_id,
            session_id=attendance.session_id,
            marked_at=attendance.marked_at,
            status=attendance.status,
            class_name=attendance.session.class_.name if attendance.session and attendance.session.class_ else None,
            class_id=attendance.session.class_id if attendance.session else None,
        )

    async def get_student_today_attendance(
        self, student_id: int
    ) -> List[AttendanceDetailResponse]:
        """Get today's attendance records for a student."""
        from app.models.models import utcnow

        now = utcnow()
        today_start = datetime.combine(now.date(), time.min)
        today_end = datetime.combine(now.date(), time.max)

        items = await self.attendance_repo.get_today_attendance(
            student_id, today_start, today_end
        )

        return [
            AttendanceDetailResponse(
                id=att.id,
                student_id=att.student_id,
                session_id=att.session_id,
                marked_at=att.marked_at,
                status=att.status,
                class_name=att.session.class_.name if att.session and att.session.class_ else None,
                class_id=att.session.class_id if att.session else None,
            )
            for att in items
        ]

    async def get_session_attendance_for_teacher(
        self, session_id: int, teacher_id: int
    ) -> SessionAttendanceListResponse:
        """Get attendance list for a session (teacher dashboard).

        Validates the teacher owns the session's class.
        """
        session = await self.session_service._get_owned_session(session_id, teacher_id)

        attendances = await self.attendance_repo.get_session_attendance(session_id)

        student_list = [
            AttendanceStudentInfo(
                student_id=att.student_id,
                student_name=att.student.name if att.student else "Unknown",
                student_email=att.student.email if att.student else "Unknown",
                marked_at=att.marked_at,
                status=att.status,
            )
            for att in attendances
        ]

        class_name = session.class_.name if session.class_ else "Unknown"

        return SessionAttendanceListResponse(
            session_id=session_id,
            class_name=class_name,
            attendances=student_list,
            total_count=len(student_list),
        )

    async def get_session_attendance_count(
        self, session_id: int, teacher_id: int
    ) -> AttendanceCountResponse:
        """Get attendance count for a session (teacher dashboard).

        Returns total enrolled (present) and a placeholder absent count.
        """
        # Verify ownership
        await self.session_service._get_owned_session(session_id, teacher_id)

        present_count = await self.attendance_repo.get_session_attendance_count(session_id)

        return AttendanceCountResponse(
            session_id=session_id,
            total_students=present_count,  # total who interacted
            present_count=present_count,
            absent_count=0,  # Cannot determine without class enrollment roster
        )
