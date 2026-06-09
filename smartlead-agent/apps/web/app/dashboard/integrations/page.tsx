"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import ErrorState from "@/components/ErrorState";
import IntegrationStatusCard from "@/components/IntegrationStatusCard";
import LoadingState from "@/components/LoadingState";
import { getIntegrationStatus } from "@/lib/api";
import type { IntegrationStatus } from "@/lib/types";

export default function IntegrationsPage() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getIntegrationStatus()
      .then((response) => setStatus(response))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load integration status."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout
      title="Integrations"
      subtitle="Owner-only status for lead sync and future notification providers."
    >
      <div className="space-y-4">
        {loading ? <LoadingState label="Loading integrations..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && status ? <IntegrationStatusCard status={status} /> : null}
      </div>
    </DashboardLayout>
  );
}
