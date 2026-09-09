"""Metrics endpoint tests."""

import pytest

def test_metrics_endpoint(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    body = r.json()
    assert {"ai_calls", "ai_errors", "p50_latency_ms"} <= set(body)
