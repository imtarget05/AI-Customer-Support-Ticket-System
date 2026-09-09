# SupportDesk — AI Customer Support Ticket System (WIP)

> **Status**: Backend MVP done, Frontend + Eval next. Honest WIP, not a finished product.

A support ticket system where AI **assists agents, never decides**: auto triage
(category/priority/summary/confidence), suggested replies, similar resolved
tickets. Agent always sends, resolves, closes. See `docs/spec.md`.

- **Stack**: FastAPI + SQLAlchemy (SQLite local, Postgres via `DATABASE_URL`), JWT, pytest.
- **AI**: stub provider by default (`AI_PROVIDER=stub`, no key needed) + OpenAI-compatible provider with schema validation + fallback.
- **Tests**: 46 pytest passing offline — `cd backend && pytest`.

## Run

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed   # demo agent@supportdesk.dev / agent1234
uvicorn app.main:app --reload  # docs: http://localhost:8000/docs
```

## Roadmap

- [x] Backend core: auth, tickets, state machine, dashboard
- [x] AI service: analyze + suggest + retrieval (stub testable)
- [ ] Frontend (React)
- [ ] `evaluation/tickets.json` + `evaluate.py`
- [ ] CI + deploy

## AI-Assisted Development

AI coding tools used for boilerplate/tests/docs; all code reviewed and tested
manually (`pytest` green, no key required).
