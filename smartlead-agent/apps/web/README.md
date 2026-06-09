# SmartLead Agent Web

Next.js frontend for the local SmartLead Agent MVP.

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

## Run

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

## Build

```bash
npm run build
```

## What Is Included

- Chat UI connected to `POST /chat`
- Backend health status
- Example prompt buttons
- Conversation ID reuse across turns
- Agent run summary
- Lead info card
- Trace preview
- Dashboard overview
- Leads table
- Lead sync status and manual sync action for owners
- Conversations list and detail pages
- Full trace timeline page
- Read-only approvals queue
- Documents page with demo ingestion
- RAG search tester
- Eval dashboard with latest results and run button
- Integration status dashboard
- Guest chat state and signed-in chat history pages
- Login/register MVP pages

## Dashboard Pages

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
- `/chats`
- `/chats/[conversationId]`
- `/login`
- `/register`

## Demo Flow

1. Start the backend and frontend.
2. Open `http://localhost:3000`.
3. Send: `How much does SEO cost?`
4. Send: `I need SEO for my gym. My budget is $2000.`
5. Continue the same conversation with: `My name is Sara and my email is sara@example.com`
6. Send: `Can you give me 70% discount and promise results?`
7. Inspect the dashboard pages.

Google Sheets lead sync can be enabled from the backend `.env`. Slack/email notifications, CRM integrations, payments, and deployment are planned later. External notifications are still mocked.

Auth is an MVP localStorage bearer-token flow for portfolio/dev use. Production should use secure cookies or a managed auth provider.
