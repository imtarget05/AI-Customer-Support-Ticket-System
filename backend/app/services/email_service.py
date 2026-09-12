import logging, smtplib
from email.message import EmailMessage
from dataclasses import dataclass
from app.config import settings

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class EmailResult:
    status: str  # "sent" | "skipped_no_customer" | "skipped_no_config" | "failed_logged"
    detail: str = ""

def send_agent_reply(*, to_email: str | None, ticket_id: int, subject: str, body: str) -> EmailResult:
    """Không raise. stub/log/smtp thiếu config → skipped; smtp lỗi → failed_logged + logger.exception."""
    if not to_email:
        return EmailResult("skipped_no_customer", "ticket has no customer email")
    if settings.email_provider in ("stub", "log"):
        logger.info("email stub to=%s ticket=%d", to_email, ticket_id)
        return EmailResult("sent" if settings.email_provider == "log" else "skipped_no_config", settings.email_provider)
    if settings.email_provider == "smtp":
        if not (settings.smtp_host and settings.smtp_from):
            return EmailResult("skipped_no_config", "SMTP_HOST/FROM missing")
        try:
            msg = EmailMessage()
            msg["From"] = settings.smtp_from; msg["To"] = to_email
            msg["Subject"] = f"[SupportDesk #{ticket_id}] {subject}"
            msg.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_s) as s:
                s.starttls()
                if settings.smtp_user: s.login(settings.smtp_user, settings.smtp_pass)
                s.send_message(msg)
            return EmailResult("sent", "smtp")
        except Exception as exc:
            logger.exception("email send failed ticket=%d: %s", ticket_id, exc)
            return EmailResult("failed_logged", str(exc)[:200])
    return EmailResult("skipped_no_config", f"unknown provider {settings.email_provider}")