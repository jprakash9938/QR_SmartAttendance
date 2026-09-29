"""Core configuration module using pydantic-settings."""

import logging
import os
import secrets
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Dynamic QR Attendance System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "mysql+aiomysql://root:@localhost:3306/attendance"

    # Admin Credentials
    ADMIN_NAME: str = "Jyoti"
    ADMIN_EMAIL: str = "abc@gmail.com"
    ADMIN_PASSWORD: str = "12345678"

    # JWT Authentication
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@attendance.local"
    SMTP_USE_TLS: bool = True

    # QR Token
    QR_TOKEN_EXPIRY_SECONDS: int = 5

    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_ATTENDANCE: str = "10/minute"
    DISABLE_RATE_LIMITS: bool = False

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def resolve_jwt_secret(cls, v: str) -> str:
        """Resolve JWT secret using multi-tiered fallback.

        Resolution order:
        1. Environment variable / .env value (if non-empty)
        2. Local file jwt_secret.txt
        3. Ephemeral randomly generated secret (with severe warning)
        """
        if v:
            return v

        # Try local secret file
        secret_file = "jwt_secret.txt"
        if os.path.exists(secret_file):
            with open(secret_file, "r") as f:
                file_secret = f.read().strip()
                if file_secret:
                    return file_secret

        # Generate ephemeral secret with warning
        # TODO(security): In production, a persistent secret MUST be configured
        # via environment variable or secret management (e.g., AWS Secrets Manager, GCP Secret Manager).
        # Ephemeral secrets break horizontal scalability and invalidate all tokens on restart.
        logging.warning(
            "JWT_SECRET_KEY not configured. Generating ephemeral secret. "
            "This instance is ISOLATED — tokens are not portable across instances or restarts. "
            "Set JWT_SECRET_KEY in production!"
        )
        return secrets.token_hex(32)

    @property
    def is_email_configured(self) -> bool:
        """Check if SMTP email is properly configured."""
        return bool(self.SMTP_HOST and self.SMTP_USERNAME and self.SMTP_PASSWORD)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
