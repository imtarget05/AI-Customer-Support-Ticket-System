"""Model comparison tests (stub vs TF-IDF vs BERT)."""

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
    """Skip if no fine-tuned artifact; otherwise basic sanity check."""
    art = EVAL / "artifacts/distilbert/config.json"
    if not art.exists():
        pytest.skip("no fine-tuned DistilBERT artifact yet")
    from train_transformer import evaluate_transformer
    out = evaluate_transformer()
    assert 0.0 <= out["accuracy"] <= 1.0
