import StatusBadge from "@/components/StatusBadge";
import type { TraceEvent } from "@/lib/types";

export default function TraceTimeline({ trace }: { trace: TraceEvent[] }) {
  const sortedTrace = [...trace].sort((a, b) => (a.step_number ?? 0) - (b.step_number ?? 0));

  return (
    <div className="space-y-3">
      {sortedTrace.map((event, index) => (
        <article key={event.id || `${event.node_name}-${index}`} className="rounded-md border border-line bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="flex h-7 min-w-7 items-center justify-center rounded-md bg-panel px-2 text-xs font-semibold text-ink/70">
                {event.step_number ?? index + 1}
              </span>
              <div>
                <h2 className="text-sm font-semibold text-ink">{event.agent_name || "Agent"}</h2>
                <p className="text-xs text-ink/50">{event.node_name || "node"}</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {event.status ? <StatusBadge value={event.status} /> : null}
              {event.tool_name ? <StatusBadge value="pending" label={event.tool_name} /> : null}
              {event.latency_ms !== null && event.latency_ms !== undefined ? (
                <span className="text-xs font-medium text-ink/50">{event.latency_ms}ms</span>
              ) : null}
            </div>
          </div>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <Info label="Input" value={event.input_summary} />
            <Info label="Output" value={event.output_summary} />
          </dl>
          {event.error_message ? (
            <div className="mt-3 rounded-md border border-accent/30 bg-accent/10 p-3 text-sm text-accent">
              {event.error_message}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase text-ink/45">{label}</dt>
      <dd className="mt-1 leading-6 text-ink/70">{value || "—"}</dd>
    </div>
  );
}
