import Link from "next/link";
import StatusBadge from "@/components/StatusBadge";
import type { Approval } from "@/lib/types";
import { formatDateTime, shortId } from "@/lib/utils";

export default function ApprovalList({ approvals }: { approvals: Approval[] }) {
  return (
    <div className="grid gap-3">
      {approvals.map((approval) => (
        <article key={approval.id} className="rounded-md border border-line bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-ink">{approval.action_type}</h2>
              <p className="mt-1 text-xs text-ink/50">{formatDateTime(approval.created_at)}</p>
            </div>
            <StatusBadge value={approval.status} />
          </div>
          <p className="mt-3 text-sm leading-6 text-ink/70">{approval.reason}</p>
          {approval.draft_response ? <p className="mt-3 text-sm leading-6 text-ink/60">{approval.draft_response}</p> : null}
          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            <span className="text-ink/50">Approval {shortId(approval.id)}</span>
            <Link className="text-brand hover:underline" href={`/dashboard/traces/${approval.agent_run_id}`}>
              View trace
            </Link>
          </div>
        </article>
      ))}
    </div>
  );
}
