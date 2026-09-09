"""TF-IDF + LogReg baseline (scikit-learn)."""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
import joblib

EVAL = Path(__file__).resolve().parent  # evaluation/


def _ensure_data():
    """Ensure train/val split exists; auto-export if missing."""
    data_dir = EVAL / "data"
    tickets_file = EVAL / "tickets.json"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    if (data_dir / "train.json").exists() and (data_dir / "val.json").exists():
        return
    if not tickets_file.exists():
        raise FileNotFoundError(f"{tickets_file} not found")
    rows = json.loads(tickets_file.read_text())
    import random
    rng = random.Random(42)
    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r["expected_category"], []).append(r)
    train, val = [], []
    for cat, items in by_cat.items():
        items = items[:]
        rng.shuffle(items)
        k = max(1, int(len(items) * 0.2))
        val += items[:k]
        train += items[k:]
    rng.shuffle(train)
    rng.shuffle(val)
    data_dir.mkdir(exist_ok=True)
    (data_dir / "train.json").write_text(json.dumps(train, indent=2))
    (data_dir / "val.json").write_text(json.dumps(val, indent=2))


def _load():
    _ensure_data()
    data_dir = EVAL / "data"
    train = json.loads((data_dir / "train.json").read_text())
    val = json.loads((data_dir / "val.json").read_text())
    Xtr = [r["subject"] + " " + r["description"] for r in train]
    ytr = [r["expected_category"] for r in train]
    Xva = [r["subject"] + " " + r["description"] for r in val]
    yva = [r["expected_category"] for r in val]
    return Xtr, ytr, Xva, yva


def train_baseline() -> dict:
    Xtr, ytr, Xva, yva = _load()
    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    Xtr_vec = vec.fit_transform(Xtr)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(Xtr_vec, ytr)
    Xva_vec = vec.transform(Xva)
    pred = clf.predict(Xva_vec)
    (EVAL / "artifacts").mkdir(exist_ok=True)
    joblib.dump((vec, clf), EVAL / "artifacts/tfidf_logreg.pkl")
    return {
        "accuracy": float(accuracy_score(yva, pred)),
        "macro_f1": float(f1_score(yva, pred, average="macro", zero_division=0)),
    }