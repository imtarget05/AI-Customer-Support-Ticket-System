"""First-agent bootstrap tests.

Settings is a frozen dataclass, so the token is overridden via the
BOOTSTRAP_TOKEN env var + module reload (monkeypatch-safe). Each test
reloads app.api.auth / app.main so the route picks up the patched
settings object; the TestClient is built from the reloaded app.
"""

import importlib
import os

import pytest
from fastapi.testclient import TestClient

TOKEN = "test-setup-token-0123456789ab"


@pytest.fixture()
def bootstrap_client(monkeypatch, db_session):
    monkeypatch.setenv("BOOTSTRAP_TOKEN", TOKEN)
    import app.api.auth as auth_mod
    import app.config as config_mod
    import app.main as main_mod

    importlib.reload(config_mod)
    auth_mod.settings = config_mod.settings
    importlib.reload(main_mod)
    assert main_mod.settings.bootstrap_token == TOKEN
    try:
        with TestClient(main_mod.app) as c:
            yield c
    finally:
        monkeypatch.delenv("BOOTSTRAP_TOKEN", raising=False)
        importlib.reload(config_mod)
        auth_mod.settings = config_mod.settings
        importlib.reload(main_mod)
        assert os.getenv("BOOTSTRAP_TOKEN") is None


def _payload(**overrides):
    body = {
        "name": "First Agent",
        "email": "first-agent@example.com",
        "password": "0123456789abcdef",
        "setup_token": TOKEN,
    }
    body.update(overrides)
    return body


def test_bootstrap_creates_first_agent_and_token_works(bootstrap_client):
    res = bootstrap_client.post("/api/auth/bootstrap", json=_payload())
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "first-agent@example.com"
    assert body["user"]["role"] == "agent"

    me = bootstrap_client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["role"] == "agent"


def test_bootstrap_wrong_token_403(bootstrap_client):
    res = bootstrap_client.post("/api/auth/bootstrap", json=_payload(setup_token="wrong-token"))
    assert res.status_code == 403


def test_bootstrap_second_agent_409(bootstrap_client):
    first = bootstrap_client.post("/api/auth/bootstrap", json=_payload())
    assert first.status_code == 201, first.text
    second = bootstrap_client.post(
        "/api/auth/bootstrap",
        json=_payload(email="second-agent@example.com"),
    )
    assert second.status_code == 409


def test_bootstrap_wrong_token_still_403_after_agent_exists(bootstrap_client):
    first = bootstrap_client.post("/api/auth/bootstrap", json=_payload())
    assert first.status_code == 201, first.text
    res = bootstrap_client.post(
        "/api/auth/bootstrap",
        json=_payload(email="other@example.com", setup_token="wrong-token"),
    )
    assert res.status_code == 403


def test_bootstrap_disabled_without_token(client):
    assert not os.getenv("BOOTSTRAP_TOKEN"), "tests must not set BOOTSTRAP_TOKEN"
    # conftest never sets the env var, so the default settings object has no token.
    from app.config import settings as live_settings

    assert live_settings.bootstrap_token == ""
    res = client.post("/api/auth/bootstrap", json=_payload())
    assert res.status_code == 403
