"use client";

import { useEffect, useState, type ReactNode } from "react";
import DashboardNav from "@/components/DashboardNav";
import ProtectedDashboardNotice from "@/components/ProtectedDashboardNotice";
import { AUTH_ENABLED, getAccessToken, getMe, hasCachedOwnerAccess } from "@/lib/api";

type DashboardLayoutProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export default function DashboardLayout({ title, subtitle, actions, children }: DashboardLayoutProps) {
  const [accessStatus, setAccessStatus] = useState<"checking" | "allowed" | "denied">(() => {
    if (!AUTH_ENABLED) {
      return "allowed";
    }
    if (!getAccessToken()) {
      return "denied";
    }
    return hasCachedOwnerAccess() ? "allowed" : "checking";
  });

  useEffect(() => {
    if (!AUTH_ENABLED) {
      setAccessStatus("allowed");
      return;
    }
    if (!getAccessToken()) {
      setAccessStatus("denied");
      return;
    }
    getMe()
      .then((response) => {
        const isOwner = response.memberships.some((membership) => membership.role === "owner");
        setAccessStatus(isOwner ? "allowed" : "denied");
      })
      .catch(() => setAccessStatus("denied"));
  }, []);

  if (accessStatus === "checking") {
    return <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8" />;
  }

  if (accessStatus === "denied") {
    return (
      <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl">
          <ProtectedDashboardNotice />
        </div>
      </main>
    );
  }

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
