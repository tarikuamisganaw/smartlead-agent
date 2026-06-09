import StatCard from "@/components/StatCard";
import type { EvalRunResults } from "@/lib/types";

export default function EvalSummaryCards({ results }: { results: EvalRunResults }) {
  const metrics = results.metrics;

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard label="Total cases" value={results.total_cases} detail={`${results.passed_cases} passed`} />
      <StatCard label="Pass rate" value={formatPercent(results.pass_rate)} detail={`${results.provider} · ${results.model || "unknown model"}`} />
      <StatCard label="Intent accuracy" value={formatPercent(metrics.intent_correct)} detail={`RAG ${formatPercent(metrics.rag_usage_correct)}`} />
      <StatCard label="Lead accuracy" value={formatPercent(metrics.lead_extraction_correct)} detail={`Approval ${formatPercent(metrics.approval_correct)}`} />
      <StatCard label="Tool accuracy" value={formatPercent(metrics.tool_call_correct)} detail={`Valid output ${formatPercent(metrics.valid_output)}`} />
      <StatCard label="Avg latency" value={`${metrics.average_latency_ms}ms`} detail="Per eval case" />
      <StatCard label="Estimated cost" value={String(metrics.estimated_cost)} detail="Uses configured placeholder rates" />
      <StatCard label="Failed cases" value={results.total_cases - results.passed_cases} detail="Review table below" />
    </section>
  );
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}
