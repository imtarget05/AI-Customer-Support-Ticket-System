"""Lifecycle state machine tests (spec scenario 3 and related rules)."""

from tests.conftest import create_ticket


def _patch(client, headers, ticket_id, payload):
    return client.patch(f"/api/tickets/{ticket_id}", json=payload, headers=headers)


def test_full_legal_path_to_closed(client, agent_headers):
    ticket_id = create_ticket(client).json()["id"]
    for status in ("in_progress", "waiting", "in_progress", "resolved", "closed"):
        res = _patch(client, agent_headers, ticket_id, {"status": status})
        assert res.status_code == 200, res.text
        assert res.json()["status"] == status


def test_illegal_open_to_closed_409_and_unchanged(client, agent_headers):
    """Spec scenario 3: OPEN → CLOSED must be rejected."""
    ticket_id = create_ticket(client).json()["id"]
    res = _patch(client, agent_headers, ticket_id, {"status": "closed"})
    assert res.status_code == 409
    detail = res.json()["detail"]
    assert "open" in detail and "closed" in detail
    assert client.get(f"/api/tickets/{ticket_id}", headers=agent_headers).json()["status"] == "open"


def test_illegal_open_to_resolved_409(client, agent_headers):
    ticket_id = create_ticket(client).json()["id"]
    assert _patch(client, agent_headers, ticket_id, {"status": "resolved"}).status_code == 409


def test_illegal_waiting_to_resolved_409(client, agent_headers):
    ticket_id = create_ticket(client).json()["id"]
    assert _patch(client, agent_headers, ticket_id, {"status": "in_progress"}).status_code == 200
    assert _patch(client, agent_headers, ticket_id, {"status": "waiting"}).status_code == 200
    assert _patch(client, agent_headers, ticket_id, {"status": "resolved"}).status_code == 409


def test_closed_is_terminal(client, agent_headers):
    ticket_id = create_ticket(client).json()["id"]
    for status in ("in_progress", "resolved", "closed"):
        assert _patch(client, agent_headers, ticket_id, {"status": status}).status_code == 200
    assert _patch(client, agent_headers, ticket_id, {"status": "open"}).status_code == 409
    assert _patch(client, agent_headers, ticket_id, {"status": "in_progress"}).status_code == 409


def test_idempotent_status_patch_allowed(client, agent_headers):
    ticket_id = create_ticket(client).json()["id"]
    res = _patch(client, agent_headers, ticket_id, {"status": "open"})
    assert res.status_code == 200


def test_priority_update_allowed_anytime(client, agent_headers):
    ticket_id = create_ticket(client).json()["id"]
    res = _patch(client, agent_headers, ticket_id, {"priority": "urgent"})
    assert res.status_code == 200
    assert res.json()["priority"] == "urgent"


def test_patch_requires_auth(client):
    ticket_id = create_ticket(client).json()["id"]
    assert client.patch(f"/api/tickets/{ticket_id}", json={"status": "open"}).status_code == 401


def test_customer_reply_on_waiting_reopens_to_in_progress(client, agent_headers, customer_headers):
    ticket_id = create_ticket(client, headers=customer_headers).json()["id"]
    assert _patch(client, agent_headers, ticket_id, {"status": "in_progress"}).status_code == 200
    assert _patch(client, agent_headers, ticket_id, {"status": "waiting"}).status_code == 200

    res = client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={"content": "Here is the info you asked for."},
        headers=customer_headers,
    )
    assert res.status_code == 201
    assert client.get(f"/api/tickets/{ticket_id}", headers=agent_headers).json()["status"] == "in_progress"


def test_agent_message_does_not_change_status(client, agent_headers, customer_headers):
    ticket_id = create_ticket(client, headers=customer_headers).json()["id"]
    res = client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={"content": "Looking into this."},
        headers=agent_headers,
    )
    assert res.status_code == 201
    assert client.get(f"/api/tickets/{ticket_id}", headers=agent_headers).json()["status"] == "open"


def test_message_on_closed_ticket_409(client, agent_headers, customer_headers):
    ticket_id = create_ticket(client, headers=customer_headers).json()["id"]
    for status in ("in_progress", "resolved", "closed"):
        assert _patch(client, agent_headers, ticket_id, {"status": status}).status_code == 200
    res = client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={"content": "One more thing..."},
        headers=customer_headers,
    )
    assert res.status_code == 409
