"""Authentication API routes.

Endpoints:
  POST /api/v1/auth/register — Register a new user
  POST /api/v1/auth/login    — Login and get JWT token
  GET  /api/v1/auth/me       — Get current user profile
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.core.limiter import limiter

settings = get_settings()

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user",
    description="Register as a new student. Account will be pending verification.",
    responses={
        201: {"description": "User successfully registered"},
        409: {"description": "Email already registered"},
    },
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    service = AuthService(db)
    return await service.register(data)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password. Returns a JWT token.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login and get JWT access token."""
    service = AuthService(db)
    return await service.login(data)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
    responses={
        200: {"description": "User profile"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user's profile."""
    return UserResponse.model_validate(current_user)
