# SmartLead Agent API

Backend foundation for SmartLead Agent, a production-style AI website assistant for small businesses.

Week 2 keeps the app local and keyless while adding real document ingestion, local RAG, conversation memory, lead update behavior, tool-call logging, and stronger tests. It still does not include a frontend, auth, real email/Slack, Google Sheets, or paid LLM calls.

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

## Endpoints

- `GET /health`
- `POST /chat`
- `GET /conversations/{conversation_id}`
- `GET /agent-runs/{agent_run_id}/trace`
- `GET /leads`
- `GET /approvals`
- `POST /documents/ingest-demo`
- `GET /documents`
- `POST /rag/search`

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

Trace and tool calls:

```bash
curl http://localhost:8000/agent-runs/{agent_run_id}/trace
```

Leads:

```bash
curl http://localhost:8000/leads
```

Approvals:

```bash
curl http://localhost:8000/approvals
```

## How Local RAG Works

Markdown files from `data/demo_business` are loaded into `Document` records, split into `DocumentChunk` records, and searched locally. The preferred path uses `sklearn` TF-IDF and cosine similarity. A pure-Python TF-IDF-style fallback is included so the app still runs without external API keys.

If `/chat` needs RAG and no chunks exist yet, demo docs are auto-ingested.

## Conversation Memory

Each `/chat` call saves the user message, runs the graph, saves the assistant response, and persists trace events. Existing lead data for the conversation is loaded into `AgentState`, so a second turn can update the same lead instead of creating a duplicate.

## Configuration

The app uses SQLite by default:

```text
sqlite:///./smartlead_agent.db
```

Set `DATABASE_URL` to point at another SQLAlchemy-supported database later, such as Postgres or Supabase.

## Still Mocked

- Intent classification
- Lead extraction
- Response generation
- Owner notification
- Follow-up draft sending

The RAG retrieval is real and local, but no real LLM provider is called.
