"""Evaluate AI classification against a labeled dataset.

    python evaluation/evaluate.py              # stub provider (default, offline)
    AI_PROVIDER=openai OPENAI_API_KEY=... python evaluation/evaluate.py

Reports accuracy, macro-F1 and per-category F1. Pure stdlib — no benchmark
frameworks, no sklearn. The point: measure the classifier instead of assuming
it works.
"""

import json
import sys
from collections import Counter
from pathlib import Path

# Make the backend package importable regardless of CWD.
BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import settings  # noqa: E402
from app.services import ai_service  # noqa: E402

DATASET = Path(__file__).resolve().parent / "tickets.json"


def load_dataset() -> list[dict]:
    with DATASET.open() as f:
        return json.load(f)


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def main() -> None:
    data = load_dataset()
    categories = sorted({row["expected_category"] for row in data})

    tp: Counter = Counter()
    fp: Counter = Counter()
    fn: Counter = Counter()
    misses: list[tuple[dict, str]] = []

    for row in data:
        try:
            result = ai_service.analyze_ticket(row["subject"], row["description"])
            predicted = result.category.value
        except ai_service.AIProviderError:
            predicted = "<error>"
        expected = row["expected_category"]
        if predicted == expected:
            tp[expected] += 1
        else:
            fp[predicted] += 1
            fn[expected] += 1
            misses.append((row, predicted))

    n = len(data)
    correct = n - len(misses)
    print(f"Dataset: {n} labeled tickets | provider: {settings.ai_provider}")
    print(f"Accuracy: {correct}/{n} = {correct / n:.1%}\n")

    print(f"{'category':<16}{'precision':>10}{'recall':>10}{'f1':>10}{'support':>9}")
    f1_scores = []
    for category in categories:
        p, r, f1 = precision_recall_f1(tp[category], fp[category], fn[category])
        f1_scores.append(f1)
        support = tp[category] + fn[category]
        print(f"{category:<16}{p:>10.2f}{r:>10.2f}{f1:>10.2f}{support:>9}")

    macro_f1 = sum(f1_scores) / len(f1_scores)
    print(f"\nMacro-F1: {macro_f1:.2f}")

    if misses:
        print(f"\nMisclassified ({len(misses)}):")
        for row, predicted in misses[:10]:
            print(
                f"  #{row['id']} expected={row['expected_category']:<14}"
                f"got={predicted:<14}:: {row['subject']}"
            )


if __name__ == "__main__":
    main()

