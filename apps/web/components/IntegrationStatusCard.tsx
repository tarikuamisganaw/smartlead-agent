import StatusBadge from "@/components/StatusBadge";
import type { IntegrationStatus } from "@/lib/types";
import { formatLabel } from "@/lib/utils";

export default function IntegrationStatusCard({ status }: { status: IntegrationStatus }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <section className="rounded-md border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-ink">Lead Sync</h2>
            <p className="mt-1 text-sm text-ink/60">{formatLabel(status.lead_sync.provider)}</p>
          </div>
          <StatusBadge
            value={status.lead_sync.configured ? "success" : "not_configured"}
            label={status.lead_sync.configured ? "Configured" : "Not Configured"}
          />
        </div>
        <dl className="mt-5 grid gap-3 text-sm">
          <Row label="Automatic Sync" value={status.lead_sync.automatic ? "Enabled" : "Disabled"} />
          <Row label="Complete Leads Only" value={status.lead_sync.sync_only_complete_leads ? "Yes" : "No"} />
          <Row
            label="Sheets Credentials"
            value={status.lead_sync.google_sheets.credentials_configured ? "Present" : "Missing"}
          />
          <Row
            label="Spreadsheet ID"
            value={status.lead_sync.google_sheets.spreadsheet_configured ? "Present" : "Missing"}
          />
          <Row label="Worksheet" value={status.lead_sync.google_sheets.worksheet_name} />
        </dl>
      </section>

      <section className="rounded-md border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-ink">Notifications</h2>
            <p className="mt-1 text-sm text-ink/60">{status.notification_providers.map(formatLabel).join(", ")}</p>
          </div>
          <StatusBadge
            value={status.notification.configured ? "success" : "not_configured"}
            label={status.notification.configured ? "Configured" : "Needs Config"}
          />
        </div>
        <dl className="mt-5 grid gap-3 text-sm">
          {status.notification_providers.map((provider) => (
            <Row
              key={provider}
              label={`${formatLabel(provider)} configured`}
              value={status.notification_configured[provider] ? "Yes" : "No"}
            />
          ))}
          <Row label="Email Provider" value={status.email_optional ? "Optional" : "Required"} />
          <Row label="Email Configured" value={status.notification_configured.email ? "Yes" : "No"} />
          <Row label="Owner Lead Notifications" value={status.send_owner_notifications ? "Enabled" : "Disabled"} />
          <Row label="Approval Notifications" value={status.send_approval_notifications ? "Enabled" : "Disabled"} />
          <Row
            label="Sync Failure Notifications"
            value={status.send_lead_sync_failure_notifications ? "Enabled" : "Disabled"}
          />
          <Row
            label="Customer Follow-up Emails"
            value={status.send_customer_followup_emails ? "Enabled" : "Disabled"}
          />
        </dl>
        <div className="mt-5 space-y-2 text-sm leading-6 text-ink/65">
          <p>Secrets are configured on the backend through environment variables. They are never shown here.</p>
          <p>
            Email is optional. Slack notifications are enough for this demo. Real email requires Resend and a verified
            sending domain.
          </p>
          {status.notification_providers.includes("slack") && !status.notification_configured.slack ? (
            <p className="text-accent">Slack provider is selected but SLACK_WEBHOOK_URL is missing.</p>
          ) : null}
          {status.notification_providers.includes("email") && !status.notification_configured.email ? (
            <p className="text-gold">Email selected but not configured. Notifications will continue through other providers.</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-line/70 pb-2 last:border-0 last:pb-0">
      <dt className="text-ink/55">{label}</dt>
      <dd className="font-medium text-ink">{value}</dd>
    </div>
  );
}
