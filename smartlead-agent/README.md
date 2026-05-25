# SmartLead Agent

SmartLead Agent is an AI website assistant backend for small businesses. Week 1 builds the backend foundation only: FastAPI endpoints, database models, schemas, a deterministic LangGraph workflow, mock LLM/RAG behavior, trace persistence, and tests.

## Structure

```text
apps/api/        FastAPI backend
data/            Demo business markdown docs
```

## Run The API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If your system exposes Python as `python3`, use `python3 -m venv .venv`.

Then open `http://127.0.0.1:8000/docs`.

## Test

```bash
cd apps/api
pytest
```

## Week 1 Scope

Included:

- `/health`
- `/chat`
- `/conversations/{conversation_id}`
- `/agent-runs/{agent_run_id}/trace`
- `/leads`
- SQLite persistence through SQLAlchemy
- Mock LangGraph workflow
- Mock intent classification, lead extraction, document search, and notifications

Not included yet:

- Frontend
- Real RAG
- Real LLM provider calls
- Google Sheets
- Email or Slack
- Auth
