"""Tests for the LangChain agent service."""

import pytest

from app.services.langchain_agent import (
    LangChainAgent,
    _ExistingProviderLLM,
    get_agent,
    reset_agent,
)


@pytest.fixture(autouse=True)
def _reset_singleton():
    yield
    reset_agent()


class TestLangChainAgent:
    def test_init(self):
        agent = LangChainAgent()
        assert agent._provider == "stub"
        assert agent._tools == {}

    def test_register_tool(self):
        agent = LangChainAgent()

        def my_tool(x: int) -> int:
            return x * 2

        agent.register_tool("double", my_tool)
        assert "double" in agent._tools
        assert agent._tools["double"](5) == 10

    def test_classify_payment_ticket(self):
        agent = LangChainAgent()
        result = agent.classify(
            subject="Card charged twice",
            description="My card was charged twice for the same order.",
        )

        assert result["category"] == "payment"
        assert result["priority"] in ("high", "urgent")
        assert result["confidence"] > 0
        assert len(result["summary"]) > 0

    def test_classify_authentication_ticket(self):
        agent = LangChainAgent()
        result = agent.classify(
            subject="Cannot login",
            description="I forgot my password and the reset link never arrives.",
        )

        assert result["category"] == "authentication"
        assert result["confidence"] > 0

    def test_draft_response(self):
        agent = LangChainAgent()
        draft = agent.draft_response(
            subject="Test issue",
            description="I need help with my account.",
            thread="",
        )

        assert isinstance(draft, str)
        assert len(draft) > 0

    def test_draft_response_with_evidence(self):
        agent = LangChainAgent()
        evidence = [
            {
                "content": "Account issues can be resolved by resetting your password.",
                "source": "faq.md",
                "score": 0.9,
            }
        ]

        draft = agent.draft_response(
            subject="Cannot login",
            description="I can't access my account.",
            thread="",
            evidence=evidence,
        )

        assert isinstance(draft, str)
        assert len(draft) > 0

    def test_get_stats(self):
        agent = LangChainAgent()
        stats = agent.get_stats()

        assert "provider" in stats
        assert "tools_registered" in stats
        assert stats["provider"] == "stub"


class TestExistingProviderLLM:
    def test_invoke(self):
        llm = _ExistingProviderLLM("stub")
        result = llm.invoke("Test prompt")
        assert isinstance(result, str)

    def test_call(self):
        llm = _ExistingProviderLLM("stub")
        result = llm("Test prompt")
        assert isinstance(result, str)


class TestSingleton:
    def test_get_agent(self):
        agent = get_agent()
        assert isinstance(agent, LangChainAgent)

    def test_reset_agent(self):
        agent1 = get_agent()
        reset_agent()
        agent2 = get_agent()
        assert agent1 is not agent2