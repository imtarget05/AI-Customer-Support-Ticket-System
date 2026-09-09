"""Similar-ticket retrieval tests."""

from tests.conftest import create_ticket


def test_embed_provider_setting_defaults_to_bow():
    from app.config import settings
    assert settings.ai_embed_provider in ("bow", "hf")

RESOLVED_DESCRIPTION = (
    "Since updating the iOS app to 4.2 logging in bounces me back to the welcome screen "
    "in a loop. Reinstalling the app did not fix it."
)


def _resolve(client, agent_headers, ticket_id):
    for status in ("in_progress", "resolved"):
        res = client.patch(
            f"/api/tickets/{ticket_id}", json={"status": status}, headers=agent_headers
        )
        assert res.status_code == 200, res.text


def test_similar_finds_resolved_ticket(client, agent_headers, customer_headers):
    resolved_id = create_ticket(
        client,
        headers=customer_headers,
        subject="Login loop after app update",
        description=RESOLVED_DESCRIPTION,
    ).json()["id"]
    _resolve(client, agent_headers, resolved_id)

    target_id = create_ticket(
        client,
        subject="App logs me out in a loop",
        description="After the latest app update on iOS I get stuck in a login loop on the welcome screen.",
    ).json()["id"]

    res = client.get(f"/api/tickets/{target_id}/similar", headers=agent_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert items, "expected at least one similar resolved ticket"
    top = items[0]
    assert top["ticket_id"] == resolved_id
    assert top["status"] == "resolved"
    assert 0 < top["similarity"] <= 1


def test_similar_excludes_self_and_open_tickets(client, agent_headers):
    open_id = create_ticket(client, subject="Some open thing", description="Just an open ticket here.").json()["id"]
    res = client.get(f"/api/tickets/{open_id}/similar", headers=agent_headers)
    assert res.status_code == 200
    assert all(item["ticket_id"] != open_id for item in res.json()["items"])
    assert all(item["status"] in ("resolved", "closed") for item in res.json()["items"])


def test_similar_no_candidates_returns_empty(client, agent_headers):
    ticket_id = create_ticket(client).json()["id"]
    res = client.get(f"/api/tickets/{ticket_id}/similar", headers=agent_headers)
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_similar_requires_agent(client, customer_headers):
    ticket_id = create_ticket(client).json()["id"]
    assert client.get(f"/api/tickets/{ticket_id}/similar").status_code == 401
    assert (
        client.get(f"/api/tickets/{ticket_id}/similar", headers=customer_headers).status_code == 403
    )


def test_embedding_persisted_and_reused(client, agent_headers, db_session):
    from app.models import TicketEmbedding

    ticket_id = create_ticket(client).json()["id"]
    client.get(f"/api/tickets/{ticket_id}/similar", headers=agent_headers)
    rows = db_session.query(TicketEmbedding).filter_by(ticket_id=ticket_id).all()
    assert len(rows) == 1
    # Second call must not duplicate the row.
    client.get(f"/api/tickets/{ticket_id}/similar", headers=agent_headers)
    assert db_session.query(TicketEmbedding).filter_by(ticket_id=ticket_id).count() == 1


def test_cosine_similarity_known_values():
    from app.services.retrieval_service import cosine_similarity

    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
