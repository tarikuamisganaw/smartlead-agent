import StatusBadge from "@/components/StatusBadge";

<<<<<<< HEAD
export default function LeadSyncStatusBadge({ status }: { status?: string | null }) {
  return <StatusBadge value={status || "not_configured"} />;
=======
type LeadSyncStatusBadgeProps = {
  status?: string | null;
};

export default function LeadSyncStatusBadge({ status }: LeadSyncStatusBadgeProps) {
  if (!status) {
    return <StatusBadge value="unsynced" label="Unsynced" />;
  }

  return <StatusBadge value={status} />;
>>>>>>> eval-bakup
}
