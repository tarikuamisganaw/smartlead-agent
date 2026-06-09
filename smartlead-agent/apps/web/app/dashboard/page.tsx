"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import { getDashboardSummary } from "@/lib/api";
import type { DashboardSummary } from "@/lib/types";
import { formatDateTime, shortId, truncate } from "@/lib/utils";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load dashboard summary."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout
      title="Overview"
      subtitle="Live operational snapshot from the local SmartLead Agent backend."
      actions={
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/">
          Open chat
        </Link>
      }
    >
      {loading ? <LoadingState label="Loading dashboard..." /> : null}
      {error ? <ErrorState message={error} /> : null}
      {summary ? (
        <div className="space-y-5">
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Total leads" value={summary.total_leads} detail={`${summary.total_conversations} conversations`} />
            <StatCard label="Hot leads" value={summary.hot_leads} detail={`${summary.warm_leads} warm, ${summary.cold_leads} cold`} />
            <StatCard label="Pending approvals" value={summary.pending_approvals} detail="Discounts, refunds, guarantees" />
            <StatCard label="Documents ingested" value={summary.total_documents} detail={`${summary.total_document_chunks} chunks indexed`} />
          </section>

          <section className="rounded-md border border-line bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-semibold text-ink">Recent Agent Runs</h2>
              <Link className="text-sm font-medium text-brand hover:underline" href="/dashboard/conversations">
                View conversations
              </Link>
            </div>
            <div className="mt-3 divide-y divide-line">
              {summary.recent_agent_runs.map((run) => (
                <div key={run.id} className="grid gap-2 py-3 first:pt-0 last:pb-0 md:grid-cols-[1fr_auto]">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Link className="font-semibold text-brand hover:underline" href={`/dashboard/traces/${run.id}`}>
                        {shortId(run.id)}
                      </Link>
                      <StatusBadge value={run.status} />
                      <span className="text-xs text-ink/50">{formatDateTime(run.started_at)}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-ink/65">{truncate(run.user_message, 160)}</p>
                  </div>
                  <Link className="self-start text-sm font-medium text-brand hover:underline" href={`/dashboard/conversations/${run.conversation_id}`}>
                    Conversation
                  </Link>
                </div>
              ))}
              {!summary.recent_agent_runs.length ? (
                <EmptyState title="No agent runs yet." message="Start from the chat demo and send a customer message." />
              ) : null}
            </div>
          </section>
        </div>
      ) : null}
    </DashboardLayout>
  );
}
