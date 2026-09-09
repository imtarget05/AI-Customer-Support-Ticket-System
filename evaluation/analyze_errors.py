"""Error analysis: confusion matrix + miss list (stdlib only)."""

import json
import os
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))
EVAL = Path(__file__).resolve().parent


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def analyze(provider: str = "stub", limit: int | None = None) -> dict:
    os.environ.setdefault("AI_PROVIDER", provider)
    from app.services import ai_service

    data = json.loads((EVAL / "tickets.json").read_text())
    if limit:
        data = data[:limit]
    tp: Counter = Counter()
    fp: Counter = Counter()
    fn: Counter = Counter()
    confusion: dict[str, dict[str, int]] = {}
    misses: list[dict] = []
    for row in data:
        try:
            pred = ai_service.analyze_ticket(row["subject"], row["description"]).category.value
        except Exception:
            pred = "<error>"
        exp = row["expected_category"]
        confusion.setdefault(exp, {}).setdefault(pred, 0)
        confusion[exp][pred] += 1
        if pred == exp:
            tp[exp] += 1
        else:
            fp[pred] += 1
            fn[exp] += 1
            misses.append(
                {"id": row["id"], "expected": exp, "predicted": pred, "subject": row["subject"]}
            )
    n, correct = len(data), sum(tp.values())
    cats = sorted({r["expected_category"] for r in data})
    f1s = [precision_recall_f1(tp[c], fp[c], fn[c])[2] for c in cats]
    return {
        "accuracy": correct / n if n else 0.0,
        "macro_f1": sum(f1s) / len(f1s),
        "confusion": confusion,
        "misses": misses,
    }


def render_markdown(out: dict) -> str:
    preds = sorted({k for v in out["confusion"].values() for k in v})
    lines = [
        "# Error analysis (stub)",
        f"Accuracy: {out['accuracy']:.1%}  Macro-F1: {out['macro_f1']:.2f}",
        "## Confusion",
        "| expected \\ predicted | " + " | ".join(preds) + " |",
    ]
    for exp, row in sorted(out["confusion"].items()):
        lines.append(f"| {exp} | " + " | ".join(str(row.get(c, 0)) for c in preds) + " |")
    lines.append("## Top misses")
    for m in out["misses"][:10]:
        lines.append(f"- #{m['id']} exp={m['expected']} got={m['predicted']}: {m['subject']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(render_markdown(analyze()))
