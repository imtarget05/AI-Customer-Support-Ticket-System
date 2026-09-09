# Close-Gaps Package B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vá 4 điểm yếu JD Intern GenAI: phân tích lỗi có bằng chứng, embedding thật lazy-load, fine-tune classifier thật so sánh trung thực, Docker + metrics.

**Architecture:** Giữ nguyên tắc AI-suggest-only + guardrails + stub-offline; mọi thứ mới đều additive, fallback về stub/BoW khi offline; fine-tune là artifact gitignored + script tái chạy được, không commit model binary.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, pytest, scikit-learn (TF-IDF baseline), transformers + torch CPU + datasets (fine-tune, lazy import), sentence-transformers (embedder thật, lazy-load), Docker.

**Spec:** JD Intern AI/ML GenAI + `docs/spec.md` (AI never decides, stub-offline, 502 + ticket untouched).

## Global Constraints

- `pytest` chạy offline không API key (`AI_PROVIDER=stub`).
- Không commit secret, model binary, `.venv`; credentials chỉ trong `backend/.env` (gitignored).
- AI layer không mutate ticket, không gửi message; malformed/unsafe → 502 + ticket untouched.
- Baseline thắng LLM thì báo cáo trung thực, không overclaim.
- Mỗi task 2–5 phút, kết thúc bằng lệnh verify + commit riêng.

---

## Decisions (user-approved 2026-09-09)

- Gói B: Applied + fine-tune thật (không chọn gói A/C tối thiểu).
- Embedding thật: sentence-transformers, lazy-load, fallback BoW khi offline. CI vẫn chạy stub.
- Docker scope: Dockerfile + compose + `GET /api/metrics` (latency/error/confidence).
- Branch thực thi: `feat/close-gaps-package-b` (không code trực tiếp trên main).
- Baseline neo: 89 pytest green tại commit `0ba9e40`.

---

### Task 1: Ổn định cây làm việc bẩn — DONE (`0ba9e40`)

- Verify: `backend/./.venv/bin/python -m pytest` → 89 passed.

### Task 2: Export confusion-matrix từ evaluation hiện tại

**Files:**
- Create: `evaluation/analyze_errors.py` (`analyze(provider, limit) -> dict`)
- Test: `backend/tests/test_error_analysis.py`

TDD: test `analyze()` trả accuracy/macro_f1/confusion/misses → RED (no module) → implement stdlib-only → GREEN → commit `feat(eval): confusion-matrix error analysis script`.

### Task 3: Báo cáo markdown refund↔payment, auth↔technical

**Files:**
- Create: `docs/error-analysis.md` (sinh từ script, không viết tay số liệu)
- Modify: `evaluation/analyze_errors.py` (+ `render_markdown`)

TDD: test `render_markdown` chứa confusion + misses → RED → implement → GREEN → commit `feat(eval): markdown error-analysis report`.

### Task 4: Thêm `AI_EMBED_PROVIDER` vào config

**Files:** Modify `backend/app/config.py` (+ `ai_embed_provider = os.getenv("AI_EMBED_PROVIDER", "bow")`); Test `backend/tests/test_retrieval.py`.

### Task 5: HF embedder lazy-load + fallback BoW

**Files:** Modify `backend/app/services/retrieval_service.py` (+ `embed_text()` dispatcher, `_embed_hf()` lazy, `get_embed_dim()`; giữ nguyên `embed()` BoW); + `sentence-transformers>=2.7` vào `backend/requirements.txt`.

### Task 6: Export dataset train/val split

**Files:** Create `evaluation/export_dataset.py` (`stratified_split(rows, seed=42)`, 80/20, ghi `evaluation/data/{train,val}.json`).

### Task 7: Baseline TF-IDF + LogisticRegression

**Files:** Create `evaluation/train_baseline.py` (sklearn, artifact `evaluation/artifacts/tfidf_logreg.pkl` gitignored); Test `backend/tests/test_model_comparison.py`.

### Task 8: Fine-tune DistilBERT CPU

**Files:** Create `evaluation/train_transformer.py` (`train_transformer(epochs=5)`, `evaluate_transformer()`; artifact `evaluation/artifacts/distilbert/` gitignored); Modify `.gitignore`; Test smoke (skip khi chưa có artifact, không train trong CI).

### Task 9: Bảng so sánh stub vs TF-IDF vs BERT

**Files:** Create `docs/model-comparison.md` từ số thật sau khi chạy 3 eval.

### Task 10: Dockerfile backend + compose

**Files:** Create `backend/Dockerfile`, `docker-compose.yml`. Verify: `docker build … && docker run … python -c "import app.config"`.

### Task 11: `GET /api/metrics`

**Files:** Create `backend/app/api/metrics.py` (counter in-memory: ai_calls, ai_errors, latencies, confidences); Modify `backend/app/main.py` (mount router); Test `backend/tests/test_metrics.py`.

### Task 12: README + recruiter-snapshot số thật

**Files:** Modify `README.md`, `docs/recruiter-snapshot.md`. Verify: mọi con số chạy từ eval thật.
