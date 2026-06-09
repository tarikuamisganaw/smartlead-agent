"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { clearAccessToken, getAccessToken, getMe } from "@/lib/api";
import type { AuthMeResponse } from "@/lib/types";

export default function AuthStatus() {
  const [auth, setAuth] = useState<AuthMeResponse | null>(null);

  useEffect(() => {
    if (!getAccessToken()) {
      return;
    }
    getMe()
      .then((response) => setAuth(response))
      .catch(() => setAuth(null));
  }, []);

  function logout() {
    clearAccessToken();
    setAuth(null);
    window.location.href = "/";
  }

  if (auth) {
    const isOwner = auth.memberships.some((membership) => membership.role === "owner");
    return (
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Link className="rounded-md border border-line bg-white px-3 py-1.5 font-medium text-ink hover:text-brand" href="/chats">
          My chats
        </Link>
        {isOwner ? (
          <Link className="rounded-md bg-brand px-3 py-1.5 font-semibold text-white hover:bg-brand/90" href="/dashboard">
            Dashboard
          </Link>
        ) : null}
        <span className="text-ink/65">{auth.user.email}</span>
        <button type="button" onClick={logout} className="rounded-md border border-line bg-white px-3 py-1.5 font-medium text-ink hover:text-brand">
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <span className="text-ink/60">Guest chat</span>
      <Link className="rounded-md border border-line bg-white px-3 py-1.5 font-medium text-ink hover:text-brand" href="/login">
        Login
      </Link>
      <Link className="rounded-md bg-brand px-3 py-1.5 font-semibold text-white hover:bg-brand/90" href="/register">
        Register
      </Link>
    </div>
  );
}
