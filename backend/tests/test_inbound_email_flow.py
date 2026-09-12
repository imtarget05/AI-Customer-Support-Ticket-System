"""Acceptance: inbound-email webhook reopens a waiting ticket (HTTP only, offline)."""

from tests.conftest import create_ticket


def test_inbound_email_reopens_ticket(client, agent_headers, customer_headers):
    # 1. Customer creates ticket (auth customer so email is cust@test.dev).
    res = create_ticket(client, headers=customer_headers)
    assert res.status_code == 201, res.text
    ticket_id = res.json()["id"]
    assert res.json()["status"] == "open"

    # 2. Agent replies.
    res = client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={"content": "We are looking into it"},
        headers=agent_headers,
    )
    assert res.status_code == 201, res.text

    # 3. Agent moves to waiting (via legal path open -> in_progress -> waiting).
    res = client.patch(
        f"/api/tickets/{ticket_id}", json={"status": "in_progress"}, headers=agent_headers
    )
    assert res.status_code == 200, res.text
    res = client.patch(
        f"/api/tickets/{ticket_id}", json={"status": "waiting"}, headers=agent_headers
    )
    assert res.status_code == 200, res.text

    # 4. Customer replies via inbound-email webhook.
    body_text = "Thanks, here is more info"
    res = client.post(
        "/api/webhooks/inbound-email",
        json={
            "from_email": "cust@test.dev",
            "subject": f"Re: [SupportDesk #{ticket_id}] issue",
            "body": body_text,
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "processed"

    # 5. Ticket has the new message and is reopened.
    res = client.get(f"/api/tickets/{ticket_id}", headers=agent_headers)
    assert res.status_code == 200, res.text
    detail = res.json()
    assert detail["status"] == "in_progress"
    assert len(detail["messages"]) >= 2
    assert detail["messages"][-1]["content"] == body_text


def test_inbound_email_reopens_resolved_ticket(client, agent_headers, customer_headers):
    # 1. Customer creates ticket.
    res = create_ticket(client, headers=customer_headers)
    assert res.status_code == 201, res.text
    ticket_id = res.json()["id"]

    # 2. Agent drives legal path open -> in_progress -> waiting -> in_progress -> resolved.
    for status in ["in_progress", "waiting", "in_progress", "resolved"]:
        res = client.patch(
            f"/api/tickets/{ticket_id}", json={"status": status}, headers=agent_headers
        )
        assert res.status_code == 200, res.text
    assert res.json()["status"] == "resolved"

    # 3. Customer replies via inbound-email webhook -> reopened to in_progress.
    body_text = "The issue is back"
    res = client.post(
        "/api/webhooks/inbound-email",
        json={
            "from_email": "cust@test.dev",
            "subject": f"Re: [SupportDesk #{ticket_id}] issue",
            "body": body_text,
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "processed"
    assert res.json()["ticket_status"] == "in_progress"

    # 4. Ticket detail confirms reopen.
    res = client.get(f"/api/tickets/{ticket_id}", headers=agent_headers)
    assert res.status_code == 200, res.text
    detail = res.json()
    assert detail["status"] == "in_progress"
    assert detail["messages"][-1]["content"] == body_text


def test_inbound_email_ignores_unknown_ticket_or_mismatch(client, customer_headers):
    # Unknown ticket id -> ignored, no crash.
    res = client.post(
        "/api/webhooks/inbound-email",
        json={
            "from_email": "cust@test.dev",
            "subject": "Re: [SupportDesk #999999] issue",
            "body": "Hello?",
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "ignored"

    # Wrong from_email (does not match ticket owner) -> ignored, no crash.
    ticket_id = create_ticket(client, headers=customer_headers).json()["id"]
    res = client.post(
        "/api/webhooks/inbound-email",
        json={
            "from_email": "stranger@example.com",
            "subject": f"Re: [SupportDesk #{ticket_id}] issue",
            "body": "I am not the owner",
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "ignored"
