const cards = [
  { title: "Leads", href: "/dashboard/leads", description: "Review captured and updated leads." },
  { title: "Conversations", href: "/", description: "Continue testing the chat workflow." },
  { title: "Traces", href: "/", description: "Open a trace from a chat response." },
  { title: "Approvals", href: "/dashboard/approvals", description: "Inspect pending human review requests." },
  { title: "Documents", href: "/dashboard/documents", description: "Check ingested demo business documents." },
  { title: "RAG Test", href: "/dashboard/rag-test", description: "Try local document retrieval." },
];

export default function DashboardPage() {
  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-5">
          <div>
            <h1 className="text-3xl font-semibold text-ink">Dashboard</h1>
            <p className="mt-2 text-sm text-ink/65">Week 3C will expand these operational views.</p>
          </div>
          <a className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/">
            Back to chat
          </a>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <a
              key={card.title}
              href={card.href}
              className="rounded-md border border-line bg-white p-4 shadow-sm transition hover:border-brand hover:shadow-soft"
            >
              <h2 className="text-lg font-semibold text-ink">{card.title}</h2>
              <p className="mt-2 text-sm leading-6 text-ink/65">{card.description}</p>
            </a>
          ))}
        </div>
      </div>
    </main>
  );
}
