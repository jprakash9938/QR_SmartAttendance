"""Dynamic QR Attendance System — FastAPI Application Entry Point.

This is the main application module that:
1. Creates the FastAPI app with metadata for Swagger/OpenAPI
2. Configures CORS, rate limiting, and security headers
3. Registers all API routers
4. Sets up database initialization on startup

Run with: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import (
    auth_router,
    class_router,
    session_router,
    attendance_router,
    teacher_router,
    admin_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================================
# Security Headers Middleware
# ============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        # TODO(security): Add strict CSP policy when frontend is deployed.
        # Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';
        response.headers["Cache-Control"] = "no-store"
        return response


# ============================================================================
# Application Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB tables on startup."""
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "## Dynamic QR Code Attendance Management System\n\n"
        "A secure REST API for managing attendance using dynamically rotating QR codes.\n\n"
        "### Teacher Workflow\n"
        "1. **Login** → `POST /api/v1/auth/login`\n"
        "2. **Create Class** → `POST /api/v1/classes`\n"
        "3. **Create Session** → `POST /api/v1/sessions`\n"
        "4. **Start Session** → `POST /api/v1/sessions/{id}/start`\n"
        "5. **Get Dynamic QR** → `GET /api/v1/sessions/{id}/qr` (refresh every 5s)\n"
        "6. **View Attendance** → `GET /api/v1/teacher/sessions/{id}/attendance`\n\n"
        "### Student Workflow\n"
        "1. **Login** → `POST /api/v1/auth/login`\n"
        "2. **Scan QR** → Frontend scans QR image\n"
        "3. **Send Token** → `POST /api/v1/attendance/mark`\n"
        "4. **Backend Validates** → Token + Session + Time + Duplicate checks\n"
        "5. **Attendance Saved** → Success response\n"
        "6. **Email Confirmation** → Async email sent\n\n"
        "### Security Features\n"
        "- JWT authentication with expiration\n"
        "- bcrypt password hashing\n"
        "- Role-based access control (TEACHER/STUDENT)\n"
        "- Rate limiting on login and attendance\n"
        "- Dynamic QR tokens (5-second expiry)\n"
        "- Server-side time validation\n"
        "- Database-level unique constraints\n"
        "- SQL injection protection via ORM\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# Middleware
# ============================================================================

# Shared Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — configured via environment variables, no wildcard in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],  # Allow necessary HTTP methods
    allow_headers=["Authorization", "Content-Type"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)


# ============================================================================
# Global Exception Handler
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler.

    Returns a generic error message to avoid leaking internal details.
    Logs the real error for debugging.
    """
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ============================================================================
# Register Routers
# ============================================================================

app.include_router(auth_router.router)
app.include_router(class_router.router)
app.include_router(session_router.router)
app.include_router(attendance_router.router)
app.include_router(teacher_router.router)
app.include_router(admin_router.router)


# ============================================================================
# Health Check
# ============================================================================


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns application health status.",
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path
    import uvicorn

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

