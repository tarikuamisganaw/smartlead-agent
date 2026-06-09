# SmartLead Agent

SmartLead Agent is a local MVP for an AI website assistant for small businesses.

Week 4C includes the backend foundation, local document ingestion, local RAG over demo business markdown files, conversation memory, lead create/update behavior, trace persistence, optional Gemini provider support, a working chat UI, operational dashboard pages, an evaluation suite with latency/cost tracking, performance diagnostics, guest chat, signed-in chat history, auth/RBAC, and provider-based lead sync with mock mode plus optional Google Sheets support.

## Structure

```text
apps/api/        FastAPI backend
apps/web/        Next.js frontend
data/            Demo business markdown docs
```

## Run The API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.scripts.ingest_demo_docs
uvicorn app.main:app --reload
```

If your system exposes Python as `python3`, use `python3 -m venv .venv`.

Then open `http://127.0.0.1:8000/docs`.

## Run The Frontend

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Then open `http://localhost:3000`.

Dashboard pages:

- `http://localhost:3000/dashboard`
- `http://localhost:3000/dashboard/leads`
- `http://localhost:3000/dashboard/conversations`
- `http://localhost:3000/dashboard/approvals`
- `http://localhost:3000/dashboard/documents`
- `http://localhost:3000/dashboard/rag-test`
- `http://localhost:3000/dashboard/integrations`
- `http://localhost:3000/dashboard/evals`
- `http://localhost:3000/chats`
- `http://localhost:3000/login`
- `http://localhost:3000/register`

## Test

```bash
cd apps/api
pytest
```

Run deterministic mock evals:

```bash
cd apps/api
MODEL_PROVIDER=mock python -m app.evals.run_evals
```

## Current Scope

Included:

- `/health`
- `/chat`
- `/dashboard/summary`
- `/conversations`
- `/conversations/{conversation_id}`
- `/conversations/{conversation_id}/agent-runs`
- `/agent-runs`
- `/agent-runs/{agent_run_id}/trace`
- `/leads`
- `/leads/{lead_id}/sync`
- `/integrations/status`
- `/approvals`
- `/documents/ingest-demo`
- `/documents`
- `/rag/search`
- `/evals/cases`
- `/evals/latest`
- `/evals/run`
- `/performance/recent`
- `/auth/register`
- `/auth/login`
- `/auth/me`
- `/auth/anonymous-session`
- `/auth/claim-anonymous-session`
- `/my/conversations`
- `/guest/conversations`
- SQLite persistence through SQLAlchemy
- LangGraph workflow with local RAG and mocked LLM behavior
- Lead memory across turns
- Trace and tool-call persistence
- Next.js chat UI connected to the backend
- Dashboard pages for leads, conversations, traces, approvals, documents, and RAG testing
- Dashboard page for integration status and lead sync retry
- Eval suite and eval dashboard for routing, RAG, lead extraction, approvals, tool calls, latency, and estimated cost
- Guest chat and signed-in user chat history
- Auth/RBAC foundation for guest chat, signed-in personal chat history, and owner-only dashboard access
- Mock lead sync by default and optional Google Sheets lead sync when configured
- RAG index caching and performance diagnostics

Not included yet:

- Real Slack, email, or CRM integrations
- Production-grade auth/session hardening
- Payment
- Production deployment

## Access Model

- Guest visitor: can chat and submit lead info; cannot access admin data when `AUTH_ENABLED=true`.
- Signed-in user: can preserve and view their own chat history.
- Owner: can access dashboard data, leads, traces, approvals, documents, evals, and performance diagnostics.

## Performance

Use the dashboard traces or:

```bash
curl http://localhost:8000/performance/recent
BACKEND_URL=http://localhost:8000 python -m app.scripts.performance_smoke_test
```

Mock-mode chat should usually stay well under a few seconds. Gemini latency depends on network/model behavior; LLM calls have timeout/fallback behavior.

## Database Notes

SQLite is the local default through `DATABASE_URL=sqlite:///./smartlead.db`. Keep `DATABASE_URL` configurable so Postgres can be used later for deployed users, chats, leads, traces, and documents. Deployment is intentionally not part of Week 4B.

## Resetting Local Dev Database

Use only for local development if SQLite schema changes cause issues:

```bash
cd apps/api
python -m app.scripts.reset_dev_db --yes
```

The script refuses production, creates a timestamped SQLite backup when possible, recreates tables, creates the default organization, optionally creates a demo owner from env vars, and re-ingests demo docs.

## Lead Sync

The API defaults to safe mock sync:

```env
LEAD_SYNC_PROVIDER=mock
SYNC_LEADS_AUTOMATICALLY=true
```

For Google Sheets, create a service account, share the spreadsheet with the service-account email, and set:

```env
LEAD_SYNC_PROVIDER=google_sheets
GOOGLE_SHEETS_CREDENTIALS_JSON={...single-line service account JSON...}
GOOGLE_SHEETS_SPREADSHEET_ID=the_id_between_/d/_and_/edit
GOOGLE_SHEETS_WORKSHEET_NAME=Leads
```

Owner dashboard users can check `http://localhost:3000/dashboard/integrations` and manually sync leads from `http://localhost:3000/dashboard/leads`.

## Next

- Optional real email notification
- Optional Slack notification
- Production database setup
- Stronger auth/session security
