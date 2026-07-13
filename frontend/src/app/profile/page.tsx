"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, Listing, getMe, getListings, updateMe, deleteListing, markSold, renewListing, logout } from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  sell: "For sale",
  buy: "Wanted",
  giveaway: "Giveaway",
};

const STATUS_LABELS: Record<string, string> = {
  open: "Open",
  sold: "Sold",
  expired: "Expired",
  removed: "Removed",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-emerald-100 text-emerald-800",
  sold: "bg-slate-200 text-slate-700",
  expired: "bg-red-100 text-red-800",
  removed: "bg-slate-300 text-slate-700",
};

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!user) return;
    try {
      const data = await getListings({ seller_id: user.id, status: "all" });
      setListings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load listings");
    }
  }, [user]);

  useEffect(() => {
    getMe()
      .then((u) => {
        setUser(u);
        setDisplayName(u.display_name);
      })
      .catch(() => router.replace("/"));
  }, [router]);

  useEffect(() => {
    if (user) {
      setLoading(true);
      load().finally(() => setLoading(false));
    }
  }, [user, load]);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSaving(true);
    try {
      const updated = await updateMe(displayName);
      setUser(updated);
      setMessage("Display name updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  async function onRemove(id: number) {
    if (!confirm("Remove this listing?")) return;
    try {
      await deleteListing(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove listing");
    }
  }

  async function onMarkSold(id: number) {
    try {
      await markSold(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark as sold");
    }
  }

  async function onRenew(id: number) {
    try {
      await renewListing(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to renew");
    }
  }

  async function onLogout() {
    await logout();
    router.replace("/");
  }

  if (!user) return null;

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <Link href="/market" className="text-xl font-bold text-slate-900">
          Workplace Market
        </Link>
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <Link href="/messages" className="hover:underline">
            Messages
          </Link>
          <button onClick={onLogout} className="text-blue-600 hover:underline">
            Log out
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-4xl p-6">
        <section className="rounded-2xl bg-white p-6 shadow">
          <h1 className="text-xl font-bold text-slate-900">Your profile</h1>
          <p className="text-sm text-slate-500">{user.email}</p>

          <form onSubmit={onSave} className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label htmlFor="displayName" className="block text-sm font-medium text-slate-700">
                Display name
              </label>
              <input
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-4 py-2"
              />
            </div>
            <button
              type="submit"
              disabled={saving || !displayName.trim()}
              className="rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </form>

          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
          {message && <p className="mt-3 text-sm text-green-700">{message}</p>}
        </section>

        <section className="mt-8">
          <h2 className="text-lg font-semibold text-slate-900">Your listings</h2>
          {loading ? (
            <p className="mt-4 text-slate-500">Loading…</p>
          ) : listings.length === 0 ? (
            <p className="mt-4 text-slate-500">You have not posted any listings yet.</p>
          ) : (
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              {listings.map((item) => (
                <div key={item.id} className="rounded-2xl bg-white p-5 shadow">
                  <Link href={`/market/${item.id}`} className="block">
                    <div className="flex gap-2">
                      <span className="inline-block rounded-full px-2 py-1 text-xs font-semibold bg-slate-100 text-slate-700">
                        {TYPE_LABELS[item.listing_type] ?? item.listing_type}
                      </span>
                      <span
                        className={`inline-block rounded-full px-2 py-1 text-xs font-semibold ${STATUS_COLORS[item.status]}`}
                      >
                        {STATUS_LABELS[item.status]}
                      </span>
                    </div>
                    <h3 className="mt-2 font-semibold text-slate-900">{item.title}</h3>
                    <p className="mt-1 text-sm text-slate-600 line-clamp-2">
                      {item.description}
                    </p>
                    {item.location_name && (
                      <p className="mt-2 text-xs text-slate-500">{item.location_name}</p>
                    )}
                    {item.expires_at && (
                      <p className="mt-1 text-xs text-slate-500">
                        Expires {new Date(item.expires_at).toLocaleDateString()}
                      </p>
                    )}
                  </Link>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
                    {item.status === "open" && (
                      <button
                        onClick={() => onMarkSold(item.id)}
                        className="text-slate-600 hover:underline"
                      >
                        Mark as sold
                      </button>
                    )}
                    {(item.status === "sold" || item.status === "expired" || item.status === "removed") && (
                      <button
                        onClick={() => onRenew(item.id)}
                        className="text-blue-600 hover:underline"
                      >
                        Renew
                      </button>
                    )}
                    <button
                      onClick={() => onRemove(item.id)}
                      className="text-red-600 hover:underline"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
