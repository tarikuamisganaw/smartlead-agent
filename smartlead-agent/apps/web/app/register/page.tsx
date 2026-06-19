"use client";

import { FormEvent, useState } from "react";
import ErrorState from "@/components/ErrorState";
import { refreshMe, registerUser, setAccessToken } from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [asOwner, setAsOwner] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await registerUser({ email, password, full_name: fullName, as_owner: asOwner });
      setAccessToken(response.access_token);
      await refreshMe();
      window.location.href = asOwner ? "/dashboard" : "/chats";
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <form onSubmit={handleSubmit} className="mx-auto grid max-w-md gap-4 rounded-md border border-line bg-white p-5 shadow-sm">
        <h1 className="text-2xl font-semibold text-ink">Register</h1>
        {error ? <ErrorState message={error} /> : null}
        <input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" className="min-h-11 rounded-md border border-line px-3 text-sm" />
        <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" className="min-h-11 rounded-md border border-line px-3 text-sm" />
        <input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" type="password" className="min-h-11 rounded-md border border-line px-3 text-sm" />
        <label className="flex items-center gap-2 text-sm text-ink/70">
          <input type="checkbox" checked={asOwner} onChange={(event) => setAsOwner(event.target.checked)} />
          Register as business owner for demo
        </label>
        <button disabled={loading} className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white disabled:bg-ink/25">
          {loading ? "Creating account..." : "Register"}
        </button>
      </form>
    </main>
  );
}
