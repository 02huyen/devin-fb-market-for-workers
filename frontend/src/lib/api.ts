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

export interface ListingImage {
  id: number;
  url: string;
  created_at: string;
}

export interface Comment {
  id: number;
  text: string;
  created_at: string;
  user: User;
}

export interface CommentInput {
  text: string;
}

export interface Conversation {
  id: number;
  listing_id: number;
  buyer: User;
  seller: User;
  updated_at: string;
  created_at: string;
  unread_count: number;
}

export interface Message {
  id: number;
  text: string;
  read_at: string | null;
  created_at: string;
  sender: User;
}

export interface MessageInput {
  text: string;
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
  status: "open" | "sold" | "expired";
  expires_at: string | null;
  created_at: string;
  seller: Seller;
  images: ListingImage[];
}

export interface ListingInput {
  title: string;
  description: string;
  listing_type: string;
  price: number;
  location_name: string;
  latitude: number | null;
  longitude: number | null;
  expiry_days?: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: isFormData ? undefined : { "Content-Type": "application/json" },
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

export function updateMe(display_name: string) {
  return request<User>("/auth/me", {
    method: "PATCH",
    body: JSON.stringify({ display_name }),
  });
}

export function logout() {
  return request<{ message: string }>("/auth/logout", { method: "POST" });
}

export function getListing(id: number) {
  return request<Listing>(`/listings/${id}`);
}

export function getListings(params: {
  q?: string;
  listing_type?: string;
  status?: string;
  lat?: number;
  lng?: number;
  radius_miles?: number;
  seller_id?: number;
}) {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  if (params.listing_type) sp.set("listing_type", params.listing_type);
  if (params.status) sp.set("status", params.status);
  if (params.lat !== undefined) sp.set("lat", String(params.lat));
  if (params.lng !== undefined) sp.set("lng", String(params.lng));
  if (params.radius_miles !== undefined)
    sp.set("radius_miles", String(params.radius_miles));
  if (params.seller_id !== undefined) sp.set("seller_id", String(params.seller_id));
  const qs = sp.toString();
  return request<Listing[]>(`/listings${qs ? `?${qs}` : ""}`);
}

export function createListing(input: ListingInput) {
  return request<Listing>("/listings", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function uploadImage(id: number, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<ListingImage>(`/listings/${id}/images`, {
    method: "POST",
    body,
  });
}

export function getComments(listingId: number) {
  return request<Comment[]>(`/listings/${listingId}/comments`);
}

export function createComment(listingId: number, input: CommentInput) {
  return request<Comment>(`/listings/${listingId}/comments`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getConversations() {
  return request<Conversation[]>("/messages/conversations");
}

export function startConversation(listingId: number) {
  return request<Conversation>(`/messages/conversations?listing_id=${listingId}`, {
    method: "POST",
  });
}

export function getMessages(conversationId: number) {
  return request<Message[]>(`/messages/conversations/${conversationId}/messages`);
}

export function sendMessage(conversationId: number, input: MessageInput) {
  return request<Message>(`/messages/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function markConversationRead(conversationId: number) {
  return request<{ message: string }>(`/messages/conversations/${conversationId}/read`, {
    method: "POST",
  });
}

export function markSold(id: number) {
  return request<Listing>(`/listings/${id}/sold`, { method: "POST" });
}

export function renewListing(id: number) {
  return request<Listing>(`/listings/${id}/renew`, { method: "POST" });
}

export function deleteListing(id: number) {
  return request<{ message: string }>(`/listings/${id}`, { method: "DELETE" });
}
