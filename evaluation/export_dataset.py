"""Stratified 80/20 split of tickets.json (stdlib, seed=42)."""
import json
import random
from pathlib import Path

EVAL = Path(__file__).resolve().parent


def stratified_split(rows: list[dict], seed: int = 42) -> tuple[list[dict], list[dict]]:
    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r["expected_category"], []).append(r)
    rng = random.Random(seed)
    train, val = [], []
    for cat, items in by_cat.items():
        items = items[:]
        rng.shuffle(items)
        k = max(1, int(len(items) * 0.2))
        val += items[:k]
        train += items[k:]
    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


if __name__ == "__main__":
    rows = json.loads((EVAL / "tickets.json").read_text())
    train, val = stratified_split(rows)
    (EVAL / "data").mkdir(exist_ok=True)
    (EVAL / "data/train.json").write_text(json.dumps(train, indent=2))
    (EVAL / "data/val.json").write_text(json.dumps(val, indent=2))
    print(f"train={len(train)} val={len(val)}")