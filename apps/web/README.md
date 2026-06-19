# SmartLead Agent Web

Next.js frontend for SmartLead Agent, a production-style AI sales assistant for service businesses. The web app includes the customer chat experience, guest and signed-in conversation history, owner dashboards, lead management, trace inspection, document tooling, integration status, and eval visibility.

The frontend is designed as an operational product surface rather than a static demo: it connects to real API endpoints, handles auth-aware dashboard access, supports anonymous sessions, and exposes the observability screens needed to understand what the agent did.

## Product Surfaces

Customer-facing:

- Chat assistant connected to `POST /chat`.
- Guest session continuity through anonymous session tokens.
- Signed-in user chat history.
- Lead details surfaced after qualification.
- Safe handling for approval-required responses.

Owner/admin:

- Dashboard overview with key business and agent metrics.
- Lead table with quality, status, sync state, and manual sync actions.
- Conversation list and detail views.
- Agent trace timeline with tool calls and latency.
- Human approval queue.
- Documents page for demo ingestion and custom content upload.
- RAG tester for inspecting retrieved chunks.
- Integration status for lead sync and notification providers.
- Eval dashboard with latest results and run controls.

## Tech Stack

| Area | Implementation |
| --- | --- |
| Framework | Next.js 14 App Router |
| UI | React 18, TypeScript, Tailwind CSS |
| Data access | Typed API client in `lib/api.ts` |
| Auth state | Local bearer token for portfolio/dev flow |
| Guest state | Anonymous session token persisted in localStorage |
| Backend | FastAPI service at `NEXT_PUBLIC_API_URL` |

## Structure

```text
app/                         App Router pages
app/page.tsx                 Main chat experience
app/chats/                   Signed-in and guest conversation history
app/dashboard/               Owner dashboard sections
components/                  Reusable product UI components
lib/api.ts                   API client and auth token helpers
lib/types.ts                 Shared frontend response types
```

## Install

```bash
cd apps/web
cp .env.example .env.local
npm install
```

## Environment

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_ENABLED=true
```

## Run Locally

Start the backend first:

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then start the frontend:

```bash
cd apps/web
npm run dev
```

Local URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`

## Build And Lint

```bash
npm run build
npm run lint
```

## Routes

Customer and auth:

- `/`
- `/login`
- `/register`
- `/chats`
- `/chats/[conversationId]`

Owner dashboard:

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

## Demo Flow

1. Start the FastAPI backend and the Next.js frontend.
2. Open `http://localhost:3000`.
3. Ask: `How much does SEO cost?`
4. Continue: `I need SEO for my gym. My budget is $2000.`
5. Continue: `My name is Sara and my email is sara@example.com.`
6. Ask: `Can you give me 70% discount and promise results?`
7. Sign in as an owner and inspect the dashboard pages.

Expected result:

- RAG answers use the business knowledge base.
- One conversation persists across turns.
- One lead record is updated as more information arrives.
- Lead score and quality appear in the owner dashboard.
- Risky discount or guarantee requests create a pending approval.
- Trace pages show how the agent routed, retrieved, scored, and acted.

## API Integration

The API client in `lib/api.ts` centralizes:

- Chat requests
- Auth registration, login, and current user lookup
- Anonymous session creation and claiming
- Guest and signed-in conversation history
- Dashboard summary
- Lead list and manual sync
- Conversation and agent run detail
- Trace retrieval
- Approval list
- Document ingestion and upload
- RAG search
- Integration status
- Eval cases, latest results, and run trigger

Auth-enabled requests send:

- `Authorization: Bearer <token>` for signed-in users
- `X-Anonymous-Session-Token` for guest sessions

## Production Readiness Notes

Implemented:

- Typed API boundary for backend responses.
- Auth-aware owner dashboard access.
- Guest session continuity.
- Reusable loading, empty, error, table, badge, and dashboard components.
- Operational screens for traces, integrations, documents, evals, and lead sync.
- Build and lint scripts through Next.js.

Recommended before live production:

- Replace localStorage bearer tokens with secure cookies or managed auth.
- Add end-to-end tests for the core chat and owner dashboard flows.
- Add deployment-specific environment validation.
- Connect production monitoring and frontend error reporting.
- Complete visual QA across target browsers and devices.
