"""AI service tests (stub provider; spec scenarios 2 and 4 groundwork)."""

import pytest

from app.services import ai_service
from tests.conftest import create_ticket


@pytest.fixture(autouse=True)
def _reset_provider():
    yield
    ai_service.set_provider(None)


def test_stub_classification_payment_high(client, agent_headers, db_session):
    from app.models import AIPrediction

    ticket_id = create_ticket(
        client,
        subject="Card charged twice",
        description="My card was charged twice for the same order and I cannot afford this.",
    ).json()["id"]

    res = client.post(f"/api/tickets/{ticket_id}/ai/analyze", headers=agent_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["category"] == "payment"
    assert body["priority"] in ("high", "urgent")
    assert body["ai_summary"]
    assert 0 <= body["ai_confidence"] <= 1

    predictions = db_session.query(AIPrediction).filter_by(ticket_id=ticket_id).all()
    assert len(predictions) == 1
    assert predictions[0].category == "payment"
    assert predictions[0].model == "stub"


def test_stub_classification_authentication(client, agent_headers):
    ticket_id = create_ticket(
        client,
        subject="Cannot login anymore",
        description="I forgot my password and the reset link never arrives in my inbox.",
    ).json()["id"]
    res = client.post(f"/api/tickets/{ticket_id}/ai/analyze", headers=agent_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["category"] == "authentication"
    assert body["priority"] == "high"


def test_analyze_requires_agent(client, customer_headers):
    ticket_id = create_ticket(client).json()["id"]
    assert client.post(f"/api/tickets/{ticket_id}/ai/analyze").status_code == 401
    assert (
        client.post(f"/api/tickets/{ticket_id}/ai/analyze", headers=customer_headers).status_code
        == 403
    )


def test_malformed_llm_output_502_ticket_unchanged(client, agent_headers, db_session):
    """Spec scenario 2: garbage from the provider must not touch ticket data."""

    class BadProvider:
        def analyze(self, subject, description):
            raise ai_service.AIProviderError("Malformed LLM JSON: 'not json at all'")

        def suggest(self, subject, description, thread):
            raise ai_service.AIProviderError("boom")

    ticket_id = create_ticket(client).json()["id"]
    ai_service.set_provider(BadProvider())

    res = client.post(f"/api/tickets/{ticket_id}/ai/analyze", headers=agent_headers)
    assert res.status_code == 502

    detail = client.get(f"/api/tickets/{ticket_id}", headers=agent_headers).json()
    assert detail["category"] == "unknown"
    assert detail["priority"] == "normal"
    assert detail["ai_summary"] is None
    assert detail["status"] == "open"

    assert client.post(f"/api/tickets/{ticket_id}/ai/suggest", headers=agent_headers).status_code == 502


def test_malformed_json_from_openai_payload_rejected(client, agent_headers):
    """Provider returns parseable HTTP response with invalid JSON body content."""

    class JsonGarbageProvider:
        def analyze(self, subject, description):
            # Simulates an LLM whose JSON has an invalid category value.
            result = ai_service.AnalysisResult.model_validate  # noqa: F841
            import json as _json

            from pydantic import ValidationError

            try:
                ai_service.AnalysisResult.model_validate(
                    _json.loads('{"category": "wizardry", "priority": 7, "summary": "", "confidence": 9}')
                )
            except ValidationError as exc:
                raise ai_service.AIProviderError(str(exc))
            raise AssertionError("should not reach")

        def suggest(self, subject, description, thread):
            return "irrelevant"

    ticket_id = create_ticket(client).json()["id"]
    ai_service.set_provider(JsonGarbageProvider())
    res = client.post(f"/api/tickets/{ticket_id}/ai/analyze", headers=agent_headers)
    assert res.status_code == 502
    detail = client.get(f"/api/tickets/{ticket_id}", headers=agent_headers).json()
    assert detail["category"] == "unknown"


def test_suggest_returns_draft_without_sending(client, agent_headers, db_session):
    from app.models import Message

    ticket_id = create_ticket(
        client, subject="Refund question", description="Where is my refund for the returned item?"
    ).json()["id"]
    before = db_session.query(Message).count()

    res = client.post(f"/api/tickets/{ticket_id}/ai/suggest", headers=agent_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["response"]) > 20
    assert "Suggested draft" in body["response"]

    # AI must NOT send anything: message count unchanged, lifecycle unchanged.
    assert db_session.query(Message).count() == before
    assert client.get(f"/api/tickets/{ticket_id}", headers=agent_headers).json()["status"] == "open"


def test_analyze_uses_stub_without_api_key(client, agent_headers):
    """Spec scenario 5 groundwork: the whole flow runs with AI_PROVIDER=stub."""
    ticket_id = create_ticket(client).json()["id"]
    res = client.post(f"/api/tickets/{ticket_id}/ai/analyze", headers=agent_headers)
    assert res.status_code == 200
