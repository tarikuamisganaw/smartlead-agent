"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cx } from "@/lib/utils";

const links = [
  { href: "/", label: "Chat Demo" },
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/leads", label: "Leads" },
  { href: "/dashboard/conversations", label: "Conversations" },
  { href: "/dashboard/approvals", label: "Approvals" },
  { href: "/dashboard/documents", label: "Documents" },
  { href: "/dashboard/rag-test", label: "RAG Test" },
  { href: "/dashboard/integrations", label: "Integrations" },
  { href: "/dashboard/evals", label: "Evals" },
];

export default function DashboardNav() {
  const pathname = usePathname();

  return (
    <aside className="lg:sticky lg:top-5 lg:self-start">
      <div className="rounded-md border border-line bg-white p-3 shadow-sm">
        <div className="px-2 py-2">
          <p className="text-xs font-semibold uppercase text-ink/45">SmartLead Agent</p>
          <p className="mt-1 text-sm font-semibold text-ink">Dashboard</p>
        </div>
        <nav className="mt-2 flex gap-1 overflow-x-auto lg:grid lg:overflow-visible">
          {links.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cx(
                  "whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition",
                  active ? "bg-brand text-white" : "text-ink/70 hover:bg-panel hover:text-brand",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
