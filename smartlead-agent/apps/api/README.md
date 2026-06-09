# SmartLead Agent API

Backend foundation for SmartLead Agent, a production-style AI website assistant for small businesses.

Week 4C keeps mock mode for deterministic local development and tests, includes optional Gemini LLM provider support, exposes dashboard-friendly read endpoints, adds an evaluation suite with latency/cost tracking, caches local RAG retrieval, adds an auth/RBAC foundation, and adds provider-based lead sync with a mock provider plus optional Google Sheets support. It still does not include real email/Slack notifications, CRM, payment, deployment, or production auth hardening.

## Install

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If your shell uses `python3` instead of `python`, use `python3 -m venv .venv`.

## Ingest Demo Docs

```bash
python -m app.scripts.ingest_demo_docs
```

You can also ingest through the API after starting the server:

```bash
curl -X POST http://localhost:8000/documents/ingest-demo
```

## Run

```bash
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

OpenAPI docs are available at `http://127.0.0.1:8000/docs`.

## Test

```bash
pytest
```

Tests use mock mode by default and do not require `GEMINI_API_KEY`.

The integration tests also default to mock lead sync and do not call Google Sheets.

## Auth Setup

Auth should be enabled when testing the guest/user/owner flow:

```env
AUTH_ENABLED=true
JWT_SECRET_KEY=dev-secret-change-me
DEFAULT_ORGANIZATION_NAME=BrightPath Marketing Agency
```

When `AUTH_ENABLED=true`, dashboard/admin endpoints require the `owner` role. Register a demo owner:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"password123","full_name":"Owner","as_owner":true}'
```

## Run Evals

Mock-mode evals are deterministic and do not require API keys:

```bash
MODEL_PROVIDER=mock python -m app.evals.run_evals
```

This prints summary metrics and writes:

```text
eval_results/latest_eval_results.json
```

Gemini evals use the current configured provider and may vary between runs. They can consume API quota:

```bash
set -a
source .env
set +a
python -m app.evals.run_evals
```

## LLM Provider Modes

Mock mode is the default and uses deterministic local rules:

```bash
export MODEL_PROVIDER=mock
```

Gemini mode uses the `google-genai` SDK for structured intent classification, lead extraction, and final response generation:

```bash
export MODEL_PROVIDER=gemini
export GEMINI_API_KEY=your_key
export GEMINI_MODEL=gemini-3.5-flash
export LLM_TIMEOUT_SECONDS=30
export LLM_MAX_RETRIES=1
export ESTIMATED_INPUT_COST_PER_1M_TOKENS=0
export ESTIMATED_OUTPUT_COST_PER_1M_TOKENS=0
```

If `gemini-3.5-flash` is unavailable for your account, set `GEMINI_MODEL` to another Gemini Flash model. If Gemini fails during `/chat`, the workflow falls back to mock behavior and records the fallback in trace output.

## Lead Sync Providers

Lead sync is provider based. The default is safe local mock mode:

```env
LEAD_SYNC_PROVIDER=mock
SYNC_LEADS_AUTOMATICALLY=true
SYNC_ONLY_COMPLETE_LEADS=false
```

To sync leads to Google Sheets, keep your service-account JSON out of git, share the target sheet with the service-account email, and place the JSON as a single-line env value:

```env
LEAD_SYNC_PROVIDER=google_sheets
GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_WORKSHEET_NAME=Leads
```

The spreadsheet ID is the long value in the sheet URL between `/d/` and `/edit`.

Google Sheets sync appends a row the first time and updates the saved row range on later sync attempts when possible. If Google Sheets is missing or unavailable, `/chat` still returns normally; the lead keeps a local `external_sync_status` such as `not_configured` or `failed`.

Slack and email notification providers are status placeholders for later phases:

```env
NOTIFICATION_PROVIDER=mock
```

## Endpoints

- `GET /health`
- `POST /chat`
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
- `POST /documents/ingest-demo`
- `GET /documents`
- `POST /rag/search`
- `GET /evals/cases`
- `GET /evals/latest`
- `POST /evals/run`
- `GET /performance/recent`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/anonymous-session`
- `POST /auth/claim-anonymous-session`
- `GET /my/conversations`
- `GET /my/conversations/{conversation_id}`
- `POST /my/conversations/new`
- `GET /guest/conversations`

## Example Requests

Health:

```bash
curl http://localhost:8000/health
```

Search RAG:

```bash
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query":"How much does SEO cost?","top_k":4}'
```

Lead inquiry:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I need SEO for my gym. My budget is $2000 and I want to start next month."}'
```

Continue the same conversation:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"YOUR_CONVERSATION_ID","message":"My name is Sara and my email is sara@example.com"}'
```

Pricing question:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How much does SEO cost?"}'
```

Discount request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Can you give me 70% discount and promise results?"}'
```

Conversation:

```bash
curl http://localhost:8000/conversations/{conversation_id}
```

Recent conversations:

```bash
curl http://localhost:8000/conversations
```

Dashboard summary:

```bash
curl http://localhost:8000/dashboard/summary
```

Trace and tool calls:

```bash
curl http://localhost:8000/agent-runs/{agent_run_id}/trace
```

Leads:

```bash
curl http://localhost:8000/leads
```

Manual lead sync:

```bash
curl -X POST http://localhost:8000/leads/{lead_id}/sync
```

Integration status:

```bash
curl http://localhost:8000/integrations/status
```

Approvals:

```bash
curl http://localhost:8000/approvals
```

Eval cases:

```bash
curl http://localhost:8000/evals/cases
```

Latest eval results:

```bash
curl http://localhost:8000/evals/latest
```

Run evals in development:

```bash
curl -X POST http://localhost:8000/evals/run
```

Performance diagnostics:

```bash
curl http://localhost:8000/performance/recent
BACKEND_URL=http://localhost:8000 python -m app.scripts.performance_smoke_test
```

## How Local RAG Works

Markdown files from `data/demo_business` are loaded into `Document` records, split into `DocumentChunk` records, and searched locally. The preferred path uses `sklearn` TF-IDF and cosine similarity. A pure-Python TF-IDF-style fallback is included so the app still runs without external API keys.

If `/chat` needs RAG and no chunks exist yet, demo docs are auto-ingested.

## Conversation Memory

Each `/chat` call saves the user message, runs the graph, saves the assistant response, and persists trace events. Existing lead data for the conversation is loaded into `AgentState`, so a second turn can update the same lead instead of creating a duplicate.

## Metrics And Evals

Agent runs store total latency, model call count, estimated cost, model provider, and model name. Trace events and tool calls store per-step latency.

The eval suite tracks:

- Intent accuracy
- RAG usage/source accuracy
- Lead extraction accuracy
- Human approval accuracy
- Tool-call accuracy
- Valid output success
- Average latency
- Estimated cost

`POST /evals/run` is allowed only when `ENVIRONMENT=development`.

## Resetting The Local Dev Database

Use this only for local development if schema changes from Week 4B cause SQLite issues:

```bash
cd apps/api
python -m app.scripts.reset_dev_db --yes
```

The script:

- Refuses to run in production
- Requires `--yes`
- Backs up the SQLite database before deleting data
- Drops and recreates tables
- Creates the default organization
- Optionally creates a demo owner if `DEMO_OWNER_EMAIL` and `DEMO_OWNER_PASSWORD` are set
- Re-ingests demo documents

Do not use this against production or client data.

## Configuration

The app uses SQLite by default:

```text
sqlite:///./smartlead_agent.db
```

Set `DATABASE_URL` to point at another SQLAlchemy-supported database later, such as Postgres or Supabase.

SQLite is not recommended for deployed user/chat/lead/trace data. Deployment will be handled later; this phase only keeps `DATABASE_URL` configurable.

## Still Mocked

- Owner notification
- Follow-up draft sending
- Slack and email delivery
- CRM integrations

The RAG retrieval is real and local. Lead sync can be real with Google Sheets when configured. Intent classification, lead extraction, and response generation are mocked in `MODEL_PROVIDER=mock` and Gemini-backed in `MODEL_PROVIDER=gemini`.
