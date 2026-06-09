import type { ReactNode } from "react";
import DashboardNav from "@/components/DashboardNav";

type DashboardLayoutProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export default function DashboardLayout({ title, subtitle, actions, children }: DashboardLayoutProps) {
  return (
    <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
        <DashboardNav />
        <section className="min-w-0">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-5">
            <div>
              <h1 className="text-2xl font-semibold text-ink sm:text-3xl">{title}</h1>
              {subtitle ? <p className="mt-2 max-w-3xl text-sm leading-6 text-ink/65">{subtitle}</p> : null}
            </div>
            {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
          </div>
          {children}
        </section>
      </div>
    </main>
  );
}
