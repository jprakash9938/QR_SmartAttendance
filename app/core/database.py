"""Async database engine and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


async def get_db() -> AsyncSession:
    """Dependency that yields an async database session.

    The session is automatically closed after the request completes.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def seed_initial_admin() -> None:
    """Ensure the configured admin user from .env exists and has valid credentials."""
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        return

    from sqlalchemy import select
    from app.models.models import User, UserRole
    from app.core.security import hash_password, verify_password

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                name=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_verified=True,
            )
            session.add(admin)
            await session.commit()
        else:
            if not verify_password(settings.ADMIN_PASSWORD, admin.password_hash):
                admin.password_hash = hash_password(settings.ADMIN_PASSWORD)
                admin.name = settings.ADMIN_NAME
                await session.commit()


async def init_db() -> None:
    """Create all tables and seed initial admin user."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_initial_admin()

