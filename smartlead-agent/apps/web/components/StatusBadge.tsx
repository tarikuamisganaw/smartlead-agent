import { cx, formatLabel } from "@/lib/utils";

type StatusBadgeProps = {
  value: string | boolean | null | undefined;
  label?: string;
};

const styles: Record<string, string> = {
  success: "border-brand/25 bg-brand/10 text-brand",
  failed: "border-accent/30 bg-accent/10 text-accent",
  skipped: "border-slate-300 bg-slate-100 text-slate-600",
  synced: "border-brand/25 bg-brand/10 text-brand",
  mock_synced: "border-brand/25 bg-brand/10 text-brand",
  not_configured: "border-gold/30 bg-gold/10 text-gold",
  pending: "border-gold/30 bg-gold/10 text-gold",
  true: "border-accent/30 bg-accent/10 text-accent",
  false: "border-brand/25 bg-brand/10 text-brand",
  hot: "border-accent/30 bg-accent/10 text-accent",
  warm: "border-gold/30 bg-gold/10 text-gold",
  cold: "border-slate-300 bg-slate-100 text-slate-600",
};

export default function StatusBadge({ value, label }: StatusBadgeProps) {
  const key = String(value ?? "unknown").toLowerCase();
  const text = label || (typeof value === "boolean" ? (value ? "Approval Required" : "No Approval") : formatLabel(key));

  return (
    <span
      className={cx(
        "inline-flex h-7 items-center rounded-md border px-2.5 text-xs font-semibold",
        styles[key] || "border-line bg-white text-ink/70",
      )}
    >
      {text}
    </span>
  );
}
