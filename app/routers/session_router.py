"""Attendance session API routes.

Endpoints:
  POST /api/v1/sessions                     — Create session (teacher)
  GET  /api/v1/sessions/{session_id}        — Get session details (teacher)
  GET  /api/v1/teacher/sessions             — List teacher's sessions
  POST /api/v1/sessions/{session_id}/start  — Start session (teacher)
  POST /api/v1/sessions/{session_id}/end    — End session (teacher)
  GET  /api/v1/sessions/{session_id}/qr     — Get dynamic QR token (teacher)
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_teacher
from app.models.models import User
from app.schemas.schemas import (
    QRTokenResponse,
    SessionCreateRequest,
    SessionDetailResponse,
    SessionResponse,
)
from app.services.qr_service import QRTokenService
from app.services.session_service import SessionService

router = APIRouter(tags=["Sessions"])


@router.post(
    "/api/v1/sessions",
    response_model=SessionResponse,
    status_code=201,
    summary="Create attendance session",
    description=(
        "Create a new attendance session for a class. "
        "The teacher must own the class. Duration is specified in minutes."
    ),
    responses={
        201: {"description": "Session created"},
        403: {"description": "Not the class owner / Teacher access required"},
        404: {"description": "Class not found"},
    },
)
async def create_session(
    data: SessionCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Create a new attendance session (teacher only)."""
    service = SessionService(db)
    return await service.create_session(data, teacher.id)


@router.get(
    "/api/v1/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session details",
    description="Get detailed information about a session. Teacher must own it.",
    responses={
        200: {"description": "Session details"},
        403: {"description": "Not the session owner"},
        404: {"description": "Session not found"},
    },
)
async def get_session(
    session_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Get session details (teacher only)."""
    service = SessionService(db)
    return await service.get_session(session_id, teacher.id)


@router.get(
    "/api/v1/teacher/sessions",
    response_model=List[SessionResponse],
    summary="List teacher's sessions",
    description="Get all attendance sessions for the authenticated teacher's classes.",
    responses={
        200: {"description": "List of sessions"},
        403: {"description": "Teacher access required"},
    },
)
async def list_teacher_sessions(
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """List all sessions for teacher's classes."""
    service = SessionService(db)
    return await service.get_teacher_sessions(teacher.id)


@router.post(
    "/api/v1/sessions/{session_id}/start",
    response_model=SessionResponse,
    summary="Start session",
    description="Start (activate) an attendance session. Cannot start already active or completed sessions.",
    responses={
        200: {"description": "Session started"},
        400: {"description": "Session already active or completed"},
        403: {"description": "Not the session owner"},
        404: {"description": "Session not found"},
    },
)
async def start_session(
    session_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Start an attendance session (teacher only)."""
    service = SessionService(db)
    return await service.start_session(session_id, teacher.id)


@router.post(
    "/api/v1/sessions/{session_id}/end",
    response_model=SessionResponse,
    summary="End session",
    description="End (complete) an active attendance session.",
    responses={
        200: {"description": "Session ended"},
        400: {"description": "Session not active"},
        403: {"description": "Not the session owner"},
        404: {"description": "Session not found"},
    },
)
async def end_session(
    session_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """End an attendance session (teacher only)."""
    service = SessionService(db)
    return await service.end_session(session_id, teacher.id)


@router.get(
    "/api/v1/sessions/{session_id}/qr",
    response_model=QRTokenResponse,
    summary="Get dynamic QR token",
    description=(
        "Generate a dynamic QR token for an active session. "
        "Token expires after 5 seconds. Only the session owner can request this. "
        "The frontend converts the returned token into a QR image."
    ),
    responses={
        200: {"description": "QR token generated", "content": {
            "application/json": {
                "example": {
                    "session_id": 1,
                    "token": "aB3dEf_GhI-jKlMnOpQrStUvWxYz0123456789AB",
                    "expires_at": "2026-08-09T10:00:05Z"
                }
            }
        }},
        400: {"description": "Session not active or has ended"},
        403: {"description": "Not the session owner"},
        404: {"description": "Session not found"},
    },
)
async def get_qr_token(
    session_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Generate a dynamic QR token (teacher only, 5-second validity)."""
    service = QRTokenService(db)
    return await service.generate_token(session_id, teacher.id)
