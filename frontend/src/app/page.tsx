"use client";

import { useState } from "react";
import { requestLink } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [devLink, setDevLink] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setDevLink(null);
    setLoading(true);
    try {
      const res = await requestLink(email);
      setMessage(res.message);
      setDevLink(res.dev_magic_link);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8">
        <h1 className="text-2xl font-bold text-slate-900">Workplace Market</h1>
        <p className="mt-2 text-slate-600">
          A trusted marketplace for verified professionals. Sign in with your
          work email — personal emails (Gmail, Yahoo, etc.) are not accepted.
        </p>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@yourcompany.com"
            className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Checking..." : "Send sign-in link"}
          </button>
        </form>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        {message && <p className="mt-4 text-sm text-green-700">{message}</p>}
        {devLink && (
          <p className="mt-2 text-sm text-slate-500 break-all">
            Dev mode link:{" "}
            <a href={devLink} className="text-blue-600 underline">
              {devLink}
            </a>
          </p>
        )}
      </div>
    </main>
  );
}
