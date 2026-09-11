"""Customer self-registration flow (đăng ký) — separate from login (đăng nhập).

Registration creates CUSTOMER accounts only; agent accounts exist solely via
the one-time bootstrap endpoint. Registration auto-logs the user in (returns
the same TokenResponse shape as login).
"""

import pytest

from tests.conftest import login


def _payload(**overrides):
    body = {
        "name": "New Customer",
        "email": "new-customer@example.com",
        "password": "0123456789abcdef",
    }
    body.update(overrides)
    return body


def test_register_creates_customer_and_returns_token(client):
    res = client.post("/api/auth/register", json=_payload())
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "new-customer@example.com"
    assert body["user"]["name"] == "New Customer"
    assert body["user"]["role"] == "customer"


def test_register_duplicate_email_409(client):
    assert client.post("/api/auth/register", json=_payload()).status_code == 201
    res = client.post("/api/auth/register", json=_payload(name="Again"))
    assert res.status_code == 409


def test_register_email_is_case_insensitive_duplicate(client):
    assert client.post("/api/auth/register", json=_payload()).status_code == 201
    res = client.post("/api/auth/register", json=_payload(email="NEW-CUSTOMER@EXAMPLE.COM"))
    assert res.status_code == 409


def test_register_normalizes_email_lowercase(client):
    res = client.post("/api/auth/register", json=_payload(email="MiXeD@Example.COM"))
    assert res.status_code == 201
    me = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {res.json()['access_token']}"}
    )
    assert me.json()["email"] == "mixed@example.com"


def test_register_short_password_422(client):
    res = client.post("/api/auth/register", json=_payload(password="short"))
    assert res.status_code == 422


def test_register_invalid_email_422(client):
    res = client.post("/api/auth/register", json=_payload(email="not-an-email"))
    assert res.status_code == 422


def test_register_cannot_escalate_to_agent(client, db_session):
    from app.models import User

    res = client.post(
        "/api/auth/register", json=_payload(email="escalate@example.com", role="agent")
    )
    assert res.status_code == 201
    user = db_session.query(User).filter(User.email == "escalate@example.com").first()
    assert user.role == "customer"


def test_register_then_login_roundtrip(client):
    client.post("/api/auth/register", json=_payload())
    res = client.post(
        "/api/auth/login",
        json={"email": "new-customer@example.com", "password": "0123456789abcdef"},
    )
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "customer"


def test_registered_customer_can_submit_and_view_own_ticket(client):
    reg = client.post("/api/auth/register", json=_payload(email="owner@example.com"))
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/tickets",
        json={"subject": "My registered ticket", "description": "Filed by a registered customer."},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["id"]

    mine = client.get(f"/api/tickets/{ticket_id}", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["customer"]["email"] == "owner@example.com"


def test_registration_is_isolated_from_existing_flows(client):
    """Existing login/bootstrap behaviour is untouched by registration."""
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "whatever123"},
    )
    assert res.status_code == 401

    res = client.post(
        "/api/auth/bootstrap",
        json={
            "name": "Agent",
            "email": "boot-agent@example.com",
            "password": "0123456789abcdef",
            "setup_token": "no-token-set",
        },
    )
    assert res.status_code == 403  # bootstrap stays token-guarded


def test_login_helper_works_for_registered_user(client):
    client.post("/api/auth/register", json=_payload(email="helper@example.com"))
    headers = login(client, "helper@example.com", "0123456789abcdef")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200