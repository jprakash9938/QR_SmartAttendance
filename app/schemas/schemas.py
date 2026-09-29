"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.models import AttendanceStatus, SessionStatus, UserRole


# ============================================================================
# Auth Schemas
# ============================================================================


class UserRegisterRequest(BaseModel):
    """Schema for user registration."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    role: UserRole = Field(..., description="User role: TEACHER or STUDENT")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum strength requirements.

        Following NIST SP 800-63B guidelines:
        - Minimum 8 characters (enforced by Field)
        - No maximum length restriction beyond 128 chars
        - Allow all character types
        """
        if len(v.strip()) < 8:
            raise ValueError("Password must be at least 8 characters (excluding leading/trailing whitespace)")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not just whitespace."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()


class UserLoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user data in responses. Never includes password_hash."""

    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""

    success: bool
    message: str


# ============================================================================
# Class Schemas
# ============================================================================


class ClassCreateRequest(BaseModel):
    """Schema for creating a class."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Class name"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Class name cannot be empty or whitespace only")
        return v.strip()


class ClassResponse(BaseModel):
    """Schema for class data in responses."""

    id: int
    name: str
    teacher_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassDetailResponse(ClassResponse):
    """Schema for class detail with teacher info."""

    teacher_name: str | None = None


# ============================================================================
# Session Schemas
# ============================================================================


class SessionCreateRequest(BaseModel):
    """Schema for creating an attendance session."""

    class_id: int = Field(..., gt=0, description="ID of the class")
    duration_minutes: int = Field(
        ..., gt=0, le=480, description="Session duration in minutes (max 8 hours)"
    )


class SessionResponse(BaseModel):
    """Schema for session data in responses."""

    id: int
    class_id: int
    start_time: datetime
    end_time: datetime
    status: SessionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetailResponse(SessionResponse):
    """Session response with class info."""

    class_name: str | None = None


# ============================================================================
# QR Token Schemas
# ============================================================================


class QRTokenResponse(BaseModel):
    """Schema for QR token response.

    Returns only the token and metadata — no student information,
    no session secrets. The frontend converts this to a QR image.
    """

    session_id: int
    token: str
    expires_at: datetime


# ============================================================================
# Attendance Schemas
# ============================================================================


class AttendanceMarkRequest(BaseModel):
    """Schema for marking attendance."""

    session_id: int = Field(..., gt=0, description="Session ID")
    token: str = Field(
        ..., min_length=1, max_length=256, description="QR token from scan"
    )


class AttendanceMarkResponse(BaseModel):
    """Schema for attendance mark result."""

    success: bool
    message: str
    session_id: int | None = None
    marked_at: datetime | None = None


class AttendanceResponse(BaseModel):
    """Schema for attendance record."""

    id: int
    student_id: int
    session_id: int
    marked_at: datetime
    status: AttendanceStatus

    model_config = {"from_attributes": True}


class AttendanceDetailResponse(AttendanceResponse):
    """Attendance response with related entity names."""

    class_name: str | None = None
    class_id: int | None = None


class AttendanceStudentInfo(BaseModel):
    """Student attendance info for teacher dashboard."""

    student_id: int
    student_name: str
    student_email: str
    marked_at: datetime
    status: AttendanceStatus


class AttendanceCountResponse(BaseModel):
    """Attendance count summary for a session."""

    session_id: int
    total_students: int
    present_count: int
    absent_count: int


class SessionAttendanceListResponse(BaseModel):
    """Full session attendance list for teacher."""

    session_id: int
    class_name: str
    attendances: List[AttendanceStudentInfo]
    total_count: int


# ============================================================================
# Pagination
# ============================================================================


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
