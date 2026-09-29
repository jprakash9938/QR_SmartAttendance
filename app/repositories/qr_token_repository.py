"""Repository layer for QRToken database operations."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import QRToken


class QRTokenRepository:
    """Data access layer for QRToken model.

    Design: Only one active token per session is maintained.
    When a new token is generated, the previous one is replaced (upsert pattern)
    to avoid creating unlimited database records every 5 seconds.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_session(self, session_id: int) -> QRToken | None:
        """Get the current (latest) QR token for a session."""
        result = await self.db.execute(
            select(QRToken)
            .where(QRToken.session_id == session_id)
            .order_by(QRToken.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, token_hash: str) -> QRToken | None:
        """Get a QR token by its hash value."""
        result = await self.db.execute(
            select(QRToken).where(QRToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def upsert_for_session(self, qr_token: QRToken) -> QRToken:
        """Replace any existing token for the session and insert a new one.

        This ensures we don't accumulate unlimited rows — only one token
        per session exists at any time.
        """
        # Delete existing tokens for this session
        await self.db.execute(
            delete(QRToken).where(QRToken.session_id == qr_token.session_id)
        )
        # Insert new token
        self.db.add(qr_token)
        await self.db.commit()
        await self.db.refresh(qr_token)
        return qr_token
