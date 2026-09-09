# Product Spec: SupportDesk — AI Customer Support Ticket System

> **Status**: Reviewed Draft (v1)
> **Last Updated**: 2026-09-09

## 1. Product Intent

SupportDesk is a credible, real-world support ticket system with AI **assisting support agents** — not a chatbot wearing a product costume, and not an autonomous AI system.

Core principle: **AI never controls the system. AI only suggests. The support agent always makes the final decision.**

- Customers create and track support tickets.
- Agents triage, respond, and resolve tickets from a dashboard.
- AI classifies, prioritizes, summarizes, drafts suggested replies, and retrieves similar resolved tickets to help the agent work faster.
- Every AI output is presented as a suggestion in the UI. Nothing is sent, resolved, or closed by AI.

## 2. Users (Personas)

| Persona | Goal | Primary Surfaces |
|---------|------|------------------|
| Customer | Report a problem and get a resolution | `/support` (create ticket), ticket status |
| Support Agent | Handle tickets efficiently with AI assist | Agent dashboard, ticket detail |
| Reviewer (interviewer) | Verify engineering quality | README, tests, CI, evaluation results |

## 3. Key Workflows

### Flow A — Customer creates a ticket
1. Customer opens `/support`, fills in subject + description (category/priority are auto-detected later).
2. Frontend `POST /api/tickets` → backend validates input, creates ticket with `status=OPEN`, `category=UNKNOWN`, `priority=NORMAL`, persists to the database.
3. Ticket ID is returned (e.g. `#1024`).

### Flow B — AI processing (after creation)
1. Backend sends subject+description to the LLM.
2. LLM returns JSON: `category`, `priority`, `summary`, `confidence`.
3. Backend validates the JSON schema; invalid output is discarded and the ticket stays UNKNOWN/NORMAL.
4. Ticket fields are updated; the raw prediction is stored in `ai_predictions` (model + confidence) for later evaluation.

### Flow C — Agent handles a ticket
1. Agent logs in, sees dashboard stats (Open / High-priority / Waiting / Closed) and the ticket list.
2. Opens ticket detail: customer info, category, priority, status, AI summary, message thread.
3. Views the AI suggested response and similar resolved tickets (with similarity scores) as reference.
4. Chooses to **use/edit/dismiss** the suggestion; sends the reply explicitly as an agent message.
5. Drives the lifecycle manually: OPEN → IN_PROGRESS → WAITING → RESOLVED → CLOSED.

## 4. Ticket Lifecycle (backend-enforced state machine)

```text
OPEN → IN_PROGRESS → WAITING → IN_PROGRESS → RESOLVED → CLOSED
```

- Allowed transitions are validated in the backend; illegal transitions return 409.
- AI may never change status or priority (it only *suggests*) and may never send messages.
- When a customer replies to a WAITING ticket, the backend moves it back to IN_PROGRESS (system rule, not AI).
- CLOSED tickets reject new messages.

## 5. Functional Scope (MVP)

Phase 1 — Core
1. Login (customer + agent roles)
2. Create ticket (authenticated customer, or anonymous with email/name)
3. Ticket list (filters: status, priority, category)
4. Ticket detail + message thread
5. Status / priority updates (agent only)
6. Agent dashboard stats

Phase 2 — AI (suggestion-only)
7. Auto classification (category + priority + summary + confidence)
8. Suggested response (uses current ticket + similar resolved tickets + support policy)

Phase 3 — Retrieval (light RAG, not a RAG chatbot)
9. Similar resolved tickets (embedding + cosine similarity, shown with similarity score)

Phase 4 — Engineering proof
10. Unit/integration tests (pytest)
11. Evaluation dataset (~100 labeled tickets) + `evaluate.py` (accuracy, macro-F1, per-category F1)
12. GitHub Actions CI (pytest + build)
13. Deployment (simple: React static + FastAPI + Postgres + LLM API)

## 6. Non-Functional Constraints

- **Stack**: FastAPI + PostgreSQL + React. No microservices, no Kafka/Redis/Celery/K8s in v1.
- **Database**: PostgreSQL is the production target via `DATABASE_URL`; SQLite is used for local dev and tests so the suite runs anywhere with zero services.
- **LLM access**: configurable provider via env; must include a mock/stub mode so tests run without an API key.
- **AI robustness**: LLM output is schema-validated; malformed JSON never corrupts ticket data.
- **Determinism for tests**: all AI behavior testable via stub.
- **Auth**: JWT bearer tokens; passwords hashed with PBKDF2-HMAC-SHA256 + per-user salt (stdlib) for MVP.

## 7. Data Model (six tables)

- `users` — id, name, email, role, created_at
- `tickets` — id, customer_id, subject, description, category, priority, status, ai_summary, ai_confidence, created_at, updated_at
- `messages` — id, ticket_id, sender_id, content, created_at
- `ticket_embeddings` — ticket_id, embedding
- `ai_predictions` — id, ticket_id, model, category, priority, confidence, created_at
- `ai_evaluations` — id, ticket_id, expected_category, predicted_category, correct, created_at

## 8. API Surface

```text
POST   /api/auth/login
POST   /api/tickets
GET    /api/tickets            (filters + pagination)
GET    /api/tickets/{id}
PATCH  /api/tickets/{id}       (status/priority transitions, agent only)
POST   /api/tickets/{id}/messages
POST   /api/tickets/{id}/ai/analyze
POST   /api/tickets/{id}/ai/suggest
GET    /api/tickets/{id}/similar
GET    /api/dashboard/stats
```

## 9. Evaluation

`evaluation/tickets.json` holds ~100 labeled tickets (expected category). `evaluate.py` reports accuracy, macro-F1, and per-category F1. This exists to prove: *"I didn't assume the LLM classification worked — I evaluated it against labeled examples."* No benchmark-framework claims.

## 10. Acceptance Scenarios

1. Customer submits ticket → ticket exists with status OPEN, category UNKNOWN.
2. LLM returns malformed JSON → ticket data unchanged, error logged, no crash.
3. Agent attempts an illegal status transition (e.g. OPEN → CLOSED) → 409, status unchanged.
4. Agent opens a ticket → sees a suggested response and similar resolved tickets with similarity scores; a reply is sent only via the explicit send action.
5. `pytest` passes without any LLM API key (stub mode).
6. `python evaluate.py` prints accuracy/macro-F1/per-category metrics from the labeled dataset.
7. CI runs pytest + build on push.

## 11. Out of Scope (v1)

Email/channel ingestion (email, chat widgets), SLA engine, multi-tenancy, fine-grained RBAC beyond customer/agent, sentiment analysis dashboards, knowledge-base authoring, auto-escalation, analytics beyond basic dashboard stats.

## 12. AI-Assisted Development Note

AI coding tools may be used for boilerplate, test cases, debugging, refactoring, and documentation. All generated code is reviewed and tested manually. README will state this briefly — never "AI built the entire project."
