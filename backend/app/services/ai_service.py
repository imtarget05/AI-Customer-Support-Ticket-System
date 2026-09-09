"""AI service (suggestion-only).

Providers:
    stub   — deterministic keyword/rule-based (default; no network, no API key)
    openai — OpenAI-compatible chat completions (AI_PROVIDER=openai)

Contracts:
    analyze_ticket()  -> AnalysisResult  (validated; raises AIProviderError)
    suggest_response() -> str

The AI layer NEVER mutates tickets. The API layer decides what to persist,
after validation succeeds. Malformed LLM output raises AIProviderError and
leaves ticket data untouched (spec scenario 2).
"""

import json
import re
from typing import Protocol

import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.enums import TicketCategory, TicketPriority


class AIProviderError(Exception):
    """Any failure talking to, or parsing output from, the AI provider."""


class AnalysisResult(BaseModel):
    category: TicketCategory
    priority: TicketPriority
    summary: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0.0, le=1.0)


class AnalysisProvider(Protocol):
    def analyze(self, subject: str, description: str) -> AnalysisResult: ...

    def suggest(self, subject: str, description: str, thread: str) -> str: ...


# ---------------------------------------------------------------- stub provider

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    TicketCategory.AUTHENTICATION.value: [
        "password", "login", "log in", "sign in", "account locked", "reset",
        "mfa", "2fa", "otp", "access denied",
    ],
    TicketCategory.PAYMENT.value: [
        "charge", "charged", "card", "payment", "billed", "invoice", "checkout",
        "double", "twice",
    ],
    TicketCategory.REFUND.value: [
        "refund", "money back", "reimburse", "returned item", "return label",
    ],
    TicketCategory.TECHNICAL.value: [
        "error", "bug", "crash", "broken", "not working", "fails", "sync",
        "update", "app", "screen", "loop", "notification", "export", "stale",
    ],
}

URGENT_WORDS = ["urgent", "asap", "immediately", "fraud", "unauthorized", "stolen", "legal"]
HIGH_WORDS = ["cannot", "can't", "unable", "blocked", "denied", "twice", "double", "never received"]
LOW_WORDS = ["suggestion", "feature request", "idea", "feedback", "nice to have"]


def _stub_category(text: str) -> tuple[TicketCategory, int]:
    scores = {
        value: sum(1 for kw in keywords if kw in text)
        for value, keywords in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        # No keyword evidence at all → falls into the catch-all bucket.
        return TicketCategory.OTHER, 0
    return TicketCategory(best), scores[best]


def _stub_priority(text: str) -> TicketPriority:
    if any(w in text for w in URGENT_WORDS):
        return TicketPriority.URGENT
    if any(w in text for w in HIGH_WORDS):
        return TicketPriority.HIGH
    if any(w in text for w in LOW_WORDS):
        return TicketPriority.LOW
    return TicketPriority.NORMAL


def _stub_summary(subject: str, description: str) -> str:
    first_sentences = re.split(r"(?<=[.!?])\s+", description.strip())
    body = " ".join(first_sentences[:2])[:220]
    return f"Customer reports: {subject.strip()} — {body}"


class StubProvider:
    """Deterministic, testable stand-in. Honest about being rule-based."""

    def analyze(self, subject: str, description: str) -> AnalysisResult:
        text = f"{subject} {description}".lower()
        category, score = _stub_category(text)
        confidence = min(0.9, 0.4 + 0.15 * score) if score else 0.3
        return AnalysisResult(
            category=category,
            priority=_stub_priority(text),
            summary=_stub_summary(subject, description),
            confidence=round(confidence, 2),
        )

    def suggest(self, subject: str, description: str, thread: str) -> str:
        text = f"{subject} {description}".lower()
        category, _ = _stub_category(text)
        empathy = {
            TicketCategory.AUTHENTICATION.value: "I'm sorry you're locked out of your account.",
            TicketCategory.PAYMENT.value: "I'm sorry about the billing trouble.",
            TicketCategory.REFUND.value: "Thanks for your patience while we sort out your refund.",
            TicketCategory.TECHNICAL.value: "Sorry you're hitting this issue.",
        }.get(category.value, "Thanks for reaching out.")
        return (
            f"Hi, thanks for contacting support about \"{subject.strip()}\". {empathy} "
            f"Could you confirm the details above so I can look into it right away? "
            f"[Suggested draft — please review and edit before sending.]"
        )


# -------------------------------------------------------------- openai provider

OPENAI_TIMEOUT_SECONDS = 30.0


class OpenAIProvider:
    """OpenAI-compatible chat completions (works with any /v1 endpoint)."""

    def __init__(self) -> None:
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.ai_model

    def _chat(self, system: str, user: str, json_mode: bool) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.2,
                    **({"response_format": {"type": "json_object"}} if json_mode else {}),
                },
                timeout=OPENAI_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIProviderError(f"LLM request failed: {exc}") from exc

    def analyze(self, subject: str, description: str) -> AnalysisResult:
        categories = ", ".join(c.value for c in TicketCategory)
        priorities = ", ".join(p.value for p in TicketPriority)
        raw = self._chat(
            "You are a support-ticket triage assistant. Reply with JSON only: "
            '{"category": <one of: %s>, "priority": <one of: %s>, '
            '"summary": <one-sentence summary>, "confidence": <0.0-1.0>}' % (categories, priorities),
            f"Subject: {subject}\n\nDescription:\n{description}",
            json_mode=True,
        )
        try:
            return AnalysisResult.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValueError) as exc:
            raise AIProviderError(f"Malformed LLM JSON: {raw[:200]!r}") from exc

    def suggest(self, subject: str, description: str, thread: str) -> str:
        return self._chat(
            "You are a support agent assistant. Draft a concise, friendly reply for the "
            "support agent to review. Never promise refunds or account changes. "
            "Output plain text only.",
            f"Subject: {subject}\n\nDescription:\n{description}\n\nConversation so far:\n{thread}",
            json_mode=False,
        )


# ------------------------------------------------------------------- dispatch

_provider: AnalysisProvider | None = None


def get_provider() -> AnalysisProvider:
    global _provider
    if _provider is None:
        _provider = OpenAIProvider() if settings.ai_provider == "openai" else StubProvider()
    return _provider


def set_provider(provider: AnalysisProvider | None) -> None:
    """Test hook: inject a fake provider or None to reset to env default."""
    global _provider
    _provider = provider


def analyze_ticket(subject: str, description: str) -> AnalysisResult:
    return get_provider().analyze(subject, description)


def suggest_response(subject: str, description: str, thread: str) -> str:
    return get_provider().suggest(subject, description, thread)
