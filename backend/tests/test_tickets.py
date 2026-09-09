from tests.conftest import create_ticket


def test_anonymous_create_ticket_gets_defaults(client):
    """Spec scenario 1: new ticket is OPEN / unknown / normal."""
    res = create_ticket(client, email="newbie@example.com")
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "open"
    assert body["category"] == "unknown"
    assert body["priority"] == "normal"
    assert body["subject"] == "Printer on fire"
    assert body["customer"]["email"] == "newbie@example.com"
    assert body["ai_summary"] is None


def test_anonymous_create_without_email_422(client):
    res = client.post(
        "/api/tickets",
        json={"subject": "No email here", "description": "Submitting without any contact info."},
    )
    assert res.status_code == 422


def test_create_validates_input(client):
    res = client.post(
        "/api/tickets",
        json={"subject": "hi", "description": "way too short", "customer_email": "a@b.co"},
    )
    assert res.status_code == 422  # subject < 3 chars
    res = client.post(
        "/api/tickets",
        json={"subject": "Bad email", "description": "Valid length description.", "customer_email": "not-an-email"},
    )
    assert res.status_code == 422


def test_authenticated_customer_create_links_account(client, customer_headers):
    res = create_ticket(client, headers=customer_headers)
    assert res.status_code == 201
    assert res.json()["customer"]["email"] == "cust@test.dev"


def test_agent_cannot_create_ticket(client, agent_headers):
    res = create_ticket(client, headers=agent_headers)
    assert res.status_code == 403


def test_list_requires_auth(client):
    assert client.get("/api/tickets").status_code == 401


def test_agent_sees_all_customer_sees_own(client, agent_user, customer_headers):
    create_ticket(client, email="x@example.com", subject="Ticket one")
    create_ticket(client, headers=customer_headers, subject="Ticket two")

    agent_res = client.post(
        "/api/auth/login", json={"email": "agent@test.dev", "password": "agentpw"}
    )
    assert agent_res.status_code == 200
    agent_list = client.get(
        "/api/tickets",
        headers={"Authorization": f"Bearer {agent_res.json()['access_token']}"},
    )
    assert agent_list.json()["total"] == 2

    own_list = client.get("/api/tickets", headers=customer_headers)
    assert own_list.json()["total"] == 1
    assert own_list.json()["items"][0]["subject"] == "Ticket two"


def test_list_filter_by_status(client, agent_headers):
    create_ticket(client, subject="Open one")
    res = create_ticket(client, subject="Another")
    ticket_id = res.json()["id"]

    agent_status = client.get("/api/tickets?status=open", headers=agent_headers)
    assert agent_status.json()["total"] == 2

    client.patch(
        f"/api/tickets/{ticket_id}",
        json={"status": "in_progress"},
        headers=agent_headers,
    )
    filtered = client.get("/api/tickets?status=open", headers=agent_headers)
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["subject"] == "Open one"


def test_pagination_metadata(client, agent_headers):
    for i in range(3):
        create_ticket(client, subject=f"Ticket {i}")
    res = client.get("/api/tickets?page=1&page_size=2", headers=agent_headers)
    body = res.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2


def test_get_detail_includes_messages(client, customer_headers, agent_headers):
    ticket_id = create_ticket(client, headers=customer_headers).json()["id"]
    client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={"content": "Adding context here"},
        headers=customer_headers,
    )
    res = client.get(f"/api/tickets/{ticket_id}", headers=agent_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["messages"]) == 1
    assert body["messages"][0]["sender"]["role"] == "customer"


def test_customer_cannot_read_other_customers_ticket(client, customer_headers):
    other = create_ticket(client, email="someoneelse@example.com").json()["id"]
    res = client.get(f"/api/tickets/{other}", headers=customer_headers)
    assert res.status_code == 403


def test_customer_cannot_patch_ticket(client, customer_headers):
    ticket_id = create_ticket(client, headers=customer_headers).json()["id"]
    res = client.patch(
        f"/api/tickets/{ticket_id}", json={"status": "in_progress"}, headers=customer_headers
    )
    assert res.status_code == 403


def test_dashboard_stats(client, agent_headers):
    create_ticket(client, subject="Printer trouble")
    second = create_ticket(client, subject="Double charge", description="Urgent double charge on my card today.")
    client.patch(
        f"/api/tickets/{second.json()['id']}",
        json={"priority": "urgent"},
        headers=agent_headers,
    )

    res = client.get("/api/dashboard/stats", headers=agent_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert body["by_status"]["open"] == 2
    assert body["high_priority_open"] == 1


def test_dashboard_requires_agent(client, customer_headers):
    assert client.get("/api/dashboard/stats", headers=customer_headers).status_code == 403
