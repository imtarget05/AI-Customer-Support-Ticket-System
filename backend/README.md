# SupportDesk Backend

FastAPI + SQLAlchemy backend. See `../docs/spec.md` for the product spec.

## Run locally

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed          # demo data (agent@supportdesk.dev / agent1234)
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- SQLite by default (`supportdesk.db`); set `DATABASE_URL` for PostgreSQL.

## Tests

```bash
pytest   # no API keys or external services needed
```

## Notes

- Auth: JWT bearer; passwords hashed with PBKDF2-HMAC-SHA256 (stdlib).
- Ticket lifecycle is a backend-enforced state machine (`app/services/state_machine.py`).
- AI runs in `stub` mode by default (`AI_PROVIDER=stub`); real provider wiring lands in the AI phase.
