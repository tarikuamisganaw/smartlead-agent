"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ApprovalList from "@/components/ApprovalList";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
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
    <DashboardLayout
      title="Approvals"
      subtitle="Read-only human review queue for risky requests such as discounts, refunds, and guarantees."
      actions={
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/">
          Try risky prompt
        </Link>
      }
    >
      <div className="space-y-4">
        {loading ? <LoadingState label="Loading approvals..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && approvals.length ? <ApprovalList approvals={approvals} /> : null}
        {!loading && !error && !approvals.length ? (
          <EmptyState title="No approval requests yet." message="Try asking for a discount in the chat demo." />
        ) : null}
      </div>
    </DashboardLayout>
  );
}
