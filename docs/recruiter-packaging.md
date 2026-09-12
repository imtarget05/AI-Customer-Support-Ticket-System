# Recruiter packaging — SupportDesk

## CV bullets (pick 3–4)

- Built a full-stack support ticket system (React/Vite, FastAPI, SQLAlchemy,
  SQLite/PostgreSQL) with AI-assisted classification, similar-ticket retrieval,
  and response drafting — AI suggests, the human agent decides and sends.
- Treated the AI layer as untrusted: added deterministic guardrails that reject
  prompt steering, refund-commitment drafts, hallucinated policy/order claims,
  and malformed LLM output — returning 502 and leaving the ticket untouched.
- Measured the classifier on a 92-ticket labeled dataset instead of assuming it
  works: rule-based stub 93.5% / 0.94 macro-F1, TF-IDF + LogReg 1.0 / 1.0,
  Llama 3.1 8B 79.3% / 0.78;
  failures cluster on refund vs payment and authentication vs technical.
- DistilBERT fine-tune deferred: 92 labels insufficient for stable fine-tune
  (see `docs/model-comparison.md`).
- Added provider reliability handling (15s timeout, one retry on transient
  failures) and a failure-isolated UI so the ticket stays usable when AI is down.
- Ran adversarial manual testing (steering, refund commitment, hallucinated
  grounding) and end-to-end regression after fixes; 133 pytest cases (1 skipped) cover auth,
  authorization, the ticket state machine, CRUD, boundaries, and AI failure modes.
- Caught and fixed a real bug during manual screenshot testing that automated
  tests missed: the detail page white-screened after AI mutations because the
  response schema lacked `messages`; fixed by refetching after each mutation.

## 2-minute demo script

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate
python -m app.seed                 # demo: agent@supportdesk.dev / agent1234
uvicorn app.main:app --reload      # http://localhost:8000/docs

# Terminal 2 — frontend
cd frontend
npm install && npm run dev         # http://localhost:5173 (proxies /api to :8000)
```

In the browser:

1. Login as agent (`agent@supportdesk.dev` / `agent1234`) — `/agent` shows
   stats cards and the ticket list with AI triage (category & priority).
2. Open ticket #1 — `/tickets/1`: AI summary with confidence, similar resolved
   tickets, and a Suggested Reply panel.
3. Click **Use in reply** — the draft lands in the editable reply box; the
   agent edits and sends. Nothing is sent until the agent sends.
4. (Optional) Break the AI provider or use an invalid token — the banner
   "AI support is unavailable…" appears and the ticket remains fully usable.

## Interview questions — answer from your own work

**What did you build, in one sentence?**
> A support ticket system where AI assists agents, never decides.

**How do you know the AI is not dangerous?**
> Its output is treated as untrusted: schema validation plus deterministic
> guardrails, verified with adversarial tests. Unsafe output is rejected, not
> shown — the agent never sees a refund promise or an invented policy.

**Why measure a stub and an LLM separately?**
> The rule-based baseline is a real benchmark. Comparing both on the same 92
> labeled tickets is the point: the classifier is evaluated, not claimed. The
> baseline beating the 8B LLM on a narrow taxonomy is an honest, useful result.

**What failure did automated tests miss?**
> A UI mutation bug: after an AI action the detail page white-screened because
> the response did not return `messages`. Pytest passed because it does not
> render the UI — manual testing caught it.

**What would you improve next?**
> Swap bag-of-words embeddings for a real embedding model, add a lightweight
> audit trail of AI drafts (edited then sent), and re-run the adversarial
> battery against a live provider once a valid token is configured.

**Why not add more AI (multi-agent, GraphRAG, MCP, Kubernetes)?**
> The story is already complete: full-stack product + AI reliability + QA
> evidence. Extra complexity would reduce credibility for an intern role.

## One-line positioning (Hitachi / Katalon)

> "I learned that testing an AI application means testing both the AI behavior
> and the surrounding software system."

> "Automated tests passed, but manual UI testing exposed a state-management bug
> after an AI mutation; I traced it to an incomplete response schema and fixed
> the frontend mutation flow."
