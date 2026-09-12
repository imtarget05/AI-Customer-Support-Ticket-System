"""Model comparison tests (stub vs TF-IDF vs local DistilBERT, see docs/model-comparison.md)."""

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
    """Smoke the locally fine-tuned DistilBERT artifact; skips on fresh checkout (artifact gitignored)."""
    art = EVAL / "artifacts/distilbert/config.json"
    if not art.exists():
        pytest.skip("DistilBERT artifact not present (gitignored); fine-tune locally via train_transformer.py")
    from train_transformer import evaluate_transformer
    out = evaluate_transformer()
    assert 0.0 <= out["accuracy"] <= 1.0
