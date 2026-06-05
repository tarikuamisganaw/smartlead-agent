# SmartLead Agent Web

Next.js frontend foundation for SmartLead Agent.

## Install

```bash
cd apps/web
npm install
```

## Environment

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
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
- Dashboard placeholder
- Minimal leads, approvals, documents, trace, and RAG test pages

Full dashboard workflows come later.
