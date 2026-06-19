import Link from "next/link";

export default function ProtectedDashboardNotice() {
  return (
    <div className="rounded-md border border-line bg-panel p-4 text-sm leading-6 text-ink/70">
      <p className="font-semibold text-ink">This dashboard is for the business owner.</p>
      <p className="mt-2">Owner access is required for leads, approvals, traces, documents, and other dashboard data.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink" href="/">
          Chat
        </Link>
        <Link className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white" href="/login">
          Login
        </Link>
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink" href="/register">
          Register
        </Link>
      </div>
    </div>
  );
}
