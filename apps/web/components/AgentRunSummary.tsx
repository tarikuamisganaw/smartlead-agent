import type { ChatResponse } from "@/lib/types";
import { asNumber } from "@/lib/utils";
import StatusBadge from "@/components/StatusBadge";

export default function AgentRunSummary({ response }: { response: ChatResponse }) {
  const leadScore = asNumber(response.lead_info?.lead_score);
  const leadQuality = typeof response.lead_info?.lead_quality === "string" ? response.lead_info.lead_quality : null;

  return (
    <section className="grid gap-3 rounded-md border border-line bg-panel p-4 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <div className="text-xs font-medium uppercase text-ink/50">Intent</div>
        <div className="mt-1 text-sm font-semibold text-ink">{response.intent}</div>
      </div>
      <div>
        <div className="text-xs font-medium uppercase text-ink/50">Approval</div>
        <div className="mt-1">
          <StatusBadge value={response.requires_human_approval} />
        </div>
      </div>
      <div>
        <div className="text-xs font-medium uppercase text-ink/50">Lead</div>
        <div className="mt-1 flex flex-wrap gap-2">
          {leadScore !== null ? <StatusBadge value={`${leadScore}`} label={`Score ${leadScore}`} /> : null}
          {leadQuality ? <StatusBadge value={leadQuality} /> : null}
          {leadScore === null && !leadQuality ? <span className="text-sm text-ink/50">No score</span> : null}
        </div>
      </div>
      <div>
        <div className="text-xs font-medium uppercase text-ink/50">Agent Run</div>
        <div className="mt-1 break-all text-xs font-medium text-ink">{response.agent_run_id}</div>
      </div>
    </section>
  );
}
