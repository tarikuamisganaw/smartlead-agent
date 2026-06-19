import { formatLabel, hasMeaningfulValue } from "@/lib/utils";

const fields = [
  "name",
  "email",
  "phone",
  "business_type",
  "service_interest",
  "budget",
  "timeline",
  "lead_score",
  "lead_quality",
];

export default function LeadInfoCard({ leadInfo }: { leadInfo: Record<string, unknown> }) {
  const visibleFields = fields.filter((field) => hasMeaningfulValue(leadInfo[field]));

  if (visibleFields.length === 0) {
    return null;
  }

  return (
    <section className="rounded-md border border-line bg-white p-4">
      <h2 className="text-sm font-semibold text-ink">Lead Info</h2>
      <dl className="mt-3 grid gap-3 sm:grid-cols-2">
        {visibleFields.map((field) => (
          <div key={field}>
            <dt className="text-xs font-medium uppercase text-ink/50">{formatLabel(field)}</dt>
            <dd className="mt-1 text-sm text-ink">{String(leadInfo[field])}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
