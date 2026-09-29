"""QR token generation tests.

Covers:
- Valid QR generation
- Expired session QR
- Wrong session token
- Unauthorized QR generation
- QR token structure
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.models import AttendanceSession, Class, SessionStatus, User, UserRole

pytestmark = pytest.mark.asyncio


class TestQRTokenGeneration:
    """Tests for GET /api/v1/sessions/{session_id}/qr."""

    async def test_generate_valid_qr(
        self, client, teacher_headers, active_session
    ):
        """Teacher can generate QR token for active session."""
        response = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == active_session.id
        assert data["token"]
        assert data["expires_at"]
        # Token should be non-empty and not contain sensitive data
        assert len(data["token"]) > 10

    async def test_qr_token_changes_on_regenerate(
        self, client, teacher_headers, active_session
    ):
        """Each QR request should generate a new token."""
        resp1 = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=teacher_headers,
        )
        resp2 = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=teacher_headers,
        )
        # Tokens should differ (cryptographically random)
        assert resp1.json()["token"] != resp2.json()["token"]

    async def test_qr_for_completed_session(
        self, client, teacher_headers, active_session
    ):
        """Cannot generate QR for a completed session."""
        # End the session first
        await client.post(
            f"/api/v1/sessions/{active_session.id}/end",
            headers=teacher_headers,
        )
        response = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=teacher_headers,
        )
        assert response.status_code == 400

    async def test_student_cannot_generate_qr(
        self, client, student_headers, active_session
    ):
        """Students cannot generate QR tokens."""
        response = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=student_headers,
        )
        assert response.status_code == 403

    async def test_qr_for_nonexistent_session(self, client, teacher_headers):
        """QR for non-existent session returns 404."""
        response = await client.get(
            "/api/v1/sessions/99999/qr",
            headers=teacher_headers,
        )
        assert response.status_code == 404

    async def test_qr_unauthorized_teacher(
        self, client, db_session, active_session
    ):
        """Another teacher cannot generate QR for someone else's session."""
        # Create another teacher
        other_teacher = User(
            name="Other Teacher",
            email="other_qr@teacher.com",
            password_hash=hash_password("password123"),
            role=UserRole.TEACHER,
        )
        db_session.add(other_teacher)
        await db_session.commit()
        await db_session.refresh(other_teacher)

        from app.core.security import create_access_token

        token = create_access_token(
            data={"sub": str(other_teacher.id), "role": "TEACHER"}
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/sessions/{active_session.id}/qr",
            headers=headers,
        )
        assert response.status_code == 403
