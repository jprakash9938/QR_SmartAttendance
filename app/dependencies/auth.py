"""FastAPI dependencies for authentication and authorization.

Provides reusable dependency functions for route-level security:
- get_current_user: Extracts and validates JWT from Authorization header
- require_teacher: Ensures the authenticated user has TEACHER role
- require_student: Ensures the authenticated user has STUDENT role
"""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.models.models import User, UserRole
from app.repositories.user_repository import UserRepository


async def get_current_user(
    authorization: str = Header(..., description="Bearer JWT token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT token from Authorization header.

    Returns the authenticated User model.
    Raises UnauthorizedException if token is missing, invalid, or expired.
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException(detail="Invalid authorization header format")

    token = authorization[7:]  # Strip "Bearer " prefix
    if not token:
        raise UnauthorizedException(detail="Token not provided")

    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException(detail="Invalid or expired token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(detail="Invalid token payload")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise UnauthorizedException(detail="Invalid token payload")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(detail="User not found")

    return user


async def require_teacher(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user has TEACHER role.

    Raises ForbiddenException if the user is not a teacher.
    """
    if current_user.role != UserRole.TEACHER:
        raise ForbiddenException(detail="Teacher access required")
    return current_user


async def require_student(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user has STUDENT role.

    Raises ForbiddenException if the user is not a student.
    """
    if current_user.role != UserRole.STUDENT:
        raise ForbiddenException(detail="Student access required")
    return current_user

async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user has ADMIN role.

    Raises ForbiddenException if the user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException(detail="Admin access required")
    return current_user
