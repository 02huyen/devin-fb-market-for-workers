const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface User {
  id: number;
  email: string;
  domain: string;
  company_name: string;
  display_name: string;
  is_verified: boolean;
}

export interface Seller {
  id: number;
  email: string;
  domain: string;
  company_name: string;
  display_name: string;
}

export interface Listing {
  id: number;
  title: string;
  description: string;
  listing_type: "sell" | "buy" | "giveaway";
  price: number;
  location_name: string;
  latitude: number | null;
  longitude: number | null;
  is_active: boolean;
  created_at: string;
  seller: Seller;
}

export interface ListingInput {
  title: string;
  description: string;
  listing_type: string;
  price: number;
  location_name: string;
  latitude: number | null;
  longitude: number | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export function requestLink(email: string) {
  return request<{ message: string; dev_magic_link: string | null }>(
    "/auth/request-link",
    { method: "POST", body: JSON.stringify({ email }) }
  );
}

export function verifyToken(token: string) {
  return request<User>(`/auth/verify?token=${encodeURIComponent(token)}`, {
    method: "POST",
  });
}

export function getMe() {
  return request<User>("/auth/me");
}

export function logout() {
  return request<{ message: string }>("/auth/logout", { method: "POST" });
}

export function getListings(params: {
  q?: string;
  listing_type?: string;
  lat?: number;
  lng?: number;
  radius_miles?: number;
}) {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  if (params.listing_type) sp.set("listing_type", params.listing_type);
  if (params.lat !== undefined) sp.set("lat", String(params.lat));
  if (params.lng !== undefined) sp.set("lng", String(params.lng));
  if (params.radius_miles !== undefined)
    sp.set("radius_miles", String(params.radius_miles));
  const qs = sp.toString();
  return request<Listing[]>(`/listings${qs ? `?${qs}` : ""}`);
}

export function createListing(input: ListingInput) {
  return request<Listing>("/listings", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function deleteListing(id: number) {
  return request<{ message: string }>(`/listings/${id}`, { method: "DELETE" });
}
