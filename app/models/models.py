"""SQLAlchemy ORM models for the attendance system."""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class SessionStatus(str, enum.Enum):
    """Attendance session status enumeration."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AttendanceStatus(str, enum.Enum):
    """Attendance record status enumeration."""

    PRESENT = "PRESENT"


def utcnow() -> datetime:
    """Return current UTC time as timezone-naive."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """User model representing teachers and students."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    classes = relationship("Class", back_populates="teacher", lazy="selectin")
    attendances = relationship("Attendance", back_populates="student", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Class(Base):
    """Class model representing a course/class taught by a teacher."""

    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    teacher_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    teacher = relationship("User", back_populates="classes", lazy="selectin")
    sessions = relationship(
        "AttendanceSession", back_populates="class_", lazy="selectin"
    )
    roster = relationship(
        "ClassRoster", back_populates="class_", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Class(id={self.id}, name='{self.name}')>"


class AttendanceSession(Base):
    """Attendance session model for tracking session windows."""

    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(
        Integer,
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        Enum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False
    )
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    class_ = relationship("Class", back_populates="sessions", lazy="selectin")
    qr_tokens = relationship("QRToken", back_populates="session", lazy="selectin")
    attendances = relationship(
        "Attendance", back_populates="session", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<AttendanceSession(id={self.id}, status='{self.status}')>"


class QRToken(Base):
    """QR token model for dynamic QR code tokens.

    Stores a SHA-256 hash of the token (not the raw token) so that
    a database compromise does not reveal valid tokens.
    Only the latest token per session is kept to avoid unbounded growth.
    """

    __tablename__ = "qr_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    session = relationship("AttendanceSession", back_populates="qr_tokens")

    def __repr__(self) -> str:
        return f"<QRToken(id={self.id}, session_id={self.session_id})>"


class Attendance(Base):
    """Attendance record model.

    The UNIQUE constraint on (student_id, session_id) is the final database-level
    protection against duplicate attendance, even under concurrent requests.
    """

    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id = Column(
        Integer,
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    marked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    status = Column(
        Enum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False
    )

    # Database-level unique constraint: one student per session
    __table_args__ = (
        UniqueConstraint("student_id", "session_id", name="uq_student_session"),
        Index("ix_attendance_student_session", "student_id", "session_id"),
    )

    # Relationships
    student = relationship("User", back_populates="attendances", lazy="selectin")
    session = relationship(
        "AttendanceSession", back_populates="attendances", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Attendance(id={self.id}, student_id={self.student_id}, session_id={self.session_id})>"


class ClassRoster(Base):
    """Roster of students enrolled in a class."""

    __tablename__ = "class_roster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_name = Column(String(255), nullable=False)
    student_email = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("class_id", "student_email", name="uq_class_student_email"),
    )

    # Relationships
    class_ = relationship("Class", back_populates="roster")

    def __repr__(self) -> str:
        return f"<ClassRoster(id={self.id}, class_id={self.class_id}, student_email='{self.student_email}')>"
