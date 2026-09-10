import pytest

"""Regression tests: AI endpoints must reject CLOSED tickets per spec §4."""

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_ai_suggest_rejects_closed_ticket(client, agent_headers, customer_headers):
    ticket_id = create_ticket(client, headers=customer_headers, subject="Closed ticket")
    close_ticket(client, ticket_id, agent_headers)
    r = client.post(f"/api/tickets/{ticket_id}/ai/suggest", headers=agent_headers)
    assert r.status_code == 409


def test_ai_analyze_rejects_closed_ticket(client, agent_headers, customer_headers):
    ticket_id = create_ticket(client, headers=customer_headers, subject="Closed ticket")
    close_ticket(client, ticket_id, agent_headers)
    r = client.post(f"/api/tickets/{ticket_id}/ai/analyze", headers=agent_headers)
    assert r.status_code == 409


def test_ai_workflow_rejects_closed_ticket(client, agent_headers, customer_headers):
    ticket_id = create_ticket(client, headers=customer_headers, subject="Closed ticket")
    close_ticket(client, ticket_id, agent_headers)
    r = client.post(f"/api/tickets/{ticket_id}/ai/workflow", headers=agent_headers)
    assert r.status_code == 409


def create_ticket(client, *, headers, subject="Test"):
    r = client.post("/api/tickets", json={"subject": subject, "description": "This is a test description"}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def close_ticket(client, ticket_id, agent_headers):
    client.patch(f"/api/tickets/{ticket_id}", json={"status": "in_progress"}, headers=agent_headers)
    client.patch(f"/api/tickets/{ticket_id}", json={"status": "resolved"}, headers=agent_headers)
    r = client.patch(f"/api/tickets/{ticket_id}", json={"status": "closed"}, headers=agent_headers)
    assert r.status_code == 200, r.text
