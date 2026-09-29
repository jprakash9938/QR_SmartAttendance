"""Admin API routes.

Endpoints:
  GET  /api/v1/admin/users       — List all users
  POST /api/v1/admin/users       — Admin creates a user
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.models import User
from app.schemas.schemas import UserRegisterRequest, UserResponse, UserLoginRequest, TokenResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Admin login",
    description="Authenticate an admin user and return a JWT token.",
)
async def admin_login(data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Admin login endpoint."""
    service = AuthService(db)
    return await service.admin_login(data)


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users",
    description="Admin only. List all registered teachers, students, and admins.",
)
async def list_users(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all users."""
    user_repo = UserRepository(db)
    users = await user_repo.get_all()
    return [UserResponse.model_validate(u) for u in users]


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user",
    description="Admin only. Create a new user (Teacher or Student) directly without logging them in.",
)
async def create_user(
    data: UserRegisterRequest,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a new user."""
    service = AuthService(db)
    return await service.admin_create_user(data)

@router.patch(
    "/users/{user_id}/verify",
    response_model=UserResponse,
    summary="Verify a user",
    description="Admin only. Mark a pending student as verified.",
)
async def verify_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin verifies a user."""
    service = AuthService(db)
    return await service.verify_user(user_id)
