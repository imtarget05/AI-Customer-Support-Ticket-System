"""DEFERRED: Fine-tune DistilBERT CPU on 92 tickets (demo-scale, honest about size).

Deferred because 92 labels are insufficient for a stable fine-tune
(high variance, overfits the 19-sample val split). Kept for exploration
only; the evaluated baselines are the rule-based stub and TF-IDF+LogReg.
Artifact saved to evaluation/artifacts/distilbert/; gitignored.
"""

import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import torch
import numpy as np
from datasets import Dataset

EVAL = Path(__file__).resolve().parent  # evaluation/
LABELS = sorted({r["expected_category"] for r in json.loads((EVAL / "tickets.json").read_text())})


def train_transformer(epochs: int = 3):
    """Minimal CPU fine-tune; 3 epochs on 92 samples."""
    tok = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    lab2id = {l: i for i, l in enumerate(LABELS)}

    def prep(split):
        rows = json.loads((EVAL / f"data/{split}.json").read_text())
        return Dataset.from_list(
            [{"text": r["subject"] + " " + r["description"], "label": lab2id[r["expected_category"]]} for r in rows]
        )

    tr = prep("train").map(lambda b: tok(b["text"], truncation=True, padding=True), batched=True)
    va = prep("val").map(lambda b: tok(b["text"], truncation=True, padding=True), batched=True)

    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=len(LABELS))

    args = TrainingArguments(
        output_dir=str(EVAL / "artifacts" / "distilbert"),
        num_train_epochs=epochs,
        per_device_train_batch_size=8,
        eval_strategy="no",
        save_strategy="no",
        seed=42,
        report_to="none",
    )

    trainer = Trainer(model=model, args=args, train_dataset=tr, eval_dataset=va, tokenizer=tok)
    trainer.train()
    model.save_pretrained(EVAL / "artifacts" / "distilbert")
    tok.save_pretrained(EVAL / "artifacts" / "distilbert")


def evaluate_transformer() -> dict:
    """Return accuracy/macro-F1 on val split using the saved artifact."""
    art = EVAL / "artifacts" / "distilbert"
    if not (art / "config.json").exists():
        raise FileNotFoundError("run train_transformer() first")
    tok = AutoTokenizer.from_pretrained(art)
    model = AutoModelForSequenceClassification.from_pretrained(art)
    model.eval()
    rows = json.loads((EVAL / "data/val.json").read_text())
    preds = []
    for r in rows:
        ids = tok(r["subject"] + " " + r["description"], return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = model(**ids).logits
            preds.append(int(logits.argmax(-1)))
    id2l = {i: l for i, l in enumerate(LABELS)}
    yva = [r["expected_category"] for r in rows]
    yp = [id2l[p] for p in preds]
    from sklearn.metrics import accuracy_score, f1_score
    return {"accuracy": float(accuracy_score(yva, yp)), "macro_f1": float(f1_score(yva, yp, average="macro", zero_division=0))}
