import type { ReactNode } from "react";
import Link from "next/link";
import LeadSyncStatusBadge from "@/components/LeadSyncStatusBadge";
import StatusBadge from "@/components/StatusBadge";
import type { Lead } from "@/lib/types";
import { cx, formatDateTime, formatMoney, shortId } from "@/lib/utils";

type LeadsTableProps = {
  leads: Lead[];
  syncingLeadId?: string | null;
  onSync?: (leadId: string) => void;
};

export default function LeadsTable({ leads, syncingLeadId, onSync }: LeadsTableProps) {
  return (
    <div className="overflow-x-auto rounded-md border border-line bg-white shadow-sm">
      <table className="min-w-[1320px] w-full border-collapse text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-ink/50">
          <tr>
            <Th>Lead</Th>
            <Th>Email</Th>
            <Th>Phone</Th>
            <Th>Business</Th>
            <Th>Service</Th>
            <Th>Budget</Th>
            <Th>Timeline</Th>
            <Th>Score</Th>
            <Th>Status</Th>
            <Th>Sync</Th>
            <Th>Provider</Th>
            <Th>Synced At</Th>
            <Th>Sync Action</Th>
            <Th>Created</Th>
            <Th>Conversation</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {leads.map((lead) => (
            <tr key={lead.id} className="align-top">
              <Td>{lead.name || "Unnamed lead"}</Td>
              <Td>{lead.email || "—"}</Td>
              <Td>{lead.phone || "—"}</Td>
              <Td>{lead.business_type || "—"}</Td>
              <Td>{lead.service_interest || "—"}</Td>
              <Td>{formatMoney(lead.budget)}</Td>
              <Td>{lead.timeline || "—"}</Td>
              <Td>
                <div className="flex flex-wrap gap-2">
                  {lead.lead_score !== null && lead.lead_score !== undefined ? (
                    <StatusBadge value={String(lead.lead_score)} label={`Score ${lead.lead_score}`} />
                  ) : null}
                  {lead.lead_quality ? <StatusBadge value={lead.lead_quality} /> : null}
                </div>
              </Td>
              <Td>{lead.status ? <StatusBadge value={lead.status} /> : "—"}</Td>
              <Td>
                <div className="space-y-1">
                  <LeadSyncStatusBadge status={lead.external_sync_status} />
                  {lead.external_sync_error ? <p className="max-w-[220px] text-xs text-accent">{lead.external_sync_error}</p> : null}
                </div>
              </Td>
              <Td>{lead.external_sync_provider || "—"}</Td>
              <Td>{formatDateTime(lead.external_synced_at)}</Td>
              <Td>
                {onSync ? (
                  <button
                    className={cx(
                      "h-9 rounded-md border border-line px-3 text-xs font-semibold transition",
                      syncingLeadId === lead.id ? "cursor-wait bg-panel text-ink/45" : "bg-white text-ink hover:border-brand hover:text-brand",
                    )}
                    disabled={syncingLeadId === lead.id}
                    type="button"
                    onClick={() => onSync(lead.id)}
                  >
                    {syncingLeadId === lead.id ? "Syncing" : "Sync"}
                  </button>
                ) : (
                  "—"
                )}
              </Td>
              <Td>{formatDateTime(lead.created_at)}</Td>
              <Td>
                {lead.conversation_id ? (
                  <Link className="text-brand hover:underline" href={`/dashboard/conversations/${lead.conversation_id}`}>
                    {shortId(lead.conversation_id)}
                  </Link>
                ) : (
                  "—"
                )}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: ReactNode }) {
  return <th className="px-4 py-3 font-semibold">{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return <td className="px-4 py-3 text-ink/75">{children}</td>;
}
