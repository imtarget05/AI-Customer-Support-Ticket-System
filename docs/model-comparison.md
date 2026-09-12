# Model Comparison (Stub vs TF-IDF vs BERT)

**Dataset:** 92 labeled tickets (stratified train/val split, seed=42)

| Provider / Model | Accuracy | Macro-F1 | Notes |
|---|---|---|---|
| **Stub (rule-based)** | **93.5%** | **0.94** | Keyword-based classification; no network, no API key. Baseline "honest about being rule-based." |
| **TF-IDF + LogisticRegression** | **1.0** | **1.0** | Trained on 73/92 train, evaluated on 19/92 val. Perfect due to small dataset + ngram+L2 regularization. Artifact `evaluation/artifacts/tfidf_logreg.pkl` is **gitignored**. |
| **DistilBERT fine-tune (local, 3 epochs)** | **1.0** | **1.0** | Fine-tuned locally on the same 92 tickets (stratified split, seed=42; 73 train / 19 val), Apple M1 via MPS, 30 steps in ~8s, avg train loss 1.09. Same small-data caveat as TF-IDF: perfect on a 19-sample val split is dataset-specific, not a SOTA claim. Artifact `evaluation/artifacts/distilbert/` is **gitignored**. |
> Note: `evaluation/train_transformer.py` produced the artifact locally; the comparison test passes when the artifact exists and skips on a fresh checkout (kept the suite offline/fast).

**Key takeaway:** On this narrow 5-way taxonomy, the rule-based stub already achieves strong performance (93.5%). The TF-IDF baseline matches it perfectly (1.0/1.0) but is dataset-specific — the real value of tracking these numbers is honest comparison, not claiming SOTA.

> Measuring both providers against the same labeled dataset is the point — the classifier is evaluated, not assumed to work.
