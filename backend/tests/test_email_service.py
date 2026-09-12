import os
import smtplib
from unittest.mock import patch

import pytest

from app.services.email_service import EmailResult, send_agent_reply


@pytest.fixture(autouse=True)
def isolate_email_provider(monkeypatch):
    """Isolate EMAIL_PROVIDER between tests."""
    original = os.getenv("EMAIL_PROVIDER")
    yield
    if original is None:
        os.unsetenv("EMAIL_PROVIDER")
    else:
        os.environ["EMAIL_PROVIDER"] = original


def test_stub_never_sends(monkeypatch, isolate_email_provider):
    """stub mode: never calls SMTP, returns skipped_no_config."""
    os.environ["EMAIL_PROVIDER"] = "stub"
    # Ensure SMTP_HOST/FROM are set so we don't hit skipped_no_config path
    os.environ.setdefault("SMTP_HOST", "smtp.example.com")
    os.environ.setdefault("SMTP_FROM", "noreply@example.com")
    result = send_agent_reply(to_email="user@example.com", ticket_id=1, subject="test", body="body")
    assert result.status == "skipped_no_config"


def test_no_customer_email_skipped(monkeypatch, isolate_email_provider):
    """No customer email → skipped_no_customer."""
    os.environ["EMAIL_PROVIDER"] = "stub"
    result = send_agent_reply(to_email=None, ticket_id=1, subject="test", body="body")
    assert result.status == "skipped_no_customer"


def test_smtp_failure_returns_failed_logged(monkeypatch, isolate_email_provider):
    """SMTP error: returns failed_logged, does NOT raise."""
    monkeypatch.setenv("EMAIL_PROVIDER", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.com")
    from app.config import Settings

    # NB: Settings field defaults are evaluated at import time, so a bare
    # Settings() would still carry stale values. Re-read the env explicitly.
    fresh = Settings(
        email_provider=os.getenv("EMAIL_PROVIDER", "smtp"),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_from=os.getenv("SMTP_FROM", ""),
    )
    monkeypatch.setattr("app.services.email_service.settings", fresh)
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp_class:
        # send_agent_reply uses `with smtplib.SMTP(...) as s:`, so the
        # raising instance is the context-manager handle, not return_value.
        mock_smtp = mock_smtp_class.return_value.__enter__.return_value
        mock_smtp.starttls.side_effect = smtplib.SMTPException("connection failed")
        result = send_agent_reply(
            to_email="user@example.com", ticket_id=1, subject="test", body="body"
        )
        assert result.status == "failed_logged"


def test_smtp_success_returns_sent(monkeypatch, isolate_email_provider):
    """SMTP success-path: returns sent, send_message called, Subject tagged."""
    monkeypatch.setenv("EMAIL_PROVIDER", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.com")
    from app.config import Settings

    fresh = Settings(
        email_provider="smtp",
        smtp_host="smtp.example.com",
        smtp_from="noreply@example.com",
    )
    monkeypatch.setattr("app.services.email_service.settings", fresh)
    with patch("app.services.email_service.smtplib.SMTP") as mock_smtp_class:
        smtp_handle = mock_smtp_class.return_value.__enter__.return_value
        result = send_agent_reply(
            to_email="user@example.com", ticket_id=7, subject="Hi", body="Body text"
        )
        assert result.status == "sent"
        assert smtp_handle.send_message.called
        sent = smtp_handle.send_message.call_args[0][0]
        assert sent["Subject"] == "[SupportDesk #7] Hi"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])