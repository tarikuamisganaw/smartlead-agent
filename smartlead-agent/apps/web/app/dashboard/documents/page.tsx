"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import DocumentsTable from "@/components/DocumentsTable";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import { getDocuments, ingestDemoDocuments } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ingestResult, setIngestResult] = useState<string | null>(null);

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
    setIngestResult(null);
    try {
      const result = await ingestDemoDocuments();
      setIngestResult(`${result.documents_ingested} documents ingested, ${result.chunks_created} chunks created.`);
      await loadDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not ingest documents.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <DashboardLayout
      title="Documents"
      subtitle="Business markdown files stored in SQLite and chunked for local RAG retrieval."
      actions={
        <button
          type="button"
          onClick={handleIngest}
          disabled={busy}
          className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-ink/25"
        >
          {busy ? "Ingesting..." : "Ingest demo documents"}
        </button>
      }
    >
      <div className="space-y-4">
        <p className="rounded-md border border-line bg-panel px-4 py-3 text-sm leading-6 text-ink/65">
          Editing markdown files does not update the database until documents are ingested again.
        </p>
        {ingestResult ? (
          <p className="rounded-md border border-brand/25 bg-brand/10 px-4 py-3 text-sm font-medium text-brand">
            {ingestResult}
          </p>
        ) : null}
        {loading ? <LoadingState label="Loading documents..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && documents.length ? <DocumentsTable documents={documents} /> : null}
        {!loading && !error && !documents.length ? (
          <EmptyState title="No documents ingested yet." message="Use the ingest button to load the demo business markdown files." />
        ) : null}
      </div>
    </DashboardLayout>
  );
}
