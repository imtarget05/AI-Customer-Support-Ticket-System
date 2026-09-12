"""Webhook HMAC signature verification (secret set → 403/200 matrix)."""

import hashlib
import hmac
import json

from tests.conftest import create_ticket


def _sign(secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


def _post(client, payload: dict, secret: str | None):
    raw = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if secret is not None:
        headers["X-Webhook-Signature"] = _sign(secret, raw)
    return client.post("/api/webhooks/inbound-email", content=raw, headers=headers)


def test_missing_signature_returns_403(client, customer_headers, monkeypatch):
    monkeypatch.setenv("INBOUND_WEBHOOK_SECRET", "testsecret123")
    res = client.post(
        "/api/webhooks/inbound-email",
        json={"from_email": "cust@test.dev", "subject": "Hi", "body": "Hello?"},
    )
    assert res.status_code == 403, res.text


def test_wrong_signature_returns_403(client, customer_headers, monkeypatch):
    monkeypatch.setenv("INBOUND_WEBHOOK_SECRET", "testsecret123")
    raw = json.dumps(
        {"from_email": "cust@test.dev", "subject": "Hi", "body": "Hello?"}
    ).encode()
    res = client.post(
        "/api/webhooks/inbound-email",
        content=raw,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": "deadbeef"},
    )
    assert res.status_code == 403, res.text


def test_correct_signature_returns_200_processed(client, customer_headers, monkeypatch):
    secret = "testsecret123"
    monkeypatch.setenv("INBOUND_WEBHOOK_SECRET", secret)
    ticket_id = create_ticket(client, headers=customer_headers).json()["id"]
    payload = {
        "from_email": "cust@test.dev",
        "subject": f"Re: [SupportDesk #{ticket_id}] issue",
        "body": "Thanks, here is more info",
    }
    res = _post(client, payload, secret)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "processed"
