"use client";

import { FormEvent, useState } from "react";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import { searchRag } from "@/lib/api";
import type { RagResult } from "@/lib/types";

export default function RagTestPage() {
  const [query, setQuery] = useState("How much does SEO cost?");
  const [results, setResults] = useState<RagResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await searchRag(query, 4);
      setResults(response.results);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "RAG search failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-5">
          <h1 className="text-3xl font-semibold text-ink">RAG Test</h1>
          <a className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/dashboard">
            Dashboard
          </a>
        </div>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="min-h-11 flex-1 rounded-md border border-line px-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          <button className="rounded-md bg-brand px-5 text-sm font-semibold text-white" type="submit">
            Search
          </button>
        </form>
        <div className="mt-5 space-y-3">
          {loading ? <LoadingState label="Searching documents..." /> : null}
          {error ? <ErrorState message={error} /> : null}
          {results.map((result) => (
            <article key={result.chunk_id} className="rounded-md border border-line bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-ink">{result.title}</h2>
                <span className="text-xs font-semibold text-brand">Score {result.score}</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-ink/70">{result.content}</p>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
