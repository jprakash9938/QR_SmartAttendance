"""Authentication service — business logic for registration and login."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, UnauthorizedException, ForbiddenException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    """Service handling user registration and authentication."""

    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def register(self, data: UserRegisterRequest) -> TokenResponse:
        """Register a new user.

        Validates unique email, hashes password, creates user,
        and returns a JWT token.
        """
        # Check for duplicate email
        if await self.user_repo.email_exists(data.email):
            raise ConflictException(detail="Email already registered")

        if data.role != UserRole.STUDENT:
            raise ForbiddenException(detail="Only students can self-register")

        # Create user with hashed password — never store plaintext
        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            is_verified=False,
        )
        user = await self.user_repo.create(user)

        # Generate JWT token
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

    async def admin_create_user(self, data: UserRegisterRequest) -> UserResponse:
        """Admin creating a new user without generating a token."""
        if await self.user_repo.email_exists(data.email):
            raise ConflictException(detail="Email already registered")

        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=data.role,
            is_verified=True,
        )
        user = await self.user_repo.create(user)
        return UserResponse.model_validate(user)

    async def verify_user(self, user_id: int) -> UserResponse:
        """Mark a user as verified."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise BadRequestException(detail="User not found")
        
        user.is_verified = True
        await self.user_repo.db.commit()
        await self.user_repo.db.refresh(user)
        return UserResponse.model_validate(user)

    async def login(self, data: UserLoginRequest) -> TokenResponse:
        """Authenticate user and return JWT token.

        Uses constant-time password comparison via bcrypt.verify
        to prevent timing attacks. Generic error messages prevent
        user enumeration.
        """
        user = await self.user_repo.get_by_email(data.email)

        # Generic error message to prevent user enumeration
        if not user:
            raise UnauthorizedException(detail="Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise UnauthorizedException(detail="Invalid email or password")

        if user.role == UserRole.ADMIN:
            raise ForbiddenException(detail="Admins must use the admin login portal")

        if not user.is_verified:
            raise ForbiddenException(detail="Account pending verification by an administrator")

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

    async def admin_login(self, data: UserLoginRequest) -> TokenResponse:
        """Authenticate admin user and return JWT token."""
        user = await self.user_repo.get_by_email(data.email)

        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException(detail="Invalid email or password")

        if user.role != UserRole.ADMIN:
            raise ForbiddenException(detail="Admin access required")

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

    async def get_current_user_profile(self, user_id: int) -> UserResponse:
        """Get current user's profile."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException(detail="User not found")
        return UserResponse.model_validate(user)
