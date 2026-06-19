# SmartLead Agent Demo Checklist

Use this checklist for a local owner/admin demo.

## 1. Start Backend

```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt
python -m app.scripts.ingest_demo_docs
uvicorn app.main:app --reload
```

Check:

```bash
curl http://localhost:8000/health
```

## 2. Start Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open the printed local URL.

## 3. Owner Account

Register an owner from the UI or API:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"password123","full_name":"Owner","as_owner":true}'
```

Owner-only pages:

- `/dashboard`
- `/dashboard/leads`
- `/dashboard/approvals`
- `/dashboard/documents`
- `/dashboard/integrations`
- `/dashboard/evals`

## 4. Chat Flow

Try:

```text
I need SEO for my gym. My budget is $2000.
```

Then continue the same chat:

```text
My name is Sara and my email is sara@example.com
```

Expected:

- One conversation
- One lead updated across turns
- Lead score improves when email/name arrive
- Owner dashboard shows the lead

## 5. RAG Flow

From `/dashboard/documents`, upload a `.md` or `.txt` document with a unique package or price.

Ask chat:

```text
How much is the dental clinic launch package?
```

Expected:

- RAG retrieves the uploaded document
- The answer uses the uploaded document, not only demo pricing

## 6. Google Sheets Sync

In `apps/api/.env`, set:

```env
LEAD_SYNC_PROVIDER=google_sheets
GOOGLE_SHEETS_CREDENTIALS_JSON={...single-line service account JSON...}
GOOGLE_SHEETS_SPREADSHEET_ID=...
GOOGLE_SHEETS_WORKSHEET_NAME=Leads
```

Share the Google Sheet with the service-account email as Editor.

Restart FastAPI, open `/dashboard/integrations`, and confirm lead sync is configured.

Create or open a lead from `/dashboard/leads`, then press `Sync`.

Expected:

- Lead status becomes `synced`
- Google Sheet gets a `Leads` worksheet if missing
- Lead row appears or updates in the sheet

## 7. Approval Flow

Ask:

```text
Can you give me 70% discount and promise results?
```

Expected:

- Chat says the team must review it
- `/dashboard/approvals` shows a pending approval
- The assistant does not approve discounts or guarantee results

## 8. Mock Notification Demo

In `apps/api/.env`, set:

```env
NOTIFICATION_PROVIDERS=mock
SEND_OWNER_NOTIFICATIONS=true
```

Restart FastAPI, then submit:

```text
My name is Sara and my email is sara@example.com. I need SEO for my gym. My budget is $3000 and I want to start next week.
```

Expected:

- Chat succeeds
- `/dashboard/traces/{agentRunId}` shows `notify_owner_mock`
- No external service is called

## 9. Slack Notification Demo

Set:

```env
NOTIFICATION_PROVIDERS=slack
SLACK_WEBHOOK_URL=...
```

Restart FastAPI and submit a warm/hot lead.

Expected:

- Slack receives a SmartLead message
- Trace/tool calls show `notify_owner_slack`
- If the webhook is missing, chat still succeeds and the tool call is marked failed

## 10. Email Notification Demo

Email is optional. Skip this step unless you want to test Resend with a verified sending domain or approved test sender.

Set:

```env
NOTIFICATION_PROVIDERS=slack,email
RESEND_API_KEY=...
OWNER_EMAIL=owner@example.com
FROM_EMAIL=SmartLead <noreply@yourdomain.com>
OWNER_NAME=Business Owner
```

Restart FastAPI and submit a warm/hot lead.

Expected:

- Owner email receives the notification
- Trace/tool calls show `notify_owner_email`
- Customer follow-up emails are not sent while `SEND_CUSTOMER_FOLLOWUP_EMAILS=false`

## 11. Approval Notification Demo

Set:

```env
NOTIFICATION_PROVIDERS=mock
SEND_APPROVAL_NOTIFICATIONS=true
```

Ask:

```text
Can you give me 70% discount and promise results?
```

Expected:

- Pending approval is created
- Trace/tool calls show `notify_approval_mock`
