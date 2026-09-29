"""Student attendance API routes.

Endpoints:
  POST /api/v1/attendance/mark                  — Mark attendance (student)
  GET  /api/v1/student/attendance               — Student attendance history
  GET  /api/v1/student/attendance/today          — Today's attendance
  GET  /api/v1/student/attendance/{attendance_id} — Specific attendance record
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_db
from app.dependencies.auth import require_student
from app.models.models import User
from app.schemas.schemas import (
    AttendanceDetailResponse,
    AttendanceMarkRequest,
    AttendanceMarkResponse,
    PaginatedResponse,
)
from app.services.attendance_service import AttendanceService
from app.services.email_service import get_email_service
from app.core.limiter import limiter

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Student Attendance"])


async def _send_attendance_email_background(
    student_name: str,
    student_email: str,
    class_name: str,
    marked_at: datetime,
) -> None:
    """Send attendance confirmation email in the background.

    This runs as an asyncio task so it doesn't block the response.
    Failures are logged but don't affect the attendance response.
    """
    try:
        email_service = get_email_service()
        await email_service.send_attendance_confirmation(
            student_name=student_name,
            student_email=student_email,
            class_name=class_name,
            attendance_date=marked_at.strftime("%Y-%m-%d"),
            attendance_time=marked_at.strftime("%H:%M:%S UTC"),
        )
    except Exception:
        logger.exception("Background email task failed for %s", student_email)


@router.post(
    "/api/v1/attendance/mark",
    response_model=AttendanceMarkResponse,
    summary="Mark attendance",
    description=(
        "Mark attendance by providing a session ID and QR token. "
        "The token must be valid (not expired, belongs to the session). "
        "Duplicate attendance is rejected."
    ),
    responses={
        200: {
            "description": "Attendance result",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Attendance marked",
                            "value": {
                                "success": True,
                                "message": "Attendance marked successfully",
                                "session_id": 1,
                                "marked_at": "2026-08-09T10:00:03Z",
                            },
                        },
                        "duplicate": {
                            "summary": "Already marked",
                            "value": {
                                "success": False,
                                "message": "Attendance already marked for this session",
                            },
                        },
                        "expired_qr": {
                            "summary": "QR expired",
                            "value": {
                                "success": False,
                                "message": "QR code has expired",
                            },
                        },
                        "session_ended": {
                            "summary": "Session ended",
                            "value": {
                                "success": False,
                                "message": "Attendance session has ended",
                            },
                        },
                    }
                }
            },
        },
        403: {"description": "Student access required"},
    },
)
@limiter.limit(settings.RATE_LIMIT_ATTENDANCE)
async def mark_attendance(
    request: Request,
    data: AttendanceMarkRequest,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Mark attendance with QR token (student only)."""
    service = AttendanceService(db)
    result = await service.mark_attendance(data, student.id)

    # Send email ONLY on successful attendance, asynchronously
    if result.success and result.marked_at:
        # Get class name for the email
        session_service = service.session_service
        session = await session_service.get_session_for_attendance(data.session_id)
        class_name = session.class_.name if session.class_ else "Unknown Class"

        # Fire-and-forget background email
        asyncio.create_task(
            _send_attendance_email_background(
                student_name=student.name,
                student_email=student.email,
                class_name=class_name,
                marked_at=result.marked_at,
            )
        )

    return result


@router.get(
    "/api/v1/student/attendance",
    response_model=PaginatedResponse,
    summary="Student attendance history",
    description="Get paginated attendance history for the authenticated student. Supports filtering by class and date range.",
    responses={
        200: {"description": "Paginated attendance list"},
        403: {"description": "Student access required"},
    },
)
async def get_student_attendance(
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get attendance history for the authenticated student."""
    service = AttendanceService(db)
    return await service.get_student_attendance(
        student_id=student.id,
        class_id=class_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/api/v1/student/attendance/today",
    response_model=List[AttendanceDetailResponse],
    summary="Today's attendance",
    description="Get today's attendance records for the authenticated student.",
    responses={
        200: {"description": "Today's attendance list"},
        403: {"description": "Student access required"},
    },
)
async def get_today_attendance(
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get today's attendance for the authenticated student."""
    service = AttendanceService(db)
    return await service.get_student_today_attendance(student.id)


@router.get(
    "/api/v1/student/attendance/{attendance_id}",
    response_model=AttendanceDetailResponse,
    summary="Get attendance record",
    description="Get a specific attendance record. Student can only access their own records.",
    responses={
        200: {"description": "Attendance details"},
        403: {"description": "Access denied / Student access required"},
        404: {"description": "Attendance record not found"},
    },
)
async def get_attendance_record(
    attendance_id: int,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific attendance record (student only, own records)."""
    service = AttendanceService(db)
    return await service.get_student_attendance_by_id(attendance_id, student.id)
