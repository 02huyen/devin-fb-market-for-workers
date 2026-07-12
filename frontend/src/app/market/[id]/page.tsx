"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Comment, Listing, User, getListing, getMe, getComments, createComment, uploadImage, startConversation } from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  sell: "For sale",
  buy: "Wanted",
  giveaway: "Giveaway",
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

export default function ListingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [listing, setListing] = useState<Listing | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentText, setCommentText] = useState("");
  const [commentLoading, setCommentLoading] = useState(false);
  const [startingConversation, setStartingConversation] = useState(false);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => router.replace("/"));
  }, [router]);

  useEffect(() => {
    if (!user || Number.isNaN(id)) return;
    setLoading(true);
    Promise.all([getListing(id), getComments(id)])
      .then(([l, c]) => {
        setListing(l);
        setComments(c);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load listing"))
      .finally(() => setLoading(false));
  }, [user, id]);

  async function onUpload(files: FileList | null) {
    if (!files || !listing) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await uploadImage(listing.id, file);
      }
      const updated = await getListing(listing.id);
      setListing(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload image");
    } finally {
      setUploading(false);
    }
  }

  async function onMessageSeller() {
    if (!listing) return;
    setStartingConversation(true);
    try {
      const conv = await startConversation(listing.id);
      router.push(`/messages/${conv.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start conversation");
    } finally {
      setStartingConversation(false);
    }
  }

  async function onSubmitComment(e: React.FormEvent) {
    e.preventDefault();
    if (!listing || !commentText.trim()) return;
    setCommentLoading(true);
    try {
      await createComment(listing.id, { text: commentText.trim() });
      const updated = await getComments(listing.id);
      setComments(updated);
      setCommentText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to post comment");
    } finally {
      setCommentLoading(false);
    }
  }

  if (!user) return null;

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50 p-6">
        <div className="mx-auto max-w-3xl">
          <p className="text-slate-500">Loading listing…</p>
        </div>
      </main>
    );
  }

  if (error || !listing) {
    return (
      <main className="min-h-screen bg-slate-50 p-6">
        <div className="mx-auto max-w-3xl">
          <p className="text-red-600">{error ?? "Listing not found"}</p>
          <Link href="/market" className="mt-4 inline-block text-blue-600 hover:underline">
            Back to marketplace
          </Link>
        </div>
      </main>
    );
  }

  const contactSubject = encodeURIComponent(`Workplace Market: ${listing.title}`);
  const contactBody = encodeURIComponent(
    `Hi ${listing.seller.display_name}, I'm interested in your listing "${listing.title}" on Workplace Market.`
  );

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
          <Link href="/profile" className="hover:underline">
            {user.display_name} · {user.company_name}
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-3xl p-6">
        <Link href="/market" className="text-sm text-blue-600 hover:underline">
          ← Back to marketplace
        </Link>

        <div className="mt-4 rounded-2xl bg-white p-6 shadow sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex gap-2">
                <span className="inline-block rounded-full px-3 py-1 text-xs font-semibold bg-slate-100 text-slate-700">
                  {TYPE_LABELS[listing.listing_type] ?? listing.listing_type}
                </span>
                <span
                  className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${STATUS_COLORS[listing.status]}`}
                >
                  {STATUS_LABELS[listing.status]}
                </span>
              </div>
              <h1 className="mt-3 text-2xl font-bold text-slate-900 sm:text-3xl">
                {listing.title}
              </h1>
            </div>
            {listing.listing_type === "sell" && (
              <span className="text-2xl font-bold text-slate-900">
                ${listing.price.toFixed(2)}
              </span>
            )}
          </div>

          <p className="mt-6 whitespace-pre-wrap text-slate-700">
            {listing.description}
          </p>

          {listing.images.length > 0 && (
            <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
              {listing.images.map((img) => (
                <img
                  key={img.id}
                  src={img.url}
                  alt={listing.title}
                  className="w-full rounded-lg object-cover"
                />
              ))}
            </div>
          )}

          {listing.seller.id === user.id && listing.status === "open" && (
            <label className="mt-6 block text-sm text-slate-600">
              {uploading ? "Uploading…" : "Add photos"}
              <input
                type="file"
                accept="image/*"
                multiple
                disabled={uploading}
                onChange={(e) => onUpload(e.target.files)}
                className="mt-1 block w-full text-sm text-slate-700"
              />
            </label>
          )}

          {listing.location_name && (
            <p className="mt-6 text-sm text-slate-500">📍 {listing.location_name}</p>
          )}

          <div className="mt-8 border-t border-slate-100 pt-6">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Seller
            </h2>
            <div className="mt-2 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-semibold text-slate-900">{listing.seller.display_name}</p>
                <p className="text-sm text-slate-600">
                  {listing.seller.company_name} ({listing.seller.domain})
                </p>
              </div>
              {listing.seller.id !== user.id && (
                <>
                  {listing.status === "open" ? (
                    <div className="mt-3 flex flex-col gap-2 sm:mt-0 sm:flex-row">
                      <button
                        onClick={onMessageSeller}
                        disabled={startingConversation}
                        className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        {startingConversation ? "Starting…" : "Message seller"}
                      </button>
                      <a
                        href={`mailto:${listing.seller.email}?subject=${contactSubject}&body=${contactBody}`}
                        className="inline-flex items-center justify-center rounded-lg border border-slate-300 px-5 py-2.5 font-semibold text-slate-700 hover:bg-slate-100"
                      >
                        Email seller
                      </a>
                    </div>
                  ) : (
                    <span className="mt-3 inline-flex items-center justify-center rounded-lg bg-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-600 sm:mt-0">
                      This listing is {listing.status}
                    </span>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-2xl bg-white p-6 shadow sm:p-8">
          <h2 className="text-lg font-semibold text-slate-900">Comments</h2>

          {listing.status === "open" && (
            <form onSubmit={onSubmitComment} className="mt-4">
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Ask a question or leave a comment…"
                className="w-full rounded-lg border border-slate-300 px-4 py-2"
                rows={3}
              />
              <button
                type="submit"
                disabled={commentLoading || !commentText.trim()}
                className="mt-2 rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {commentLoading ? "Posting…" : "Post comment"}
              </button>
            </form>
          )}

          {listing.status !== "open" && (
            <p className="mt-4 text-sm text-slate-500">
              This listing is {listing.status}. Comments are read-only.
            </p>
          )}

          <div className="mt-4 space-y-4">
            {comments.map((c) => (
              <div key={c.id} className="border-b border-slate-100 pb-4 last:border-0">
                <p className="text-sm font-semibold text-slate-900">
                  {c.user.display_name} · {c.user.company_name}
                </p>
                <p className="mt-1 text-sm text-slate-600">{c.text}</p>
                <p className="mt-1 text-xs text-slate-400">
                  {new Date(c.created_at).toLocaleString()}
                </p>
              </div>
            ))}
            {comments.length === 0 && (
              <p className="text-sm text-slate-500">No comments yet.</p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
