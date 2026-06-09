"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LeadsTable from "@/components/LeadsTable";
import LoadingState from "@/components/LoadingState";
import { getLeads, syncLead } from "@/lib/api";
import type { Lead } from "@/lib/types";

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncingLeadId, setSyncingLeadId] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  useEffect(() => {
    loadLeads();
  }, []);

  async function loadLeads() {
    setError(null);
    try {
      const response = await getLeads();
      setLeads(response.leads);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load leads.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSync(leadId: string) {
    setSyncingLeadId(leadId);
    setSyncMessage(null);
    setError(null);
    try {
      const response = await syncLead(leadId);
      setLeads((current) => current.map((lead) => (lead.id === leadId ? response.lead : lead)));
      setSyncMessage(response.sync_result.message || `Sync status: ${response.sync_result.status}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not sync lead.");
    } finally {
      setSyncingLeadId(null);
    }
  }

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
        {syncMessage ? (
          <div className="rounded-md border border-brand/20 bg-brand/5 px-4 py-3 text-sm text-brand">{syncMessage}</div>
        ) : null}
        {!loading && !error && leads.length ? <LeadsTable leads={leads} syncingLeadId={syncingLeadId} onSync={handleSync} /> : null}
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
