# SmartLead Agent API

FastAPI backend for SmartLead Agent,an AI sales assistant for service businesses. The API powers customer chat, agent orchestration, document retrieval, lead qualification, owner dashboards, human approvals, evaluation runs, and external integration boundaries.

The backend is designed to be credible in a real operating environment: configurable LLM providers, persistent traces and tool calls, role-aware data access, safe integration fallbacks, and a database abstraction that can run locally on Postgres/Supabase.

## Backend Capabilities

- `POST /chat` endpoint backed by a LangGraph workflow.
- Intent classification, RAG retrieval, lead extraction, lead scoring, safety review, tool execution, and final response generation.
- Multi-turn lead memory that updates existing leads instead of duplicating them.
- Owner-only dashboard endpoints for leads, conversations, agent runs, traces, approvals, documents, evals, integrations, and performance.
- Guest sessions, authenticated users, anonymous-session claiming, and owner RBAC.
- with Supabase `pgvector` retrieval and local fallback.
- Google Sheets lead sync provider.
- Slack notification provider, and optional Resend owner email provider.
- Persisted model metadata, estimated cost, latency, tool calls, and trace events for each agent run.
- Regression eval runner and performance smoke test.

## Architecture

```text
app/main.py                  FastAPI app factory, CORS, readiness checks
app/api/routes.py            Chat, dashboard, RAG, eval, integration, and performance routes
app/api/auth_routes.py       Register, login, current user, anonymous sessions
app/workflow/graph.py        LangGraph workflow definition
app/workflow/nodes.py        Agent nodes for routing, RAG, leads, safety, actions, response
app/services/                Auth, RAG, LLM, lead, trace, document, integration services
app/models.py                SQLAlchemy persistence models
app/evals/                   Eval cases and runner
app/scripts/                 Ingestion, reset, and performance scripts
tests/                       API, workflow, RAG, auth, metrics, and integration tests
```

## Agent Flow

```text
User message
  -> intent_router
  -> optional rag
  -> lead_qualification
  -> lead_scoring
  -> safety
  -> action
  -> final_response
```

Each run can persist:

- Conversation messages
- Lead record and lead score
- Retrieved document chunks
- Human approval requests
- Tool calls
- Trace events
- Provider/model metadata
- Latency and estimated cost

## Install

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If your shell uses `python3`, create the environment with `python3 -m venv .venv`.

## Environment

Create `apps/api/.env` from the example file:

```bash
cp .env.example .env
```


## Ingest Demo Documents

```bash
python -m app.scripts.ingest_demo_docs
```

Or ingest through the API after the server starts:

```bash
curl -X POST http://localhost:8000/documents/ingest-demo
```

## Run

```bash
uvicorn app.main:app --reload
```

Local endpoints:

- API: `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- Readiness: `http://127.0.0.1:8000/ready`

## Auth And RBAC

When `AUTH_ENABLED=true`, owner/admin data requires an owner membership. Register a demo owner:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"password123","full_name":"Owner","as_owner":true}'
```

Access model:

- Guest visitor: can chat through an anonymous session and submit lead details.
- Signed-in user: can preserve and view personal chat history.
- Owner: can access dashboard data, leads, traces, approvals, documents, evals, performance diagnostics, and integration controls.

## API Surface

Public and chat:

- `GET /`
- `GET /health`
- `GET /ready`
- `POST /chat`

Auth:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/anonymous-session`
- `POST /auth/claim-anonymous-session`

Owner/dashboard:

- `GET /dashboard/summary`
- `GET /conversations`
- `GET /conversations/{conversation_id}`
- `GET /conversations/{conversation_id}/agent-runs`
- `GET /agent-runs`
- `GET /agent-runs/{agent_run_id}/trace`
- `GET /leads`
- `POST /leads/{lead_id}/sync`
- `GET /integrations/status`
- `GET /approvals`
- `GET /documents`
- `POST /documents/ingest-demo`
- `POST /documents/upload`
- `POST /rag/search`
- `GET /evals/cases`
- `GET /evals/latest`
- `POST /evals/run`
- `GET /performance/recent`

User conversation history:

- `POST /my/conversations/new`
- `GET /my/conversations`
- `GET /my/conversations/{conversation_id}`
- `GET /guest/conversations`

## LLM Provider Modes

Gemini mode enables model-backed classification, extraction, and response generation:

```env
MODEL_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-3.5-flash
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=1
```

If Gemini fails during `/chat`, the workflow falls back to safe mock behavior and records the fallback in the trace.

## RAG Options

Local mode uses the ingested documents and a local retrieval index:

```env

```

Supabase/Postgres mode uses SQLAlchemy storage plus optional `pgvector` retrieval:

```env
DATABASE_URL=postgresql+psycopg://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:6543/postgres?sslmode=require
RAG_PROVIDER=supabase
RAG_VECTOR_DIMENSION=768
RAG_FALLBACK_TO_LOCAL=true
EMBEDDING_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

Enable `pgvector` once in Supabase:

```sql
create extension if not exists vector;
```

If automatic vector setup is not permitted, run:

```sql
alter table document_chunks
add column if not exists embedding vector(768);

create index if not exists ix_document_chunks_embedding
on document_chunks using ivfflat (embedding vector_cosine_ops);
```

When vector search is unavailable and `RAG_FALLBACK_TO_LOCAL=true`, `/chat` keeps working with local retrieval.

## Lead Sync

Mock mode is the safe default:

```env
LEAD_SYNC_PROVIDER=mock
SYNC_LEADS_AUTOMATICALLY=true
SYNC_ONLY_COMPLETE_LEADS=false
```

Google Sheets sync:

```env
LEAD_SYNC_PROVIDER=google_sheets
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_WORKSHEET_NAME=Leads
```

Share the sheet with the service-account email. The provider appends a row on first sync and updates the saved row range on later sync attempts when possible. If Google Sheets is missing or unavailable, chat still succeeds and the lead records an external sync status such as `not_configured` or `failed`.

## Notifications

```

Slack owner/team notifications:

```env
NOTIFICATION_PROVIDERS=slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

Optional owner email through Resend:

```env
NOTIFICATION_PROVIDERS=slack,email
RESEND_API_KEY=...
OWNER_EMAIL=owner@example.com
FROM_EMAIL=SmartLead <noreply@yourdomain.com>
OWNER_NAME=Business Owner
```

Email is optional and requires a verified sending domain or approved test sender. Customer follow-up emails are disabled by default.

## Docker Deployment

The repository root includes a Dockerfile for deploying this API as a stateless container. It copies `apps/api` and the demo `data` folder, installs Python dependencies, and starts Uvicorn on port `7860`.

For the full free deployment path with Supabase, Hugging Face Spaces, and Vercel, see [../../docs/free-deployment.md](../../docs/free-deployment.md).

## Testing

Run the backend test suite:

```bash
pytest
```

Tests are built around mock-safe defaults and do not require Gemini, Google Sheets, Slack, or Resend credentials.

Run deterministic evals:

```bash
MODEL_PROVIDER=mock python -m app.evals.run_evals
```

Run evals with the configured provider:

```bash
set -a
source .env
set +a
python -m app.evals.run_evals
```

The runner writes:

```text
eval_results/latest_eval_results.json
```

## Performance Diagnostics

Use the API:

```bash
curl http://localhost:8000/performance/recent
```

Or run a smoke test against a running backend:

```bash
BACKEND_URL=http://localhost:8000 python -m app.scripts.performance_smoke_test
```

Mock-mode chat should stay comfortably fast. Gemini latency depends on network and model behavior, so the API records latency, model calls, and fallback information for inspection.

## Local Database Reset

For local development only:

```bash
python -m app.scripts.reset_dev_db --yes
```

The script refuses production-style resets unless explicitly enabled, creates a timestamped SQLite backup when possible, recreates tables, creates the default organization, optionally creates a demo owner from env vars, and re-ingests demo documents.



## Implemented safeguards:

- Environment-driven configuration
- Auth/RBAC checks on admin data
- LLM timeout and fallback behavior
- Persistent traces and tool calls
- Evals and performance diagnostics
- Postgres-compatible database configuration
- vector retrieval with local fallback

