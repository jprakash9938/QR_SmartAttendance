"""Teacher attendance dashboard API routes.

Endpoints:
  GET /api/v1/teacher/sessions/{session_id}/attendance       — Attendance list
  GET /api/v1/teacher/sessions/{session_id}/attendance/count  — Attendance count
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_teacher
from app.models.models import User
from app.schemas.schemas import AttendanceCountResponse, SessionAttendanceListResponse
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/api/v1/teacher/sessions", tags=["Teacher Dashboard"])


@router.get(
    "/{session_id}/attendance",
    response_model=SessionAttendanceListResponse,
    summary="Session attendance list",
    description=(
        "Get the full attendance list for a session, including student names, "
        "emails, and timestamps. Only the teacher who owns the session can access this."
    ),
    responses={
        200: {"description": "Attendance list with student details"},
        403: {"description": "Not the session owner / Teacher access required"},
        404: {"description": "Session not found"},
    },
)
async def get_session_attendance(
    session_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance list for a session (teacher only)."""
    service = AttendanceService(db)
    return await service.get_session_attendance_for_teacher(session_id, teacher.id)


@router.get(
    "/{session_id}/attendance/count",
    response_model=AttendanceCountResponse,
    summary="Attendance count",
    description="Get attendance count summary for a session.",
    responses={
        200: {"description": "Attendance count summary"},
        403: {"description": "Not the session owner / Teacher access required"},
        404: {"description": "Session not found"},
    },
)
async def get_session_attendance_count(
    session_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance count for a session (teacher only)."""
    service = AttendanceService(db)
    return await service.get_session_attendance_count(session_id, teacher.id)


@router.get(
    "/{session_id}/export",
    summary="Export attendance to CSV",
    description="Download the attendance list for a session as a CSV file.",
    responses={
        200: {"description": "CSV file"},
        403: {"description": "Not the session owner"},
        404: {"description": "Session not found"},
    },
)
async def export_session_attendance(
    session_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Export attendance list as CSV."""
    from fastapi import Response
    import csv
    import io

    service = AttendanceService(db)
    attendance_data = await service.get_session_attendance_for_teacher(session_id, teacher.id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Student Email", "Marked At", "Status"])
    
    for record in attendance_data.attendance:
        writer.writerow([
            record.student.name,
            record.student.email,
            record.marked_at.isoformat() if record.marked_at else "",
            record.status.value if record.status else "PRESENT"
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=attendance_session_{session_id}.csv"
        }
    )
