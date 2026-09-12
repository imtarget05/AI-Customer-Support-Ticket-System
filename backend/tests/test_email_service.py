import os
import smtplib
from unittest.mock import patch

import pytest

from backend.app.services.email_service import EmailResult, send_agent_reply


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
    os.environ["EMAIL_PROVIDER"] = "smtp"
    os.environ["SMTP_HOST"] = "smtp.example.com"
    os.environ["SMTP_FROM"] = "noreply@example.com"
    with patch("backend.app.services.email_service.smtplib.SMTP") as mock_smtp_class:
        mock_smtp = mock_smtp_class.return_value
        mock_smtp.starttls.side_effect = smtplib.SMTPException("connection failed")
        result = send_agent_reply(
            to_email="user@example.com", ticket_id=1, subject="test", body="body"
        )
        assert result.status == "failed_logged"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])