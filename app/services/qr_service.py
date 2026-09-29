"""QR token service — business logic for dynamic QR code generation."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.core.security import generate_qr_token, hash_token
from app.models.models import AttendanceSession, QRToken, SessionStatus
from app.repositories.qr_token_repository import QRTokenRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.schemas import QRTokenResponse

settings = get_settings()


class QRTokenService:
    """Service handling dynamic QR token generation and validation.

    Design decisions:
    1. Tokens are cryptographically random (secrets.token_urlsafe) — no
       sensitive data encoded in the token.
    2. Token hashes (SHA-256) are stored in DB, not raw tokens.
    3. Only ONE token per session exists (upsert pattern) to prevent
       unbounded database growth from 5-second refresh cycles.
    4. Expiry is validated against server time (UTC), not client time.
    5. Token validity defaults to 5 seconds.
    """

    def __init__(self, db: AsyncSession):
        self.qr_repo = QRTokenRepository(db)
        self.session_repo = SessionRepository(db)

    async def generate_token(
        self, session_id: int, teacher_id: int
    ) -> QRTokenResponse:
        """Generate a new dynamic QR token for a session.

        Only the teacher who owns the session can generate tokens.
        The session must be ACTIVE.
        """
        # Verify session exists and teacher owns it
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundException(detail="Session not found")

        if session.class_ and session.class_.teacher_id != teacher_id:
            raise ForbiddenException(detail="You do not own this session")

        if session.status != SessionStatus.ACTIVE:
            raise BadRequestException(detail="Session is not active")

        from app.models.models import utcnow

        # Check if session time window is still valid
        now = utcnow()
        if now > session.end_time:
            raise BadRequestException(detail="Session has ended")

        # Generate cryptographically secure token
        raw_token = generate_qr_token()
        token_hash_value = hash_token(raw_token)
        expires_at = now + timedelta(seconds=settings.QR_TOKEN_EXPIRY_SECONDS)

        # Upsert: replace existing token for this session
        qr_token = QRToken(
            session_id=session_id,
            token_hash=token_hash_value,
            expires_at=expires_at,
        )
        await self.qr_repo.upsert_for_session(qr_token)

        return QRTokenResponse(
            session_id=session_id,
            token=raw_token,
            expires_at=expires_at,
        )

    async def validate_token(
        self, session_id: int, raw_token: str
    ) -> bool:
        """Validate a QR token for attendance marking.

        Checks:
        1. Token hash exists in DB
        2. Token belongs to the correct session
        3. Token has not expired (server time)

        Returns True if valid, raises appropriate exception otherwise.
        """
        token_hash_value = hash_token(raw_token)
        qr_token = await self.qr_repo.get_by_hash(token_hash_value)

        if not qr_token:
            raise BadRequestException(detail="Invalid QR token")

        if qr_token.session_id != session_id:
            raise BadRequestException(detail="Token does not belong to this session")

        from app.models.models import utcnow

        now = utcnow()
        if now > qr_token.expires_at:
            raise BadRequestException(detail="QR code has expired")

        return True
