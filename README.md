# SupportDesk — AI Customer Support Ticket System

> **Status**: MVP complete. Honest portfolio build, not a production product.

A support ticket system where AI **assists agents, never decides**: auto triage
(category/priority/summary/confidence), suggested replies, similar resolved
tickets. The agent always sends, resolves, and closes. See `docs/spec.md`.

## Screens

- `/` — customer ticket form (with account, or anonymous with email)
- `/agent` — agent dashboard: stats cards, ticket list with status filters
- `/tickets/:id` — ticket detail: lifecycle controls, AI summary, suggested reply
  (use/edit/dismiss), similar resolved tickets, conversation thread

## Stack

- **Backend**: FastAPI + SQLAlchemy (SQLite local, PostgreSQL via `DATABASE_URL`), JWT auth (PBKDF2), pytest.
- **AI**: stub provider by default (`AI_PROVIDER=stub`, offline, no key) and an
  OpenAI-compatible provider (`AI_PROVIDER=openai`). LLM output is schema-validated;
  malformed output → 502 and ticket data is left untouched.
- **Retrieval**: hashed bag-of-words embeddings + cosine similarity over
  resolved/closed tickets ("light RAG" reference, not a chatbot).
- **Frontend**: Vite + React 18 + TypeScript.

## Run

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed                 # demo: agent@supportdesk.dev / agent1234
uvicorn app.main:app --reload      # docs: http://localhost:8000/docs

# frontend (second terminal)
cd frontend
npm install && npm run dev         # http://localhost:5173 (proxies /api to :8000)
```

## Tests

```bash
cd backend && pytest               # 46 tests, no API key / external services
cd frontend && npm run build       # tsc strict + vite build
```

## Evaluation

`evaluation/tickets.json` holds 92 labeled tickets; `evaluation/evaluate.py`
reports accuracy, macro-F1 and per-category F1 (pure stdlib):

```bash
python evaluation/evaluate.py
# Accuracy: 86/92 = 93.5% | Macro-F1: 0.94 (stub provider)
```

The remaining misses are genuine refund↔payment ambiguities — measuring the
classifier surfaced them instead of hiding them. With `AI_PROVIDER=openai`
the same script evaluates a real LLM against the same labels.

## Engineering Notes

- Ticket lifecycle (`OPEN → IN_PROGRESS → WAITING → RESOLVED → CLOSED`) is a
  backend-enforced state machine; illegal transitions return 409. Customer
  replies auto-reopen WAITING tickets; closed tickets reject messages.
- AI never mutates the lifecycle or sends messages — it only returns validated
  suggestions; the API layer persists them.
- `ai_predictions` stores every AI classification (model + confidence) for
  later evaluation.

## AI-Assisted Development

AI coding tools were used for boilerplate, test scaffolding, debugging, and
documentation. All code was reviewed and tested manually (`pytest` green, no
API key required). The AI provider is measured against a labeled dataset
(`evaluation/evaluate.py`) rather than assumed to work.

