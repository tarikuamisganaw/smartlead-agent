"use client";

import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import EvalResultsTable from "@/components/EvalResultsTable";
import EvalSummaryCards from "@/components/EvalSummaryCards";
import LoadingState from "@/components/LoadingState";
import { getEvalCases, getLatestEvalResults, runEvals } from "@/lib/api";
import type { EvalCase, EvalRunResults, LatestEvalResponse } from "@/lib/types";

export default function EvalsPage() {
  const [cases, setCases] = useState<EvalCase[]>([]);
  const [latest, setLatest] = useState<LatestEvalResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getEvalCases(), getLatestEvalResults()])
      .then(([caseResponse, latestResponse]) => {
        setCases(caseResponse.cases);
        setLatest(latestResponse);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load eval data."))
      .finally(() => setLoading(false));
  }, []);

  const evalResults = useMemo(() => {
    if (!latest || "status" in latest) {
      return null;
    }
    return latest as EvalRunResults;
  }, [latest]);

  async function handleRunEvals() {
    setRunning(true);
    setError(null);
    try {
      const results = await runEvals();
      setLatest(results);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not run evals.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <DashboardLayout
      title="Evals"
      subtitle="Deterministic mock-mode checks for routing, RAG, lead extraction, approval decisions, tool calls, latency, and cost."
      actions={
        <button
          type="button"
          onClick={handleRunEvals}
          disabled={running}
          className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-ink/25"
        >
          {running ? "Running evals..." : "Run latest eval"}
        </button>
      }
    >
      <div className="space-y-5">
        <section className="rounded-md border border-line bg-panel px-4 py-3 text-sm leading-6 text-ink/65">
          {cases.length} eval cases are loaded from the backend. Gemini evals may vary and can consume quota; normal local tests use mock mode.
        </section>
        {loading ? <LoadingState label="Loading eval dashboard..." /> : null}
        {running ? <LoadingState label="Running eval cases..." /> : null}
        {error ? <ErrorState message={error} /> : null}

        {!loading && !evalResults ? (
          <EmptyState
            title="No eval run results yet."
            message="Run the eval suite to generate latest_eval_results.json and inspect pass rates."
          />
        ) : null}

        {evalResults ? (
          <>
            <EvalSummaryCards results={evalResults} />
            <EvalResultsTable results={evalResults.results} />
          </>
        ) : null}
      </div>
    </DashboardLayout>
  );
}
