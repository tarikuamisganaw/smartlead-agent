"use client";

import { FormEvent, useState } from "react";
import ErrorState from "@/components/ErrorState";
import { getMe, loginUser, setAccessToken } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await loginUser({ email, password });
      setAccessToken(response.access_token);
      const me = await getMe();
      const isOwner = me.memberships.some((membership) => membership.role === "owner");
      window.location.href = isOwner ? "/dashboard" : "/chats";
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <form onSubmit={handleSubmit} className="mx-auto grid max-w-md gap-4 rounded-md border border-line bg-white p-5 shadow-sm">
        <h1 className="text-2xl font-semibold text-ink">Login</h1>
        {error ? <ErrorState message={error} /> : null}
        <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" className="min-h-11 rounded-md border border-line px-3 text-sm" />
        <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" type="password" className="min-h-11 rounded-md border border-line px-3 text-sm" />
        <button disabled={loading} className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white disabled:bg-ink/25">
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
    </main>
  );
}
