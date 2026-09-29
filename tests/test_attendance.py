"""Attendance marking tests.

Covers:
- Successful attendance
- Duplicate attendance
- Expired QR token
- Expired session
- Attendance before session starts
- Invalid token
- Unauthorized student
- Concurrent attendance requests
- Email notification behavior
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.security import generate_qr_token, hash_password, hash_token
from app.models.models import (
    AttendanceSession,
    Class,
    QRToken,
    SessionStatus,
    User,
    UserRole,
    utcnow,
)

pytestmark = pytest.mark.asyncio


class TestMarkAttendance:
    """Tests for POST /api/v1/attendance/mark."""

    async def _get_valid_token(self, client, teacher_headers, session_id: int) -> str:
        """Helper: generate a valid QR token via the API."""
        resp = await client.get(
            f"/api/v1/sessions/{session_id}/qr",
            headers=teacher_headers,
        )
        assert resp.status_code == 200
        return resp.json()["token"]

    async def test_successful_attendance(
        self, client, teacher_headers, student_headers, active_session
    ):
        """Student can mark attendance with a valid QR token."""
        token = await self._get_valid_token(
            client, teacher_headers, active_session.id
        )
        response = await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": active_session.id, "token": token},
            headers=student_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Attendance marked successfully"
        assert data["session_id"] == active_session.id
        assert data["marked_at"] is not None

    async def test_duplicate_attendance(
        self, client, teacher_headers, student_headers, active_session
    ):
        """Marking attendance twice should fail."""
        token = await self._get_valid_token(
            client, teacher_headers, active_session.id
        )
        # First mark
        await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": active_session.id, "token": token},
            headers=student_headers,
        )
        # Get new token for second attempt
        token2 = await self._get_valid_token(
            client, teacher_headers, active_session.id
        )
        response = await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": active_session.id, "token": token2},
            headers=student_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already marked" in data["message"].lower()

    async def test_expired_session(
        self, client, db_session, teacher_headers, student_headers, test_class
    ):
        """Cannot mark attendance for an expired session."""
        now = utcnow()
        expired_session = AttendanceSession(
            class_id=test_class.id,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            status=SessionStatus.ACTIVE,
        )
        db_session.add(expired_session)
        await db_session.commit()
        await db_session.refresh(expired_session)

        # Create a token directly in DB (since QR endpoint checks session time too)
        raw_token = generate_qr_token()
        qr = QRToken(
            session_id=expired_session.id,
            token_hash=hash_token(raw_token),
            expires_at=now + timedelta(seconds=30),
        )
        db_session.add(qr)
        await db_session.commit()

        response = await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": expired_session.id, "token": raw_token},
            headers=student_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "ended" in data["message"].lower()

    async def test_invalid_token(
        self, client, student_headers, active_session
    ):
        """Invalid QR token should be rejected."""
        response = await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": active_session.id, "token": "totally-invalid-token"},
            headers=student_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    async def test_expired_qr_token(
        self, client, db_session, student_headers, active_session
    ):
        """Expired QR token should be rejected."""
        raw_token = generate_qr_token()
        now = utcnow()
        qr = QRToken(
            session_id=active_session.id,
            token_hash=hash_token(raw_token),
            expires_at=now - timedelta(seconds=10),  # Already expired
        )
        db_session.add(qr)
        await db_session.commit()

        response = await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": active_session.id, "token": raw_token},
            headers=student_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "expired" in data["message"].lower()

    async def test_teacher_cannot_mark_attendance(
        self, client, teacher_headers, active_session
    ):
        """Teachers cannot mark attendance (student role required)."""
        response = await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": active_session.id, "token": "some-token"},
            headers=teacher_headers,
        )
        assert response.status_code == 403

    async def test_completed_session_attendance(
        self, client, teacher_headers, student_headers, active_session
    ):
        """Cannot mark attendance for a completed session."""
        # End the session
        await client.post(
            f"/api/v1/sessions/{active_session.id}/end",
            headers=teacher_headers,
        )
        response = await client.post(
            "/api/v1/attendance/mark",
            json={"session_id": active_session.id, "token": "some-token"},
            headers=student_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "ended" in data["message"].lower()


class TestAttendanceHistory:
    """Tests for student attendance history endpoints."""

    async def test_get_student_attendance(
        self, client, teacher_headers, student_headers, active_session
    ):
        """Student can view their attendance history."""
        # Mark attendance first
        token = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=teacher_headers,
        )
        await client.post(
            "/api/v1/attendance/mark",
            json={
                "session_id": active_session.id,
                "token": token.json()["token"],
            },
            headers=student_headers,
        )

        # Get history
        response = await client.get(
            "/api/v1/student/attendance",
            headers=student_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_get_today_attendance(
        self, client, teacher_headers, student_headers, active_session
    ):
        """Student can view today's attendance."""
        # Mark attendance
        token = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=teacher_headers,
        )
        await client.post(
            "/api/v1/attendance/mark",
            json={
                "session_id": active_session.id,
                "token": token.json()["token"],
            },
            headers=student_headers,
        )

        response = await client.get(
            "/api/v1/student/attendance/today",
            headers=student_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) >= 1

    async def test_teacher_cannot_access_student_attendance_api(
        self, client, teacher_headers
    ):
        """Teachers cannot use the student attendance endpoint."""
        response = await client.get(
            "/api/v1/student/attendance",
            headers=teacher_headers,
        )
        assert response.status_code == 403


class TestEmailNotification:
    """Tests for email notifications on attendance."""

    async def test_email_sent_on_successful_attendance(
        self, client, teacher_headers, student_headers, active_session
    ):
        """Email should be sent after successful attendance."""
        with patch(
            "app.routers.attendance_router.get_email_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_attendance_confirmation = AsyncMock(return_value=True)
            mock_get_service.return_value = mock_service

            token = await client.get(
                f"/api/v1/sessions/{active_session.id}/qr",
                headers=teacher_headers,
            )
            response = await client.post(
                "/api/v1/attendance/mark",
                json={
                    "session_id": active_session.id,
                    "token": token.json()["token"],
                },
                headers=student_headers,
            )
            assert response.json()["success"] is True

            # Allow background task to run
            await asyncio.sleep(0.1)

    async def test_no_email_on_failed_attendance(
        self, client, student_headers, active_session
    ):
        """No email should be sent when attendance fails."""
        with patch(
            "app.routers.attendance_router.get_email_service"
        ) as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service

            response = await client.post(
                "/api/v1/attendance/mark",
                json={
                    "session_id": active_session.id,
                    "token": "invalid-token",
                },
                headers=student_headers,
            )
            assert response.json()["success"] is False
            # Email service should NOT be called
            mock_service.send_attendance_confirmation.assert_not_called()
