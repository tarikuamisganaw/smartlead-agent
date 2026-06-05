# SmartLead Agent

SmartLead Agent is an AI website assistant backend for small businesses.

Week 2 includes the backend foundation from Week 1 plus local document ingestion, local RAG over demo business markdown files, conversation memory, lead create/update behavior, trace persistence, and tool-call logging.

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
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Test

```bash
cd apps/api
pytest
```

## Current Scope

Included:

- `/health`
- `/chat`
- `/conversations/{conversation_id}`
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

Not included yet:

- Frontend
- Real LLM provider calls
- Google Sheets
- Email or Slack
- Auth
- Production deployment
