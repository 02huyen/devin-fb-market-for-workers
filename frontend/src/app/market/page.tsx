"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  User,
  Listing,
  getMe,
  getListings,
  createListing,
  deleteListing,
  markSold,
  renewListing,
  uploadImage,
  logout,
} from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  sell: "For sale",
  buy: "Wanted",
  giveaway: "Giveaway",
};

const TYPE_COLORS: Record<string, string> = {
  sell: "bg-blue-100 text-blue-800",
  buy: "bg-amber-100 text-amber-800",
  giveaway: "bg-green-100 text-green-800",
};

const STATUS_LABELS: Record<string, string> = {
  open: "Open",
  sold: "Sold",
  expired: "Expired",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-emerald-100 text-emerald-800",
  sold: "bg-slate-200 text-slate-700",
  expired: "bg-red-100 text-red-800",
};

export default function MarketPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("open");
  const [radius, setRadius] = useState(50);
  const [useLocation, setUseLocation] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listingsLoading, setListingsLoading] = useState(true);

  const [form, setForm] = useState({
    title: "",
    description: "",
    listing_type: "sell",
    price: 0,
    location_name: "",
    expiry_days: 7,
  });
  const [imageFiles, setImageFiles] = useState<FileList | null>(null);

  const load = useCallback(async () => {
    setListingsLoading(true);
    setError(null);
    try {
      const data = await getListings({
        q: q || undefined,
        listing_type: typeFilter || undefined,
        status: statusFilter || undefined,
        lat: useLocation && coords ? coords.lat : undefined,
        lng: useLocation && coords ? coords.lng : undefined,
        radius_miles: useLocation && coords ? radius : undefined,
      });
      setListings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load listings");
    } finally {
      setListingsLoading(false);
    }
  }, [q, typeFilter, statusFilter, radius, useLocation, coords]);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => router.replace("/"));
  }, [router]);

  useEffect(() => {
    if (user) load();
  }, [user, load]);

  function enableLocation() {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setUseLocation(true);
      },
      () => setError("Could not get your location")
    );
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await createListing({
        title: form.title,
        description: form.description,
        listing_type: form.listing_type,
        price: Number(form.price) || 0,
        location_name: form.location_name,
        latitude: null,
        longitude: null,
        expiry_days: form.expiry_days,
      });
      if (imageFiles) {
        for (const file of Array.from(imageFiles)) {
          await uploadImage(created.id, file);
        }
      }
      setShowForm(false);
      setForm({
        title: "",
        description: "",
        listing_type: "sell",
        price: 0,
        location_name: "",
        expiry_days: 7,
      });
      setImageFiles(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create listing");
    }
  }

  async function onDelete(id: number) {
    await deleteListing(id);
    load();
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
        <h1 className="text-xl font-bold text-slate-900">Workplace Market</h1>
        <div className="flex items-center gap-4 text-sm text-slate-600">
          <Link href="/messages" className="hover:underline">
            Messages
          </Link>
          <Link href="/profile" className="hover:underline">
            {user.display_name} · {user.company_name}
          </Link>
          <button onClick={onLogout} className="text-blue-600 hover:underline">
            Log out
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-5xl p-6">
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search items…"
            className="flex-1 min-w-48 rounded-lg border border-slate-300 px-4 py-2"
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2"
          >
            <option value="">All types</option>
            <option value="sell">For sale</option>
            <option value="buy">Wanted</option>
            <option value="giveaway">Giveaway</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2"
          >
            <option value="open">Open</option>
            <option value="sold">Sold</option>
            <option value="expired">Expired</option>
            <option value="">All statuses</option>
          </select>
          {useLocation ? (
            <label className="flex items-center gap-2 text-sm text-slate-600">
              Within
              <input
                type="number"
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
                className="w-20 rounded-lg border border-slate-300 px-2 py-2"
              />
              miles
              <button
                onClick={() => setUseLocation(false)}
                className="text-blue-600 hover:underline"
              >
                clear
              </button>
            </label>
          ) : (
            <button
              onClick={enableLocation}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
            >
              Filter by my location
            </button>
          )}
          <button
            onClick={() => setShowForm((v) => !v)}
            className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700"
          >
            {showForm ? "Cancel" : "+ New listing"}
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        {showForm && (
          <form
            onSubmit={onCreate}
            className="mt-6 grid grid-cols-1 gap-4 rounded-2xl bg-white p-6 shadow sm:grid-cols-2"
          >
            <input
              required
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="rounded-lg border border-slate-300 px-4 py-2 sm:col-span-2"
            />
            <textarea
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="rounded-lg border border-slate-300 px-4 py-2 sm:col-span-2"
            />
            <select
              value={form.listing_type}
              onChange={(e) => setForm({ ...form, listing_type: e.target.value })}
              className="rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="sell">For sale</option>
              <option value="buy">Wanted</option>
              <option value="giveaway">Giveaway</option>
            </select>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="Price (USD)"
              value={form.price || ""}
              onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
              className="rounded-lg border border-slate-300 px-4 py-2"
            />
            <input
              placeholder="Location name (e.g. Austin, TX)"
              value={form.location_name}
              onChange={(e) => setForm({ ...form, location_name: e.target.value })}
              className="rounded-lg border border-slate-300 px-4 py-2 sm:col-span-2"
            />
            <label className="flex items-center gap-2 text-sm text-slate-600 sm:col-span-2">
              Expires in
              <select
                value={form.expiry_days}
                onChange={(e) =>
                  setForm({ ...form, expiry_days: Number(e.target.value) })
                }
                className="rounded-lg border border-slate-300 px-2 py-1"
              >
                <option value={1}>1 day</option>
                <option value={7}>7 days</option>
                <option value={14}>14 days</option>
                <option value={30}>30 days</option>
              </select>
            </label>
            <label className="block text-sm text-slate-600 sm:col-span-2">
              Photos
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => setImageFiles(e.target.files)}
                className="mt-1 block w-full text-sm text-slate-700"
              />
            </label>
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 sm:col-span-2"
            >
              Post listing
            </button>
          </form>
        )}

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {listingsLoading ? (
            <p className="text-slate-500 sm:col-span-2 lg:col-span-3">Loading listings…</p>
          ) : (
            <>
              {listings.map((item) => (
                <div key={item.id} className="relative rounded-2xl bg-white p-5 shadow">
                  <Link href={`/market/${item.id}`} className="block focus:outline-none">
                    {item.images[0] && (
                      <img
                        src={item.images[0].url}
                        alt={item.title}
                        className="h-40 w-full rounded-lg object-cover mb-3"
                      />
                    )}
                    <div className="flex items-start justify-between">
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-semibold ${TYPE_COLORS[item.listing_type]}`}
                      >
                        {TYPE_LABELS[item.listing_type]}
                      </span>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-semibold ${STATUS_COLORS[item.status]}`}
                      >
                        {STATUS_LABELS[item.status]}
                      </span>
                    </div>
                    <h2 className="mt-2 font-semibold text-slate-900">{item.title}</h2>
                    <p className="mt-1 text-sm text-slate-600 line-clamp-3">
                      {item.description}
                    </p>
                    <div className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
                      <p>
                        {item.seller.display_name} · {item.seller.company_name} (
                        {item.seller.domain})
                      </p>
                      {item.location_name && <p>{item.location_name}</p>}
                      {item.expires_at && (
                        <p>Expires {new Date(item.expires_at).toLocaleDateString()}</p>
                      )}
                    </div>
                  </Link>
                  {item.seller.id === user.id && (
                    <div className="relative z-10 mt-3 flex flex-wrap items-center gap-3 text-xs">
                      {item.status === "open" && (
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            onMarkSold(item.id);
                          }}
                          className="text-slate-600 hover:underline"
                        >
                          Mark as sold
                        </button>
                      )}
                      {(item.status === "sold" || item.status === "expired") && (
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            onRenew(item.id);
                          }}
                          className="text-blue-600 hover:underline"
                        >
                          Renew
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          onDelete(item.id);
                        }}
                        className="text-red-600 hover:underline"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              ))}
              {listings.length === 0 && (
                <p className="text-slate-500 sm:col-span-2 lg:col-span-3">
                  No listings match your filters yet.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}
