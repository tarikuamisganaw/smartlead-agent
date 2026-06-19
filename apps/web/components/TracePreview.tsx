import type { TraceEvent } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";

export default function TracePreview({ trace }: { trace: TraceEvent[] }) {
  if (!trace.length) {
    return null;
  }

  return (
    <section className="rounded-md border border-line bg-white p-4">
      <h2 className="text-sm font-semibold text-ink">Trace Preview</h2>
      <div className="mt-3 divide-y divide-line">
        {trace.slice(-5).map((event, index) => (
          <div key={`${event.node_name}-${event.step_number ?? index}`} className="py-3 first:pt-0 last:pb-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-ink">{event.agent_name || "Agent"}</span>
              <span className="text-xs text-ink/50">{event.node_name}</span>
              {event.status ? <StatusBadge value={event.status} /> : null}
              {event.tool_name ? <StatusBadge value="pending" label={event.tool_name} /> : null}
              {event.latency_ms !== null && event.latency_ms !== undefined ? (
                <span className="text-xs text-ink/50">{event.latency_ms}ms</span>
              ) : null}
            </div>
            {event.output_summary ? <p className="mt-2 text-sm leading-6 text-ink/70">{event.output_summary}</p> : null}
          </div>
        ))}
      </div>
    </section>
  );
}
