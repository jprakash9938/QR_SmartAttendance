"""JWT token and password security utilities."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing context using bcrypt with automatic salt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with unique salt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token with expiration.

    The algorithm is hardcoded (not derived from the token) to prevent
    algorithm confusion attacks. The 'none' algorithm is rejected by
    python-jose by default when a secret is provided.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    # Hardcode algorithm — never derive from unverified token
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token.

    Returns the payload dict on success, None on failure.
    The algorithm is hardcoded for verification to prevent algorithm confusion.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],  # Hardcoded expected algorithm
        )
        return payload
    except JWTError:
        return None


def generate_qr_token() -> str:
    """Generate a cryptographically secure random QR token.

    Uses os.urandom via secrets module (CSPRNG).
    The token does not contain any sensitive information.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Create a SHA-256 hash of a QR token for secure storage.

    We store hashes instead of raw tokens so that a database compromise
    does not expose valid tokens.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
