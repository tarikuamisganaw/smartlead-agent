# SmartLead Agent

SmartLead Agent is a local MVP for an AI website assistant for small businesses.

Week 3C includes the backend foundation, local document ingestion, local RAG over demo business markdown files, conversation memory, lead create/update behavior, trace persistence, optional Gemini provider support, a working chat UI, and operational dashboard pages.

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

## Test

```bash
cd apps/api
pytest
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
- `/approvals`
- `/documents/ingest-demo`
- `/documents`
- `/rag/search`
- SQLite persistence through SQLAlchemy
- LangGraph workflow with local RAG and mocked LLM behavior
- Lead memory across turns
- Trace and tool-call persistence
- Next.js chat UI connected to the backend
- Dashboard pages for leads, conversations, traces, approvals, documents, and RAG testing

Not included yet:

- Real Slack, email, Google Sheets, or CRM integrations
- Auth
- Payment
- Production deployment
