"""Model comparison tests (stub vs TF-IDF; DistilBERT deferred, see docs/model-comparison.md)."""

import json
import pytest
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]  # repo root
sys.path.insert(0, str(BACKEND))
EVAL = BACKEND.parent / "evaluation"
sys.path.insert(0, str(EVAL))


def test_baseline_trains_and_scores():
    from train_baseline import train_baseline
    out = train_baseline()
    assert 0.0 <= out["accuracy"] <= 1.0 and out["macro_f1"] >= 0.0


def test_transformer_smokes_when_artifact_exists():
    """DistilBERT deferred (92 labels insufficient); skip without local exploration artifact."""
    art = EVAL / "artifacts/distilbert/config.json"
    if not art.exists():
        pytest.skip("DistilBERT deferred: 92 labels insufficient for stable fine-tune")
    from train_transformer import evaluate_transformer
    out = evaluate_transformer()
    assert 0.0 <= out["accuracy"] <= 1.0
