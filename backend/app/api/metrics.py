# Metrics in-memory counters for AI layer.

# - ai_calls: total AI provider calls
# - ai_errors: total AI errors (502 surface)
# - latencies: list of call durations (ms)
# - confidences: list of reported confidence values

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["metrics"])  # prefix added by include_router in main.py

# In-memory state (process-level; reset for tests)
_counters = {"ai_calls": 0, "ai_errors": 0, "latencies": [], "confidences": []}

@router.get("/metrics", include_in_schema=False)
def get_metrics():
    _latency_sorted = sorted(_counters["latencies"])
    p50 = (_latency_sorted[len(_latency_sorted)//2] if _latency_sorted else 0)
    return {
        "ai_calls": _counters["ai_calls"],
        "ai_errors": _counters["ai_errors"],
        "p50_latency_ms": int(p50),
        "avg_confidence": round(sum(_counters["confidences"]) / len(_counters["confidences"]), 2) if _counters["confidences"] else None,
    }

class MetricsSnapshot(BaseModel):
    ai_calls: int
    ai_errors: int
    p50_latency_ms: int
    avg_confidence: float | None
