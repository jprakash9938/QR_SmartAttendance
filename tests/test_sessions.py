"""Session management tests.

Covers:
- Teacher creates session
- Student cannot create session
- Teacher cannot access another teacher's session
- Session lifecycle (start, end)
- Invalid duration
- Session state machine rules
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.core.security import create_access_token, hash_password
from app.models.models import AttendanceSession, Class, SessionStatus, User, UserRole, utcnow

pytestmark = pytest.mark.asyncio


class TestSessionCreation:
    """Tests for POST /api/v1/sessions."""

    async def test_teacher_creates_session(
        self, client, teacher_headers, test_class
    ):
        """Teacher can create a session for their class."""
        response = await client.post(
            "/api/v1/sessions",
            json={"class_id": test_class.id, "duration_minutes": 60},
            headers=teacher_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["class_id"] == test_class.id
        assert data["status"] == "ACTIVE"

    async def test_student_cannot_create_session(
        self, client, student_headers, test_class
    ):
        """Students must not be able to create sessions."""
        response = await client.post(
            "/api/v1/sessions",
            json={"class_id": test_class.id, "duration_minutes": 60},
            headers=student_headers,
        )
        assert response.status_code == 403

    async def test_invalid_duration(self, client, teacher_headers, test_class):
        """Duration must be positive and within limits."""
        # Zero duration
        response = await client.post(
            "/api/v1/sessions",
            json={"class_id": test_class.id, "duration_minutes": 0},
            headers=teacher_headers,
        )
        assert response.status_code == 422

        # Negative duration
        response = await client.post(
            "/api/v1/sessions",
            json={"class_id": test_class.id, "duration_minutes": -10},
            headers=teacher_headers,
        )
        assert response.status_code == 422

    async def test_teacher_cannot_access_other_teachers_session(
        self, client, db_session, teacher_headers, test_class
    ):
        """A teacher cannot access a session belonging to another teacher's class."""
        # Create another teacher
        other_teacher = User(
            name="Other Teacher",
            email="other@teacher.com",
            password_hash=hash_password("password123"),
            role=UserRole.TEACHER,
        )
        db_session.add(other_teacher)
        await db_session.commit()
        await db_session.refresh(other_teacher)

        # Create class for other teacher
        other_class = Class(name="Other Class", teacher_id=other_teacher.id)
        db_session.add(other_class)
        await db_session.commit()
        await db_session.refresh(other_class)

        # Create session for other teacher's class
        now = utcnow()
        other_session = AttendanceSession(
            class_id=other_class.id,
            start_time=now,
            end_time=now + timedelta(hours=1),
            status=SessionStatus.ACTIVE,
        )
        db_session.add(other_session)
        await db_session.commit()
        await db_session.refresh(other_session)

        # Try to access the other teacher's session
        response = await client.get(
            f"/api/v1/sessions/{other_session.id}",
            headers=teacher_headers,
        )
        assert response.status_code == 403


class TestSessionLifecycle:
    """Tests for session start/end operations."""

    async def test_end_active_session(
        self, client, teacher_headers, active_session
    ):
        """Teacher can end an active session."""
        response = await client.post(
            f"/api/v1/sessions/{active_session.id}/end",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"

    async def test_cannot_start_active_session(
        self, client, teacher_headers, active_session
    ):
        """Cannot start an already active session."""
        response = await client.post(
            f"/api/v1/sessions/{active_session.id}/start",
            headers=teacher_headers,
        )
        assert response.status_code == 400

    async def test_cannot_restart_completed_session(
        self, client, teacher_headers, active_session
    ):
        """Cannot restart a completed session."""
        # End it first
        await client.post(
            f"/api/v1/sessions/{active_session.id}/end",
            headers=teacher_headers,
        )
        # Try to start again
        response = await client.post(
            f"/api/v1/sessions/{active_session.id}/start",
            headers=teacher_headers,
        )
        assert response.status_code == 400

    async def test_cannot_end_completed_session(
        self, client, teacher_headers, active_session
    ):
        """Cannot end an already completed session."""
        await client.post(
            f"/api/v1/sessions/{active_session.id}/end",
            headers=teacher_headers,
        )
        response = await client.post(
            f"/api/v1/sessions/{active_session.id}/end",
            headers=teacher_headers,
        )
        assert response.status_code == 400

    async def test_list_teacher_sessions(
        self, client, teacher_headers, active_session
    ):
        """Teacher can list their sessions."""
        response = await client.get(
            "/api/v1/teacher/sessions",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_session_not_found(self, client, teacher_headers):
        """Non-existent session returns 404."""
        response = await client.get(
            "/api/v1/sessions/99999",
            headers=teacher_headers,
        )
        assert response.status_code == 404
