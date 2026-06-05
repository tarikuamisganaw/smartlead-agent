"use client";

import { useEffect, useState } from "react";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import StatusBadge from "@/components/StatusBadge";
import TracePreview from "@/components/TracePreview";
import { getAgentTrace } from "@/lib/api";
import type { AgentTraceResponse } from "@/lib/types";

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
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-5">
          <div>
            <h1 className="text-3xl font-semibold text-ink">Agent Trace</h1>
            <p className="mt-2 break-all text-sm text-ink/60">{params.agentRunId}</p>
          </div>
          <a className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/dashboard">
            Dashboard
          </a>
        </div>
        {loading ? <LoadingState label="Loading trace..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {trace ? (
          <div className="space-y-4">
            <TracePreview trace={trace.trace} />
            <section className="rounded-md border border-line bg-white p-4">
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
                    </div>
                    <pre className="mt-2 max-h-44 overflow-auto rounded-md bg-panel p-3 text-xs text-ink/70">
                      {JSON.stringify(toolCall.tool_output, null, 2)}
                    </pre>
                  </div>
                ))}
                {!trace.tool_calls?.length ? <p className="text-sm text-ink/60">No tool calls recorded.</p> : null}
              </div>
            </section>
          </div>
        ) : null}
      </div>
    </main>
  );
}
