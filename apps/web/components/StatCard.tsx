type StatCardProps = {
  label: string;
  value: string | number;
  detail?: string;
};

export default function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <article className="rounded-md border border-line bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase text-ink/45">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-ink">{value}</p>
      {detail ? <p className="mt-2 text-sm text-ink/60">{detail}</p> : null}
    </article>
  );
}
