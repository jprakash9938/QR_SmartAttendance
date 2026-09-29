"""Attendance session service — business logic for session management."""

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.models import AttendanceSession, SessionStatus
from app.repositories.session_repository import SessionRepository
from app.schemas.schemas import SessionCreateRequest, SessionDetailResponse, SessionResponse
from app.services.class_service import ClassService


class SessionService:
    """Service handling attendance session lifecycle."""

    def __init__(self, db: AsyncSession):
        self.session_repo = SessionRepository(db)
        self.class_service = ClassService(db)

    async def create_session(
        self, data: SessionCreateRequest, teacher_id: int
    ) -> SessionResponse:
        """Create a new attendance session.

        Validates teacher owns the class, calculates start/end times from
        the server clock (UTC), and sets initial status to ACTIVE.
        """
        # Verify teacher owns the class
        class_ = await self.class_service.verify_class_ownership(
            data.class_id, teacher_id
        )

        from app.models.models import utcnow

        now = utcnow()
        session = AttendanceSession(
            class_id=data.class_id,
            start_time=now,
            end_time=now + timedelta(minutes=data.duration_minutes),
            status=SessionStatus.ACTIVE,
        )
        session = await self.session_repo.create(session)
        return SessionResponse.model_validate(session)

    async def get_session(
        self, session_id: int, teacher_id: int
    ) -> SessionDetailResponse:
        """Get session details. Teacher must own the associated class."""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundException(detail="Session not found")

        # Verify ownership via class
        if session.class_ and session.class_.teacher_id != teacher_id:
            raise ForbiddenException(detail="You do not own this session")

        return SessionDetailResponse(
            id=session.id,
            class_id=session.class_id,
            start_time=session.start_time,
            end_time=session.end_time,
            status=session.status,
            created_at=session.created_at,
            class_name=session.class_.name if session.class_ else None,
        )

    async def get_teacher_sessions(self, teacher_id: int) -> List[SessionResponse]:
        """Get all sessions for a teacher's classes."""
        sessions = await self.session_repo.get_by_teacher(teacher_id)
        return [SessionResponse.model_validate(s) for s in sessions]

    async def start_session(
        self, session_id: int, teacher_id: int
    ) -> SessionResponse:
        """Start (activate) a session.

        Rules:
        - Cannot start an already active session.
        - Cannot restart a completed session.
        - Teacher must own the class.
        """
        session = await self._get_owned_session(session_id, teacher_id)

        if session.status == SessionStatus.ACTIVE:
            raise BadRequestException(detail="Session is already active")
        if session.status == SessionStatus.COMPLETED:
            raise BadRequestException(detail="Cannot restart a completed session")

        from app.models.models import utcnow

        # Re-calculate times for starting a cancelled/new session
        now = utcnow()
        original_duration = session.end_time - session.start_time
        session.start_time = now
        session.end_time = now + original_duration
        session.status = SessionStatus.ACTIVE

        session = await self.session_repo.update_status(session_id, SessionStatus.ACTIVE)
        return SessionResponse.model_validate(session)

    async def end_session(
        self, session_id: int, teacher_id: int
    ) -> SessionResponse:
        """End (complete) a session.

        Rules:
        - Only active sessions can be ended.
        - Teacher must own the class.
        """
        session = await self._get_owned_session(session_id, teacher_id)

        if session.status != SessionStatus.ACTIVE:
            raise BadRequestException(
                detail="Only active sessions can be ended"
            )

        session = await self.session_repo.update_status(
            session_id, SessionStatus.COMPLETED
        )
        return SessionResponse.model_validate(session)

    async def get_session_for_attendance(self, session_id: int) -> AttendanceSession:
        """Get raw session model for attendance marking (used by AttendanceService).

        Does NOT enforce teacher ownership since students need to look up sessions.
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundException(detail="Session not found")
        return session

    async def _get_owned_session(
        self, session_id: int, teacher_id: int
    ) -> AttendanceSession:
        """Internal: Get session and verify teacher ownership."""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundException(detail="Session not found")
        if session.class_ and session.class_.teacher_id != teacher_id:
            raise ForbiddenException(detail="You do not own this session")
        return session
