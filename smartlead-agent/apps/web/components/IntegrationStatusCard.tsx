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
          <StatusBadge value={status.lead_sync.configured} label={status.lead_sync.configured ? "Configured" : "Not Configured"} />
        </div>
        <dl className="mt-5 grid gap-3 text-sm">
          <Row label="Automatic Sync" value={status.lead_sync.automatic ? "Enabled" : "Disabled"} />
          <Row label="Complete Leads Only" value={status.lead_sync.sync_only_complete_leads ? "Yes" : "No"} />
          <Row label="Sheets Credentials" value={status.lead_sync.google_sheets.credentials_configured ? "Present" : "Missing"} />
          <Row label="Spreadsheet ID" value={status.lead_sync.google_sheets.spreadsheet_configured ? "Present" : "Missing"} />
          <Row label="Worksheet" value={status.lead_sync.google_sheets.worksheet_name} />
        </dl>
      </section>

      <section className="rounded-md border border-line bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-ink">Notifications</h2>
            <p className="mt-1 text-sm text-ink/60">{formatLabel(status.notification.provider)}</p>
          </div>
          <StatusBadge value={status.notification.configured} label={status.notification.configured ? "Configured" : "Mock / Reserved"} />
        </div>
        <p className="mt-5 text-sm leading-6 text-ink/65">
          Slack and email providers are represented here for future setup. Week 4C keeps real notifications disabled unless a provider is explicitly implemented later.
        </p>
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
