import StatusBadge from "@/components/StatusBadge";

type LeadSyncStatusBadgeProps = {
  status?: string | null;
};

export default function LeadSyncStatusBadge({ status }: LeadSyncStatusBadgeProps) {
  if (!status) {
    return <StatusBadge value="unsynced" label="Unsynced" />;
  }

  return <StatusBadge value={status} />;
}
