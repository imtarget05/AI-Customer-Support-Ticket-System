"""Error-analysis tests (confusion matrix + miss list, stub provider offline)."""

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
EVAL = BACKEND.parent / "evaluation"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(EVAL))


def test_analyze_returns_confusion_and_misses():
    from analyze_errors import analyze
    out = analyze(provider="stub", limit=92)
    assert 0.0 <= out["accuracy"] <= 1.0
    assert "refund" in out["confusion"]
    assert isinstance(out["misses"], list)


def test_export_dataset_stratified_split():
    from export_dataset import stratified_split
    rows = json.loads((EVAL / "tickets.json").read_text())
    train, val = stratified_split(rows, seed=42)
    assert len(train) + len(val) == len(rows)
    assert {r["expected_category"] for r in val} <= {r["expected_category"] for r in rows}