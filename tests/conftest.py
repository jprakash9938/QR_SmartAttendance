import os
os.environ["DISABLE_RATE_LIMITS"] = "true"

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.limiter import limiter
from app.core.security import create_access_token, hash_password
from app.main import app

limiter.enabled = False
from app.models.models import (
    Attendance,
    AttendanceSession,
    AttendanceStatus,
    Class,
    ClassRoster,
    QRToken,
    SessionStatus,
    User,
    UserRole,
    utcnow,
)

# In-memory SQLite for test isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)



@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create fresh tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide a test database session."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Provide a test HTTP client with the test database injected."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Disable rate limits during testing
    limiter.enabled = False
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# Helper fixtures for creating test data
# ============================================================================


@pytest_asyncio.fixture
async def teacher_user(db_session: AsyncSession) -> User:
    """Create a teacher user."""
    user = User(
        name="Test Teacher",
        email="teacher@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.TEACHER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession) -> User:
    """Create a student user."""
    user = User(
        name="Test Student",
        email="student@test.com",
        password_hash=hash_password("password123"),
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def teacher_token(teacher_user: User) -> str:
    """Generate a JWT token for the teacher."""
    return create_access_token(
        data={"sub": str(teacher_user.id), "role": teacher_user.role.value}
    )


@pytest_asyncio.fixture
async def student_token(student_user: User) -> str:
    """Generate a JWT token for the student."""
    return create_access_token(
        data={"sub": str(student_user.id), "role": student_user.role.value}
    )


@pytest_asyncio.fixture
async def teacher_headers(teacher_token: str) -> dict:
    """Auth headers for teacher."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest_asyncio.fixture
async def student_headers(student_token: str) -> dict:
    """Auth headers for student."""
    return {"Authorization": f"Bearer {student_token}"}


@pytest_asyncio.fixture
async def test_class(db_session: AsyncSession, teacher_user: User) -> Class:
    """Create a test class with default student enrolled."""
    class_ = Class(name="Test Class", teacher_id=teacher_user.id)
    db_session.add(class_)
    await db_session.commit()
    await db_session.refresh(class_)

    roster = ClassRoster(
        class_id=class_.id,
        student_name="Test Student",
        student_email="student@test.com",
    )
    db_session.add(roster)
    await db_session.commit()

    return class_


@pytest_asyncio.fixture
async def active_session(
    db_session: AsyncSession, test_class: Class
) -> AttendanceSession:
    """Create an active attendance session."""
    now = utcnow()
    session = AttendanceSession(
        class_id=test_class.id,
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=SessionStatus.ACTIVE,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session
