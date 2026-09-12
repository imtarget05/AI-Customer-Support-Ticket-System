# Evaluation

Offline evaluation for the AI classification layer. No network, no API key required for the stub path.

- `evaluate.py` — accuracy / macro-F1 / per-category F1 for the active provider (pure stdlib), e.g. `AI_PROVIDER=stub python evaluate.py`.
- `train_baseline.py` — TF-IDF + LogisticRegression baseline (scikit-learn, in backend/requirements.txt). Artifact `artifacts/tfidf_logreg.pkl` is gitignored.
- `train_transformer.py` — local DistilBERT fine-tune (3 epochs, 92 tickets). **Exploration-only deps**: requires `torch` + `transformers` + `datasets` in the active venv — intentionally **not** in `backend/requirements.txt` (keeps the prod image lean). Artifact `artifacts/distilbert/` is gitignored.
- `generate_dataset.py` / `export_dataset.py` / `analyze_errors.py` — dataset tooling and error analysis.
