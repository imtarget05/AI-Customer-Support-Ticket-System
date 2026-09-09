# Recruiter snapshot — SupportDesk

## What it is

**SupportDesk — AI-Assisted Ticket Management.** A full-stack support ticket
system (React/Vite + FastAPI + SQLAlchemy) where AI **assists agents, never
decides**: it classifies tickets, finds similar resolved ones, and drafts a
reply — the human agent reviews, edits, and sends.

## Why it stands out

- **AI is treated as untrusted.** Deterministic guardrails reject prompt
  steering, refund-commitment drafts, hallucinated policy/order claims, and
  malformed LLM output → 502, ticket untouched.
- **Measured, not assumed.** 92 labeled tickets evaluated: rule-based stub
  **93.5% / 0.94 macro-F1**, TF-IDF + LogReg **1.0 / 1.0** (same repo, artifact
  gitignored), Llama 3.1 8B **79.3% / 0.78** — the baselines win, and the report
  says so honestly.
- **Failure-isolated UX.** When AI is down, the UI shows an explanatory banner
  and the ticket stays fully usable — fail closed on AI, not on the workflow.
- **55+ pytest cases**: auth, authorization, state machine, CRUD, boundaries,
  AI behavior, guardrail failure modes. No API key needed to run them.
- **Adversarial regression documented** in `docs/qa-followup-ai-guardrails.md`.
- **Real bug caught by manual testing** (not pytest): the detail page
  white-screened after AI mutations; traced to an incomplete response schema,
  fixed by refetching ticket detail after each agent action.

## Repo hygiene

- No AI-harness files; screenshots + evidence in `docs/screenshots/`.
- Credentials in `backend/.env` (gitignored); `.env.example` shows the shape.
- Normal commit history — no force-pushes.
