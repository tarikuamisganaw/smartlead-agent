"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import DocumentsTable from "@/components/DocumentsTable";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import { getDocuments, ingestDemoDocuments, uploadDocument } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
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

  async function handleUpload() {
    if (!selectedFile || uploading) {
      return;
    }
    const extension = selectedFile.name.split(".").pop()?.toLowerCase();
    if (!extension || !["md", "txt"].includes(extension)) {
      setError("Only .md and .txt files can be uploaded.");
      return;
    }

    setUploading(true);
    setError(null);
    setIngestResult(null);
    try {
      const content = await selectedFile.text();
      const result = await uploadDocument({ title: selectedFile.name, content });
      setIngestResult(`${result.title} uploaded, ${result.chunks_created} chunks created.`);
      setSelectedFile(null);
      await loadDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not upload document.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <DashboardLayout
      title="Documents"
      subtitle="Manage the business documents the assistant can use."
      actions={
        <button
          type="button"
          onClick={handleIngest}
          disabled={busy}
          className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-ink/25"
        >
          {busy ? "Loading..." : "Load sample documents"}
        </button>
      }
    >
      <div className="space-y-4">
        <section className="rounded-md border border-line bg-white p-4 shadow-sm">
          <h2 className="text-sm font-semibold text-ink">Upload document</h2>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <input
              type="file"
              accept=".md,.txt,text/markdown,text/plain"
              onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              className="min-h-10 rounded-md border border-line bg-panel px-3 py-2 text-sm text-ink"
            />
            <button
              type="button"
              onClick={() => void handleUpload()}
              disabled={!selectedFile || uploading}
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-ink/25"
            >
              {uploading ? "Uploading..." : "Upload"}
            </button>
          </div>
          {selectedFile ? <p className="mt-2 text-xs text-ink/50">{selectedFile.name}</p> : null}
        </section>
        {ingestResult ? (
          <p className="rounded-md border border-brand/25 bg-brand/10 px-4 py-3 text-sm font-medium text-brand">
            {ingestResult}
          </p>
        ) : null}
        {loading ? <LoadingState label="Loading documents..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && documents.length ? <DocumentsTable documents={documents} /> : null}
        {!loading && !error && !documents.length ? (
          <EmptyState title="No documents yet." message="Load the sample set or upload a business document to get started." />
        ) : null}
      </div>
    </DashboardLayout>
  );
}
