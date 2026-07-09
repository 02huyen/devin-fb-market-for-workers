"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  Listing,
  getMe,
  getListings,
  createListing,
  deleteListing,
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

export default function MarketPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [radius, setRadius] = useState(50);
  const [useLocation, setUseLocation] = useState(false);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    title: "",
    description: "",
    listing_type: "sell",
    price: 0,
    location_name: "",
    latitude: "" as string,
    longitude: "" as string,
  });

  const load = useCallback(async () => {
    try {
      const data = await getListings({
        q: q || undefined,
        listing_type: typeFilter || undefined,
        lat: useLocation && coords ? coords.lat : undefined,
        lng: useLocation && coords ? coords.lng : undefined,
        radius_miles: useLocation && coords ? radius : undefined,
      });
      setListings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load listings");
    }
  }, [q, typeFilter, radius, useLocation, coords]);

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
      await createListing({
        title: form.title,
        description: form.description,
        listing_type: form.listing_type,
        price: Number(form.price) || 0,
        location_name: form.location_name,
        latitude: form.latitude ? Number(form.latitude) : null,
        longitude: form.longitude ? Number(form.longitude) : null,
      });
      setShowForm(false);
      setForm({
        title: "",
        description: "",
        listing_type: "sell",
        price: 0,
        location_name: "",
        latitude: "",
        longitude: "",
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create listing");
    }
  }

  async function onDelete(id: number) {
    await deleteListing(id);
    load();
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
          <span>
            {user.display_name} · {user.company_name}
          </span>
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
              className="rounded-lg border border-slate-300 px-4 py-2"
            />
            <div className="flex gap-2">
              <input
                placeholder="Latitude"
                value={form.latitude}
                onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                className="w-1/2 rounded-lg border border-slate-300 px-4 py-2"
              />
              <input
                placeholder="Longitude"
                value={form.longitude}
                onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                className="w-1/2 rounded-lg border border-slate-300 px-4 py-2"
              />
            </div>
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 sm:col-span-2"
            >
              Post listing
            </button>
          </form>
        )}

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {listings.map((item) => (
            <div key={item.id} className="rounded-2xl bg-white p-5 shadow">
              <div className="flex items-start justify-between">
                <span
                  className={`rounded-full px-2 py-1 text-xs font-semibold ${TYPE_COLORS[item.listing_type]}`}
                >
                  {TYPE_LABELS[item.listing_type]}
                </span>
                {item.listing_type === "sell" && (
                  <span className="font-bold text-slate-900">
                    ${item.price.toFixed(2)}
                  </span>
                )}
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
              </div>
              {item.seller.id === user.id && (
                <button
                  onClick={() => onDelete(item.id)}
                  className="mt-3 text-xs text-red-600 hover:underline"
                >
                  Remove listing
                </button>
              )}
            </div>
          ))}
          {listings.length === 0 && (
            <p className="text-slate-500 sm:col-span-2 lg:col-span-3">
              No listings match your filters yet.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
