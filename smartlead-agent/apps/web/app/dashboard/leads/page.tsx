"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LeadsTable from "@/components/LeadsTable";
import LoadingState from "@/components/LoadingState";
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
    <DashboardLayout
      title="Leads"
      subtitle="Captured and updated leads from the agent workflow."
      actions={
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/">
          Try chat demo
        </Link>
      }
    >
      <div className="space-y-4">
        {loading ? <LoadingState label="Loading leads..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && leads.length ? <LeadsTable leads={leads} /> : null}
        {!loading && !error && !leads.length ? (
          <EmptyState
            title="No leads yet."
            message='Try the chat demo with: "I need SEO for my gym. My budget is $2000."'
          />
        ) : null}
      </div>
    </DashboardLayout>
  );
}
