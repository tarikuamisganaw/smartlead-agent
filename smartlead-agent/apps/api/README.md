# SmartLead Agent API

Week 1 backend foundation for SmartLead Agent, a production-style AI website assistant for small businesses.

This version includes a FastAPI app, SQLAlchemy models, SQLite persistence, Pydantic schemas, a deterministic mock LangGraph workflow, trace storage, lead storage, and tests. It intentionally does not use real LLM calls, real RAG, Google Sheets, email, Slack, auth, or a frontend.

## Install

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If your shell uses `python3` instead of `python`, use `python3 -m venv .venv`.

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

## Endpoints

- `GET /health`
- `POST /chat`
- `GET /conversations/{conversation_id}`
- `GET /agent-runs/{agent_run_id}/trace`
- `GET /leads`

## Example Requests

Health:

```bash
curl http://127.0.0.1:8000/health
```

Lead inquiry:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I need SEO for my gym. My budget is $2000 and I want to start next month."}'
```

Pricing question:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How much does SEO cost?"}'
```

Discount request:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Can you give me 70% discount and promise results?"}'
```

Conversation:

```bash
curl http://127.0.0.1:8000/conversations/{conversation_id}
```

Trace:

```bash
curl http://127.0.0.1:8000/agent-runs/{agent_run_id}/trace
```

Leads:

```bash
curl http://127.0.0.1:8000/leads
```

## Configuration

The app uses SQLite by default:

```text
sqlite:///./smartlead_agent.db
```

Set `DATABASE_URL` to point at another SQLAlchemy-supported database later, such as Postgres or Supabase.

## Mocked In Week 1

- Intent classification
- Lead extraction
- Response generation
- Document search
- Owner notification

## Week 2 Direction

- Replace mock document lookup with real RAG
- Ground FAQ and pricing responses in retrieved documents
- Add more realistic lead enrichment and qualification
- Prepare external integrations behind service boundaries
