"""Authentication tests.

Covers:
- Registration (success, duplicate email, validation)
- Login (success, wrong password, non-existent email)
- JWT validation (valid, invalid, expired)
- Role authorization
"""

import pytest
from datetime import timedelta
from app.core.security import create_access_token


pytestmark = pytest.mark.asyncio


class TestRegistration:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_teacher_success(self, client):
        """Register a teacher successfully."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "John Teacher",
                "email": "john@teacher.com",
                "password": "securePassword123",
                "role": "TEACHER",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "john@teacher.com"
        assert data["user"]["role"] == "TEACHER"
        assert "password_hash" not in data["user"]
        assert "password" not in data["user"]

    async def test_register_student_success(self, client):
        """Register a student successfully."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Jane Student",
                "email": "jane@student.com",
                "password": "securePassword123",
                "role": "STUDENT",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["role"] == "STUDENT"

    async def test_register_duplicate_email(self, client):
        """Duplicate email registration should fail."""
        user_data = {
            "name": "User One",
            "email": "duplicate@test.com",
            "password": "securePassword123",
            "role": "STUDENT",
        }
        await client.post("/api/v1/auth/register", json=user_data)
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 409

    async def test_register_short_password(self, client):
        """Password under 8 characters should be rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "User",
                "email": "short@test.com",
                "password": "short",
                "role": "STUDENT",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client):
        """Invalid email format should be rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "User",
                "email": "not-an-email",
                "password": "securePassword123",
                "role": "STUDENT",
            },
        )
        assert response.status_code == 422

    async def test_register_empty_name(self, client):
        """Empty name should be rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "   ",
                "email": "emptyname@test.com",
                "password": "securePassword123",
                "role": "STUDENT",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, client, teacher_user):
        """Login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@test.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["user"]["email"] == "teacher@test.com"
        assert "password_hash" not in data["user"]

    async def test_login_wrong_password(self, client, teacher_user):
        """Login with wrong password should fail."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    async def test_login_nonexistent_email(self, client):
        """Login with non-existent email should fail with generic message."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.com", "password": "password123"},
        )
        assert response.status_code == 401
        # Should NOT reveal whether the email exists
        assert "Invalid email or password" in response.json()["detail"]


class TestJWT:
    """Tests for JWT token validation."""

    async def test_valid_token(self, client, teacher_headers):
        """Valid JWT should authenticate."""
        response = await client.get("/api/v1/auth/me", headers=teacher_headers)
        assert response.status_code == 200
        assert response.json()["email"] == "teacher@test.com"

    async def test_invalid_token(self, client):
        """Invalid JWT should be rejected."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert response.status_code == 401

    async def test_expired_token(self, client, teacher_user):
        """Expired JWT should be rejected."""
        token = create_access_token(
            data={"sub": str(teacher_user.id), "role": "TEACHER"},
            expires_delta=timedelta(seconds=-10),
        )
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_missing_token(self, client):
        """Missing Authorization header should fail."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 422  # Missing required header

    async def test_no_bearer_prefix(self, client):
        """Token without 'Bearer ' prefix should fail."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "just-a-token"},
        )
        assert response.status_code == 401


class TestRoleAuthorization:
    """Tests for role-based access control."""

    async def test_student_cannot_create_class(self, client, student_headers):
        """Students should be forbidden from creating classes."""
        response = await client.post(
            "/api/v1/classes",
            json={"name": "Test Class"},
            headers=student_headers,
        )
        assert response.status_code == 403

    async def test_teacher_can_create_class(self, client, teacher_headers):
        """Teachers should be able to create classes."""
        response = await client.post(
            "/api/v1/classes",
            json={"name": "Test Class"},
            headers=teacher_headers,
        )
        assert response.status_code == 201
