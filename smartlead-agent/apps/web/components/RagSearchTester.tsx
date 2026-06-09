"use client";

import { FormEvent, useState } from "react";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import { searchRag } from "@/lib/api";
import type { RagResult } from "@/lib/types";

const examples = [
  "How much does SEO cost?",
  "What happens after a lead is captured?",
  "Do you offer website design?",
  "What is the refund policy?",
  "Show me gym SEO case studies",
];

export default function RagSearchTester() {
  const [query, setQuery] = useState("How much does SEO cost?");
  const [topK, setTopK] = useState(4);
  const [results, setResults] = useState<RagResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(nextQuery = query) {
    const trimmed = nextQuery.trim();
    if (!trimmed) {
      return;
    }

    setQuery(nextQuery);
    setSearched(true);
    setLoading(true);
    setError(null);
    try {
      const response = await searchRag(trimmed, topK);
      setResults(response.results);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "RAG search failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch();
  }

  return (
    <div className="space-y-5">
      <section className="rounded-md border border-line bg-white p-4 shadow-sm">
        <form onSubmit={handleSubmit} className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_120px_auto]">
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase text-ink/45">Query</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="min-h-11 rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
            />
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase text-ink/45">Top K</span>
            <input
              type="number"
              min={1}
              max={10}
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
              className="min-h-11 rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
            />
          </label>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="self-end rounded-md bg-brand px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-ink/25"
          >
            Search
          </button>
        </form>
        <div className="mt-4 flex flex-wrap gap-2">
          {examples.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => void runSearch(example)}
              className="rounded-md border border-line bg-panel px-3 py-1.5 text-xs font-medium text-ink transition hover:border-brand hover:text-brand"
            >
              {example}
            </button>
          ))}
        </div>
      </section>

      {loading ? <LoadingState label="Searching document chunks..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading && searched && !results.length ? (
        <EmptyState title="No chunks matched." message="Try ingesting demo documents or searching with a business term like SEO, pricing, refund, onboarding, or case studies." />
      ) : null}

      <div className="grid gap-3">
        {results.map((result) => (
          <article key={result.chunk_id} className="rounded-md border border-line bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-sm font-semibold text-ink">{result.title}</h2>
                <p className="mt-1 break-all text-xs text-ink/50">{result.source}</p>
              </div>
              <span className="rounded-md border border-brand/25 bg-brand/10 px-2.5 py-1 text-xs font-semibold text-brand">
                Score {result.score}
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-ink/70">{result.content}</p>
            <p className="mt-3 break-all text-xs text-ink/45">Chunk {result.chunk_id}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
