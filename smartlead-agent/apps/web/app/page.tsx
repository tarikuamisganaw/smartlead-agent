import ChatWindow from "@/components/ChatWindow";

export default function HomePage() {
  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-2 border-b border-line pb-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-3xl font-semibold tracking-normal text-ink sm:text-4xl">
                SmartLead Agent
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-ink/70 sm:text-base">
                AI website assistant that answers from business documents, qualifies leads, saves leads, and flags risky requests for human approval.
              </p>
            </div>
            <a
              href="/dashboard"
              className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink shadow-sm transition hover:border-brand hover:text-brand"
            >
              Dashboard
            </a>
          </div>
        </header>
        <ChatWindow />
      </div>
    </main>
  );
}
