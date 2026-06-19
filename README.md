# SmartLead Agent

SmartLead Agent is an AI sales assistant for service businesses. It combines a customer-facing chat experience with a FastAPI agent backend, retrieval over business documents, lead qualification, human approval routing, owner dashboards, traceability, evaluations, and optional external integrations.

The project is built to demonstrate the engineering patterns a real business would need before trusting an AI assistant with live prospects: deterministic local development, auditable agent runs, role-based access, safe mock integrations, configurable model providers, and measurable latency/cost behavior.

## What It Demonstrates

- AI agent workflow using LangGraph nodes for intent routing, RAG, lead extraction, scoring, safety checks, actions, and final response generation.
- Retrieval-augmented answers over local markdown business documents, with optional Supabase `pgvector` retrieval and local fallback.
- Multi-turn conversation memory that updates one lead record across a prospect's journey.
- Lead scoring, lead quality classification, and owner-facing lead management.
- Human approval workflow for risky requests such as discounts, refunds, guarantees, and promised results.
- Persistent traces, tool calls, latency, model metadata, and estimated cost for each agent run.
- Guest chat, registered user chat history, owner-only dashboard access, and RBAC-backed API protection.
- Provider-based integrations for mock mode, Google Sheets lead sync, Slack notifications, and optional Resend owner email.
- Evaluation suite covering routing, retrieval, lead extraction, approval behavior, tool calls, latency, and estimated cost.

## Architecture

```text
apps/api/        FastAPI, LangGraph, SQLAlchemy, RAG, auth, integrations, evals
apps/web/        Next.js 14, TypeScript, dashboard, chat, auth screens
data/            Demo business knowledge base used for local RAG
docs/            Demo and operator checklists
```

```text
Visitor chat
    -> Next.js web app
    -> FastAPI /chat
    -> LangGraph agent workflow
    -> RAG, lead extraction, safety, actions
    -> SQLite or Postgres persistence
    -> dashboard, traces, evals, sync, notifications
```

## Tech Stack

| Area | Implementation |
| --- | --- |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Agent workflow | LangGraph |
| LLM providers |Gemini provider |
| Retrieval | Supabase/Postgres `pgvector` |
| Storage | SQLite for local development, Postgres-compatible `DATABASE_URL` |
| Auth | JWT bearer tokens, organization membership roles, guest sessions |
| Integrations | Google Sheets, Slack, optional Resend email |
| Quality | Pytest, eval runner, performance smoke test, dashboard diagnostics |

## Core Product Surfaces

Customer-facing:

- Chat assistant for pricing, services, FAQs, and lead capture.
- Guest conversation continuity through anonymous session tokens.
- Signed-in chat history for returning users.
- Safe responses when a request requires owner review.

Owner/admin:

- Dashboard summary with conversations, leads, document counts, and recent runs.
- Leads table with lead quality, sync status, and manual retry.
- Conversation detail pages with message history and agent runs.
- Trace timeline for agent reasoning, tool calls, model usage, latency, and failures.
- Approval queue for risky requests.
- Documents page for demo ingestion and custom document upload.
- RAG tester to inspect retrieved chunks.
- Integration status page for lead sync and notification providers.
- Eval dashboard for regression checks.

## Quick Start

### 1. Run The API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.scripts.ingest_demo_docs
uvicorn app.main:app --reload
```

If your system exposes Python as `python3`, use `python3 -m venv .venv`.

API docs will be available at `http://127.0.0.1:8000/docs`.

### 2. Run The Web App

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

### 3. Create An Owner Account

Use the register page or call the API:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"password123","full_name":"Owner","as_owner":true}'
```

## Demo Flow

1. Open `http://localhost:3000`.
2. Ask: `How much does SEO cost?`
3. Continue: `I need SEO for my gym. My budget is $2000.`
4. Continue: `My name is Sara and my email is sara@example.com.`
5. Ask: `Can you give me 70% discount and promise results?`
6. Review `/dashboard`, `/dashboard/leads`, `/dashboard/approvals`, and `/dashboard/traces/[agentRunId]`.

Expected result: the assistant answers from business documents, updates one lead across turns, scores the lead, sends risky requests to approval, and records a traceable agent run.

## Important Routes

Web:

- `/`
- `/login`
- `/register`
- `/chats`
- `/chats/[conversationId]`
- `/dashboard`
- `/dashboard/leads`
- `/dashboard/conversations`
- `/dashboard/conversations/[conversationId]`
- `/dashboard/traces/[agentRunId]`
- `/dashboard/approvals`
- `/dashboard/documents`
- `/dashboard/rag-test`
- `/dashboard/integrations`
- `/dashboard/evals`

API:

- `GET /`
- `GET /health`
- `GET /ready`
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
- `POST /documents/upload`
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
- `POST /my/conversations/new`
- `GET /my/conversations`
- `GET /my/conversations/{conversation_id}`
- `GET /guest/conversations`

## Testing And Evaluation

Backend tests:

```bash
cd apps/api
pytest
```

Deterministic evals:

```bash
cd apps/api
MODEL_PROVIDER=mock python -m app.evals.run_evals
```

Performance smoke test:

```bash
cd apps/api
BACKEND_URL=http://localhost:8000 python -m app.scripts.performance_smoke_test
```

## Configuration

Local development works with SQLite and mock-safe providers. Copy and customize the example files:

```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

## Deployment

For a free portfolio deployment, use Supabase/Postgres for persistence, Hugging Face Spaces for the Dockerized FastAPI backend, and Vercel for the Next.js frontend.

See [docs/free-deployment.md](docs/free-deployment.md) for the full step-by-step deployment guide.

Optional production-style services:

- Gemini for model-backed classification, extraction, and response generation.
- Supabase/Postgres for persistent storage and `pgvector` retrieval.
- Google Sheets for lead sync.
- Slack for owner/team notifications.
- Resend for optional owner email notifications.

## Production Readiness Notes

This project is intentionally built with concerns visible instead of hidden:

- Secrets are environment-driven and excluded from the dashboard.
- Agent traces and tool calls are persisted for debugging and auditability.
- LLM calls include timeout and fallback behavior.
- Admin data is protected behind owner-role checks when auth is enabled.
- Eval and performance tooling are included to catch behavior and latency regressions.


## Why This Project Matters

SmartLead Agent is more than a chat widget. It shows how to wrap an AI assistant in the operational systems a business actually needs: knowledge retrieval, lead capture, persistence, review workflows, observability, evaluation, and integration boundaries.
