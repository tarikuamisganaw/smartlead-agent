"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
<<<<<<< HEAD
import EmptyState from "@/components/EmptyState";
=======
>>>>>>> eval-bakup
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
<<<<<<< HEAD
      .then(setStatus)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load integrations."))
=======
      .then((response) => setStatus(response))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load integration status."))
>>>>>>> eval-bakup
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout
      title="Integrations"
<<<<<<< HEAD
      subtitle="External integrations are optional. The mock provider is used by default, so the app runs without external credentials."
=======
      subtitle="Owner-only status for lead sync and future notification providers."
>>>>>>> eval-bakup
    >
      <div className="space-y-4">
        {loading ? <LoadingState label="Loading integrations..." /> : null}
        {error ? <ErrorState message={error} /> : null}
<<<<<<< HEAD
        {status ? <IntegrationStatusCard status={status} /> : null}
        {!loading && !error && !status ? (
          <EmptyState title="No integration status found." message="Check that the FastAPI backend is running." />
        ) : null}
=======
        {!loading && !error && status ? <IntegrationStatusCard status={status} /> : null}
>>>>>>> eval-bakup
      </div>
    </DashboardLayout>
  );
}
