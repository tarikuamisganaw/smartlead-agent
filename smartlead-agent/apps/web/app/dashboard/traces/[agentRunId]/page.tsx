"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import StatusBadge from "@/components/StatusBadge";
import TraceTimeline from "@/components/TraceTimeline";
import { getAgentTrace } from "@/lib/api";
import type { AgentTraceResponse } from "@/lib/types";
import { formatDateTime, shortId } from "@/lib/utils";

export default function TraceDetailPage({ params }: { params: { agentRunId: string } }) {
  const [trace, setTrace] = useState<AgentTraceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAgentTrace(params.agentRunId)
      .then(setTrace)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load trace."))
      .finally(() => setLoading(false));
  }, [params.agentRunId]);

  return (
    <DashboardLayout
      title="Agent Trace"
      subtitle={`Run ${params.agentRunId}`}
      actions={
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/dashboard/conversations">
          Conversations
        </Link>
      }
    >
      <div className="space-y-5">
        <p className="rounded-md border border-line bg-panel px-4 py-3 text-sm leading-6 text-ink/65">
          Tracing shows the workflow path the agent followed, including nodes, tool calls, outputs, errors, and latency.
        </p>
        {loading ? <LoadingState label="Loading trace..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {trace ? (
          <>
            {trace.trace.length ? <TraceTimeline trace={trace.trace} /> : <EmptyState title="No trace events recorded." />}

            <section className="rounded-md border border-line bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-ink">Tool Calls</h2>
              <div className="mt-3 divide-y divide-line">
                {(trace.tool_calls || []).map((toolCall) => (
                  <div key={toolCall.id} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-ink">{toolCall.tool_name}</span>
                      <StatusBadge value={toolCall.status} />
                      {toolCall.latency_ms !== null && toolCall.latency_ms !== undefined ? (
                        <span className="text-xs text-ink/50">{toolCall.latency_ms}ms</span>
                      ) : null}
                      <span className="text-xs text-ink/45">{formatDateTime(toolCall.created_at)}</span>
                    </div>
                    <p className="mt-2 text-xs text-ink/45">Tool call {shortId(toolCall.id)}</p>
                    <div className="mt-3 grid gap-3 lg:grid-cols-2">
                      <pre className="max-h-64 overflow-auto rounded-md bg-panel p-3 text-xs leading-5 text-ink/70">
                        {JSON.stringify(toolCall.tool_input, null, 2)}
                      </pre>
                      <pre className="max-h-64 overflow-auto rounded-md bg-panel p-3 text-xs leading-5 text-ink/70">
                        {JSON.stringify(toolCall.tool_output, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
                {!trace.tool_calls?.length ? <EmptyState title="No tool calls recorded." /> : null}
              </div>
            </section>
          </>
        ) : null}
      </div>
    </DashboardLayout>
  );
}
