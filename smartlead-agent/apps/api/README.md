# SmartLead Agent API

Backend foundation for SmartLead Agent, a production-style AI website assistant for small businesses.

Week 4A keeps mock mode for deterministic local development and tests, includes optional Gemini LLM provider support, exposes dashboard-friendly read endpoints, and adds an evaluation suite with latency/cost tracking. It still does not include auth, real email/Slack, Google Sheets, CRM, or real notifications.

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
- `GET /approvals`
- `POST /documents/ingest-demo`
- `GET /documents`
- `POST /rag/search`
- `GET /evals/cases`
- `GET /evals/latest`
- `POST /evals/run`

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

## Configuration

The app uses SQLite by default:

```text
sqlite:///./smartlead_agent.db
```

Set `DATABASE_URL` to point at another SQLAlchemy-supported database later, such as Postgres or Supabase.

## Still Mocked

- Owner notification
- Follow-up draft sending
- Slack, email, Google Sheets, and CRM integrations

The RAG retrieval is real and local. Intent classification, lead extraction, and response generation are mocked in `MODEL_PROVIDER=mock` and Gemini-backed in `MODEL_PROVIDER=gemini`.
