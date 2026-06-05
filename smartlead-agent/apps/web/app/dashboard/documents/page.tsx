"use client";

import { useEffect, useState } from "react";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import { getDocuments, ingestDemoDocuments } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDocuments() {
    setLoading(true);
    setError(null);
    try {
      const body = await getDocuments();
      setDocuments(body.documents);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load documents.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function handleIngest() {
    setBusy(true);
    setError(null);
    try {
      await ingestDemoDocuments();
      await loadDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not ingest documents.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-5">
          <h1 className="text-3xl font-semibold text-ink">Documents</h1>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleIngest}
              disabled={busy}
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white disabled:bg-ink/25"
            >
              Ingest demo docs
            </button>
            <a className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/dashboard">
              Dashboard
            </a>
          </div>
        </div>
        {loading ? <LoadingState label="Loading documents..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        <div className="grid gap-3">
          {documents.map((document) => (
            <article key={document.id} className="rounded-md border border-line bg-white p-4">
              <h2 className="font-semibold text-ink">{document.title}</h2>
              <p className="mt-1 break-all text-sm text-ink/60">{document.source}</p>
              <p className="mt-3 text-sm text-ink/70">{document.chunk_count} chunk(s)</p>
            </article>
          ))}
          {!loading && !documents.length ? <p className="text-sm text-ink/60">No documents ingested yet.</p> : null}
        </div>
      </div>
    </main>
  );
}
