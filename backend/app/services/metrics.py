"""Metrics in-memory counters for AI layer.

Single source of truth for AI call counts, errors, latencies, and confidences.
Import from here (app.services.metrics) — not from app.api.metrics — to avoid
circularity when ai_service also updates counters.
"""

# In-memory state (process-level; reset for tests)
_counters = {"ai_calls": 0, "ai_errors": 0, "latencies": [], "confidences": []}


def record_call(latency_ms: int, confidence: float | None) -> None:
    """Record a successful AI provider call."""
    _counters["ai_calls"] += 1
    _counters["latencies"].append(latency_ms)
    if confidence is not None:
        _counters["confidences"].append(confidence)


def record_error() -> None:
    """Record an AI provider error."""
    _counters["ai_errors"] += 1


def get_metrics_data() -> dict:
    """Return the current metrics snapshot (used by the API endpoint)."""
    _latency_sorted = sorted(_counters["latencies"])
    p50 = _latency_sorted[len(_latency_sorted) // 2] if _latency_sorted else 0
    return {
        "ai_calls": _counters["ai_calls"],
        "ai_errors": _counters["ai_errors"],
        "p50_latency_ms": int(p50),
        "avg_confidence": round(sum(_counters["confidences"]) / len(_counters["confidences"]), 2)
        if _counters["confidences"]
        else None,
    }


def reset() -> None:
    """Reset all counters (for tests)."""
    _counters["ai_calls"] = 0
    _counters["ai_errors"] = 0
    _counters["latencies"] = []
    _counters["confidences"] = []


class MetricsSnapshot:
    """Pydantic model for the metrics endpoint response (kept for API backward compat)."""

    def __init__(self, ai_calls: int, ai_errors: int, p50_latency_ms: int, avg_confidence: float | None):
        self.ai_calls = ai_calls
        self.ai_errors = ai_errors
        self.p50_latency_ms = p50_latency_ms
        self.avg_confidence = avg_confidence