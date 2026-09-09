"""Error-analysis tests (confusion matrix + miss list, stub provider offline)."""

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


def test_render_markdown_contains_confusion(tmp_path):
    from analyze_errors import analyze, render_markdown
    out = analyze(provider="stub", limit=20)
    md = render_markdown(out)
    assert "confusion" in md.lower() and "miss" in md.lower()
