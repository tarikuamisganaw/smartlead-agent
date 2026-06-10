"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AuthStatus from "@/components/AuthStatus";
import ChatWindow from "@/components/ChatWindow";
import EmptyState from "@/components/EmptyState";
import LoadingState from "@/components/LoadingState";
import { getAccessToken } from "@/lib/api";

export default function ChatsPage() {
  const [loading, setLoading] = useState(true);
  const [requiresLogin, setRequiresLogin] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      setRequiresLogin(true);
      setLoading(false);
      return;
    }
    setLoading(false);
  }, []);

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-5">
          <div>
            <h1 className="text-3xl font-semibold text-ink">Chats</h1>
            <p className="mt-2 text-sm text-ink/65">Review and continue your conversations.</p>
          </div>
          <AuthStatus />
        </div>
        {loading ? <LoadingState label="Loading chats..." /> : null}
        {requiresLogin ? (
          <EmptyState
            title="Sign in to view chats."
            message="Use the homepage to try chat, or sign in to open your conversations."
            action={
              <div className="flex flex-wrap gap-2">
                <Link className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white" href="/login">
                  Login
                </Link>
                <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink" href="/register">
                  Register
                </Link>
              </div>
            }
          />
        ) : null}
        {!loading && !requiresLogin ? <ChatWindow /> : null}
      </div>
    </main>
  );
}
