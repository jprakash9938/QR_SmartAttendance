"""Email notification service with SMTP and console fallback.

Sends attendance confirmation emails asynchronously.
Uses a console/mock service when SMTP is not configured (development mode).
"""

import logging
from abc import ABC, abstractmethod

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseEmailService(ABC):
    """Abstract base class for email services."""

    @abstractmethod
    async def send_attendance_confirmation(
        self,
        student_name: str,
        student_email: str,
        class_name: str,
        attendance_date: str,
        attendance_time: str,
    ) -> bool:
        """Send attendance confirmation email."""
        ...


class ConsoleEmailService(BaseEmailService):
    """Mock email service that logs to console.

    Used in development when SMTP is not configured.
    """

    async def send_attendance_confirmation(
        self,
        student_name: str,
        student_email: str,
        class_name: str,
        attendance_date: str,
        attendance_time: str,
    ) -> bool:
        """Log email to console instead of sending."""
        logger.info(
            "═══════════════════════════════════════════════════════════════"
        )
        logger.info("📧 EMAIL (Console Mock) — Attendance Confirmed")
        logger.info(
            "═══════════════════════════════════════════════════════════════"
        )
        logger.info("To: %s <%s>", student_name, student_email)
        logger.info("Subject: Attendance Confirmed")
        logger.info("───────────────────────────────────────────────────────")
        logger.info("Student: %s", student_name)
        logger.info("Class: %s", class_name)
        logger.info("Date: %s", attendance_date)
        logger.info("Time: %s", attendance_time)
        logger.info("Status: PRESENT")
        logger.info(
            "═══════════════════════════════════════════════════════════════"
        )
        return True


class SMTPEmailService(BaseEmailService):
    """Real SMTP email service.

    SMTP credentials are loaded from environment variables — never hardcoded.
    """

    async def send_attendance_confirmation(
        self,
        student_name: str,
        student_email: str,
        class_name: str,
        attendance_date: str,
        attendance_time: str,
    ) -> bool:
        """Send attendance confirmation via SMTP."""
        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Attendance Confirmed"
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = student_email

            text_body = (
                f"Dear {student_name},\n\n"
                f"Your attendance has been confirmed.\n\n"
                f"Class: {class_name}\n"
                f"Date: {attendance_date}\n"
                f"Time: {attendance_time}\n"
                f"Status: PRESENT\n\n"
                f"Thank you."
            )

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #4CAF50; color: white; padding: 20px; text-align: center;">
                    <h1>✅ Attendance Confirmed</h1>
                </div>
                <div style="padding: 20px; background: #f9f9f9;">
                    <p>Dear <strong>{student_name}</strong>,</p>
                    <p>Your attendance has been successfully recorded.</p>
                    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Class</td>
                            <td style="padding: 8px;">{class_name}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Date</td>
                            <td style="padding: 8px;">{attendance_date}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Time</td>
                            <td style="padding: 8px;">{attendance_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold;">Status</td>
                            <td style="padding: 8px; color: #4CAF50; font-weight: bold;">PRESENT</td>
                        </tr>
                    </table>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS if settings.SMTP_PORT == 465 else False,
                start_tls=True if settings.SMTP_PORT == 587 else False,
            )

            logger.info(
                "Attendance confirmation email sent to %s", student_email
            )
            return True

        except Exception:
            # Log error but don't expose details to caller
            logger.exception("Failed to send email to %s", student_email)
            return False


def get_email_service() -> BaseEmailService:
    """Factory: return SMTP service if configured, else console mock."""
    if settings.is_email_configured:
        return SMTPEmailService()
    logger.info(
        "SMTP not configured — using console email service for development"
    )
    return ConsoleEmailService()
