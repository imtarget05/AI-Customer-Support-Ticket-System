# Production Deploy Runbook — Render API + Neon Postgres + Cloudflare Pages

> Live topology: `https://<app>.pages.dev` (Pages static) calls
> `https://<api>.onrender.com/api/...` (Render Docker) → **Neon Postgres**
> (serverless, external URL, `sslmode=require`).
> `docker-compose.yml` is local-only — never used in prod.

## 0. Prerequisites

- GitHub repo pushed to `main` (Render + Pages both deploy from git).
- Accounts: Render (free tier OK) + Cloudflare (free tier OK) + Neon (free tier OK).
- No secrets in git — every credential below is set on dashboards only.


## 1. Deploy API + Postgres (Render Web Service + Neon)

1. Create a Neon project → copy the **pooled connection string**, then adapt it:
   - Use the **direct** endpoint (drop `-pooler` from the hostname) for the app:
     migrations and SQLAlchemy pools behave like plain Postgres.
   - **Drop `channel_binding=require`** — psycopg2 rejects it as a startup option.
   - Keep `?sslmode=require` (TLS is mandatory on Neon).
   - Final form: `postgresql://<user>:<pw>@ep-xxxx.<region>.aws.neon.tech/<db>?sslmode=require`
2. Render dashboard → New → **Web Service** (Docker) from this repo
   (`backend/Dockerfile`, context repo root, health check `/api/health`).
3. Leave `CORS_ORIGINS` empty for now (set after Pages URL exists).
4. Wait for build (~7–18 min first time, torch dominates) → deploy.
   The first boot runs `alembic upgrade head` against Neon (creates all tables).

> Migration note: `backend/alembic/env.py` takes a **transaction-scoped**
> `pg_advisory_xact_lock` — a session-level lock silently breaks the migration
> transaction on Neon (DDL appears to run but never persists).

## 2. Render env reference

| Variable | Value |
|---|---|
| `DATABASE_URL` | Neon direct URL (§1); SQLite rejected in deployment. |
| `JWT_SECRET` | Random ≥32 chars. Never commit or bake into image. Rotate → all sessions logout. |
| `ENVIRONMENT` | `production` (enables Postgres-only + strict CORS fail-fast). |
| `ALEMBIC_MIGRATE` | `true` — idempotent `upgrade head` at boot. |
| `AI_PROVIDER` / `AI_EMBED_PROVIDER` | `stub` / `bow` until a Cloudflare token with **Workers AI → Run** permission exists (`ai/run` must return 200, not 401). |
| `BOOTSTRAP_TOKEN` | Random ≥8 chars, set **before first deploy**; blank after bootstrap (§4). |
| `CORS_ORIGINS` | Set AFTER Pages deploy: `https://<app>.pages.dev`, then redeploy API. |

## 3. Verify API health + migrate

- Health: `GET https://<api>.onrender.com/api/health` → `{"status":"ok"}` (503 = DB/migration not ready, check logs for `upgrade head`).
- Migrations run automatically at boot; concurrent instances are lock-guarded.
- Neon free tier autosuspends the compute when idle — the first request after
  idle pays a few seconds of wake-up (the API surfaces it as a short 503).

## 4. Bootstrap the first agent (once)

Free plans have **no Shell/SSH access**, so `python -m app.seed` won't run there.
The app ships a one-time `/api/auth/bootstrap` endpoint guarded by `BOOTSTRAP_TOKEN`.

1. Before the first deploy, set `BOOTSTRAP_TOKEN=<random ≥8 chars>` (keep it secret;
   `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`).
2. After the service is live, create the agent with one call:

```bash
curl -X POST https://<api>.onrender.com/api/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"name":"Support Admin","email":"admin@<your-domain>","password":"<strong-password>","setup_token":"<BOOTSTRAP_TOKEN>"}'
# -> 201 {access_token, user:{role:"agent"}}
```

3. The endpoint is strictly one-time: a second valid call returns 409 (agent exists),
   a wrong token returns 403. After bootstrapping, set `BOOTSTRAP_TOKEN=""` (or remove it)
   and redeploy so the route is disabled entirely.
4. Seeded demo accounts/tickets are local-only (`python -m app.seed`) — never run on prod.

## 5. Deploy frontend on Cloudflare Pages

1. Cloudflare dashboard → Pages → Connect repo → project name `<app>`.
2. Build settings: root `frontend/`, build `npm ci && npm run build`, output `dist`.
3. Build env: `VITE_API_URL=https://<api>.onrender.com` (Vite bakes it at build time — changing it requires rebuild).
4. Deploy → note the `https://<app>.pages.dev` URL. SPA routes (`/agent`, `/tickets/:id`) work via `public/_redirects` (`/* /index.html 200`).

## 6. Wire CORS and redeploy API

1. Render → service → Environment → set `CORS_ORIGINS=https://<app>.pages.dev` → Save (triggers redeploy).
2. Render terminates HTTPS at the boundary; no extra proxy config needed.

## 7. Prod smoke test (real user flow)

1. Open `https://<app>.pages.dev` → log in as agent.
2. Create a ticket (anonymous with email works too) → status `OPEN`, category `UNKNOWN`.
3. Agent opens ticket → AI suggest (stub) returns draft → send reply explicitly.
4. Drive lifecycle to `CLOSED` → verify new messages + 4 AI endpoints return 409.
5. Wrong-password login → 401; unauth `/api/tickets` → 401/403.

## 8. Rollback and secret rotation

- Rollback: Render → service → Deploys → redeploy previous commit. Keep Postgres; migrate forward only.
- Rotate `JWT_SECRET`: set new value → deploy → wait for old tokens to expire (`JWT_EXPIRE_MINUTES=720`) → done. All users are logged out on rotate.
- Rotate DB/provider credentials through Render controls; never commit values.

## 9. Known limits (launch)

- Free-tier sleep: API cold-starts ~30–60s after idle; Pages shows its loading state meanwhile. Upgrade to Starter if always-on is needed.
- First Docker build is slow (torch/sentence-transformers). Keep `AI_EMBED_PROVIDER=bow` on free tier to avoid OOM.
- `VITE_API_URL` is bake-time: any backend URL change needs a Pages rebuild + redeploy.
