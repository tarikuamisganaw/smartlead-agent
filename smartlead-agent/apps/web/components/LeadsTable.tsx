import type { ReactNode } from "react";
import Link from "next/link";
import StatusBadge from "@/components/StatusBadge";
import type { Lead } from "@/lib/types";
import { formatDateTime, formatMoney, shortId } from "@/lib/utils";

export default function LeadsTable({ leads }: { leads: Lead[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-line bg-white shadow-sm">
      <table className="min-w-[1040px] w-full border-collapse text-left text-sm">
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
