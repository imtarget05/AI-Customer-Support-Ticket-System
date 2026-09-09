"""Model comparison tests (stub vs TF-IDF vs BERT)."""

import json
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