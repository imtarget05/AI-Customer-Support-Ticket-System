# Model Comparison (Stub vs TF-IDF vs BERT)

**Dataset:** 92 labeled tickets (stratified train/val split, seed=42)

| Provider / Model | Accuracy | Macro-F1 | Notes |
|---|---|---|---|
| **Stub (rule-based)** | **93.5%** | **0.94** | Keyword-based classification; no network, no API key. Baseline "honest about being rule-based." |
| **TF-IDF + LogisticRegression** | **1.0** | **1.0** | Trained on 73/92 train, evaluated on 19/92 val. Perfect due to small dataset + ngram+L2 regularization. Artifact `evaluation/artifacts/tfidf_logreg.pkl` is **gitignored**. |
| **DistilBERT fine-tune** | deferred | deferred | 92 labels insufficient for stable fine-tune; MiniLM embeddings + TF-IDF+LogReg used instead |
> Note: `evaluation/train_transformer.py` is kept for exploration; its artifact is gitignored and the test skips without the artifact.

**Key takeaway:** On this narrow 5-way taxonomy, the rule-based stub already achieves strong performance (93.5%). The TF-IDF baseline matches it perfectly (1.0/1.0) but is dataset-specific — the real value of tracking these numbers is honest comparison, not claiming SOTA.

> Measuring both providers against the same labeled dataset is the point — the classifier is evaluated, not assumed to work.
