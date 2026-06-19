# Free Deployment Guide

This guide deploys SmartLead Agent with:

- Supabase/Postgres for the database
- Hugging Face Spaces for the FastAPI backend
- Vercel for the Next.js frontend

The backend container is stateless. Do not commit `.env` files or service credentials. Configure production values in the hosting dashboards.

## 1. Prepare Supabase

Use the Supabase Postgres connection string that already works locally.

Recommended production-style API values:

```env
DATABASE_URL=postgresql+psycopg://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:6543/postgres?sslmode=require
ENVIRONMENT=production
RAG_PROVIDER=local
RAG_FALLBACK_TO_LOCAL=true
```

Use `RAG_PROVIDER=local` for the simplest free deployment. It still stores documents and chunks in Supabase, then builds the local retrieval index in the API process. Use `RAG_PROVIDER=supabase` only if `pgvector` is enabled and your embedding provider is configured.

If using vector RAG, enable `pgvector` in Supabase:

```sql
create extension if not exists vector;
```

## 2. Deploy The Backend On Hugging Face Spaces

1. Create a new Hugging Face Space.
2. Select `Docker` as the Space SDK.
3. Choose public visibility for a recruiter demo.
4. Push this repository to the Space, or connect/import it from GitHub.
5. Make sure the Space repository has the root `Dockerfile`.
6. If Hugging Face does not detect Docker automatically, copy the YAML block from `deploy/huggingface/README.md` to the top of the Space repository `README.md`.

Set these Hugging Face Space Variables:

```env
ENVIRONMENT=production
FRONTEND_URL=https://YOUR_VERCEL_APP.vercel.app
CORS_ORIGINS=https://YOUR_VERCEL_APP.vercel.app
AUTH_ENABLED=true
MODEL_PROVIDER=mock
RAG_PROVIDER=local
RAG_FALLBACK_TO_LOCAL=true
LEAD_SYNC_PROVIDER=mock
NOTIFICATION_PROVIDERS=mock
SYNC_LEADS_AUTOMATICALLY=true
SEND_CUSTOMER_FOLLOWUP_EMAILS=false
```

Set these Hugging Face Space Secrets:

```env
DATABASE_URL=your_supabase_database_url
JWT_SECRET_KEY=generate-a-long-random-secret
```

Optional secrets:

```env
GEMINI_API_KEY=your_key_if_using_MODEL_PROVIDER_gemini
SLACK_WEBHOOK_URL=your_webhook_if_using_slack_notifications
RESEND_API_KEY=your_key_if_using_email_notifications
OWNER_EMAIL=owner@example.com
FROM_EMAIL=SmartLead <noreply@yourdomain.com>
GOOGLE_SHEETS_CREDENTIALS_JSON=single-line-service-account-json
GOOGLE_SHEETS_SPREADSHEET_ID=your_sheet_id
```

After the Space builds, test:

```text
https://YOUR_SPACE.hf.space/health
https://YOUR_SPACE.hf.space/ready
https://YOUR_SPACE.hf.space/docs
```

If `/ready` reports `rag_ready=false`, open the frontend as an owner and ingest demo documents from `/dashboard/documents`, or call:

```bash
curl -X POST https://YOUR_SPACE.hf.space/documents/ingest-demo \
  -H "Authorization: Bearer YOUR_OWNER_TOKEN"
```

## 3. Deploy The Frontend On Vercel

1. Import the GitHub repository into Vercel.
2. Set the Vercel project root directory to:

```text
apps/web
```

3. Use these build settings:

```text
Framework Preset: Next.js
Install Command: npm install
Build Command: npm run build
Output Directory: Next.js default
```

4. Set these Vercel environment variables:

```env
NEXT_PUBLIC_API_URL=https://YOUR_SPACE.hf.space
NEXT_PUBLIC_AUTH_ENABLED=true
```

5. Deploy the frontend.

## 4. Connect Frontend And Backend

After Vercel gives you the final frontend URL, return to Hugging Face and update:

```env
FRONTEND_URL=https://YOUR_VERCEL_APP.vercel.app
CORS_ORIGINS=https://YOUR_VERCEL_APP.vercel.app
```

Restart the Hugging Face Space after changing those values.

## 5. Create The Demo Owner

Register from the deployed `/register` page and enable `as_owner`, or call the API:

```bash
curl -X POST https://YOUR_SPACE.hf.space/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"password123","full_name":"Owner","as_owner":true}'
```

Use a stronger password for any public demo you plan to leave online.

## 6. Demo Checklist

1. Open the Vercel URL.
2. Register or log in as owner.
3. Open `/dashboard/documents`.
4. Ingest demo documents.
5. Return to `/`.
6. Ask: `How much does SEO cost?`
7. Ask: `I need SEO for my gym. My budget is $2000. My email is sara@example.com.`
8. Ask: `Can you give me 70% discount and promise results?`
9. Review `/dashboard/leads`, `/dashboard/approvals`, and `/dashboard/integrations`.

## Free Hosting Notes

- Hugging Face free Spaces can sleep when unused. First load may be slow.
- Supabase free projects can have limits and may pause depending on plan rules. Keep traffic low for a recruiter demo.
- Vercel Hobby is suitable for personal portfolio projects, but watch usage limits.
- Use mock providers for lead sync and notifications unless you really need Google Sheets or Slack in the demo.
