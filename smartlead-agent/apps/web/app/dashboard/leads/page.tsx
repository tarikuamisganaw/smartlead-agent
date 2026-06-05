"use client";

import { useEffect, useState } from "react";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import StatusBadge from "@/components/StatusBadge";
import { getLeads } from "@/lib/api";
import type { Lead } from "@/lib/types";

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLeads()
      .then((response) => setLeads(response.leads))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load leads."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <PageHeader title="Leads" />
        {loading ? <LoadingState label="Loading leads..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        <div className="grid gap-3">
          {leads.map((lead) => (
            <article key={lead.id} className="rounded-md border border-line bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-ink">{lead.name || lead.email || "Unnamed lead"}</h2>
                  <p className="mt-1 text-sm text-ink/60">{lead.service_interest || "No service"} · {lead.business_type || "No business type"}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {lead.lead_quality ? <StatusBadge value={lead.lead_quality} /> : null}
                  {lead.status ? <StatusBadge value={lead.status} /> : null}
                </div>
              </div>
              <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                <Info label="Email" value={lead.email} />
                <Info label="Phone" value={lead.phone} />
                <Info label="Budget" value={lead.budget ? `$${lead.budget}` : null} />
                <Info label="Timeline" value={lead.timeline} />
                <Info label="Score" value={lead.lead_score?.toString()} />
                <Info label="Conversation" value={lead.conversation_id} />
              </dl>
            </article>
          ))}
          {!loading && !leads.length ? <p className="text-sm text-ink/60">No leads yet.</p> : null}
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

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase text-ink/50">{label}</dt>
      <dd className="mt-1 break-words text-ink">{value || "—"}</dd>
    </div>
  );
}
