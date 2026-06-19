import type { ReactNode } from "react";
import StatusBadge from "@/components/StatusBadge";
import type { EvalCaseResult } from "@/lib/types";

const scoreLabels = [
  ["intent_correct", "Intent"],
  ["rag_usage_correct", "RAG"],
  ["lead_extraction_correct", "Lead"],
  ["approval_correct", "Approval"],
  ["tool_call_correct", "Tools"],
  ["valid_output", "Output"],
];

export default function EvalResultsTable({ results }: { results: EvalCaseResult[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-line bg-white shadow-sm">
      <table className="min-w-[980px] w-full border-collapse text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-ink/50">
          <tr>
            <Th>Case</Th>
            <Th>Status</Th>
            <Th>Scores</Th>
            <Th>Latency</Th>
            <Th>Errors</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {results.map((result) => (
            <tr key={result.case_id} className="align-top">
              <Td><span className="font-semibold text-ink">{result.case_id}</span></Td>
              <Td><StatusBadge value={result.passed ? "success" : "failed"} label={result.passed ? "Passed" : "Failed"} /></Td>
              <Td>
                <div className="flex flex-wrap gap-2">
                  {scoreLabels.map(([key, label]) => (
                    <StatusBadge
                      key={key}
                      value={Boolean(result.scores[key])}
                      label={`${label}: ${result.scores[key] ? "OK" : "Fail"}`}
                    />
                  ))}
                </div>
              </Td>
              <Td>{result.latency_ms}ms</Td>
              <Td>
                {result.errors.length ? (
                  <ul className="grid gap-1">
                    {result.errors.map((error) => (
                      <li key={error} className="text-accent">{error}</li>
                    ))}
                  </ul>
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
