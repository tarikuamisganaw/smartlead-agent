"use client";

import { useEffect, useState } from "react";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import StatusBadge from "@/components/StatusBadge";
import { getApprovals } from "@/lib/api";
import type { Approval } from "@/lib/types";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getApprovals()
      .then((response) => setApprovals(response.approvals))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load approvals."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <PageHeader title="Approvals" />
        {loading ? <LoadingState label="Loading approvals..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        <div className="grid gap-3">
          {approvals.map((approval) => (
            <article key={approval.id} className="rounded-md border border-line bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-ink">{approval.action_type}</h2>
                <StatusBadge value={approval.status} />
              </div>
              <p className="mt-3 text-sm leading-6 text-ink/70">{approval.reason}</p>
              {approval.draft_response ? <p className="mt-2 text-sm text-ink/60">{approval.draft_response}</p> : null}
            </article>
          ))}
          {!loading && !approvals.length ? <p className="text-sm text-ink/60">No approvals yet.</p> : null}
        </div>
      </div>
    </main>
  );
}

function PageHeader({ title }: { title: string }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-5">
      <h1 className="text-3xl font-semibold text-ink">{title}</h1>
      <a className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/dashboard">
        Dashboard
      </a>
    </div>
  );
}
