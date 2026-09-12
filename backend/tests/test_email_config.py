import os
import pytest
from dataclasses import dataclass

from app.config import settings


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch):
    """Isolate Settings from global state between tests."""
    original = {
        "EMAIL_PROVIDER": settings.email_provider,
        "SMTP_HOST": settings.smtp_host,
        "SMTP_PORT": settings.smtp_port,
        "SMTP_USER": settings.smtp_user,
        "SMTP_PASS": settings.smtp_pass,
        "SMTP_FROM": settings.smtp_from,
        "SMTP_TIMEOUT_S": settings.smtp_timeout_s,
    }
    yield
    # restore original after test
    for key, val in original.items():
        monkeypatch.setenv(key, val)


@pytest.mark.red_only
def test_smtp_settings_defaults_stub():
    """RED: defaults to stub when env vars are not set."""
    assert settings.email_provider == "stub"
    assert settings.smtp_host == ""
    assert settings.smtp_port == 587
    assert settings.smtp_user == ""
    assert settings.smtp_pass == ""
    assert settings.smtp_from == ""
    assert settings.smtp_timeout_s == 5


@pytest.mark.red_only
def test_smtp_timeout_is_float():
    """Verify SMTP timeout can be configured as float."""
    val = settings.smtp_timeout_s
    assert isinstance(val, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])