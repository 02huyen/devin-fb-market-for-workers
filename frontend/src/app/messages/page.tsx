"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, Conversation, getMe, getConversations } from "@/lib/api";

export default function MessagesPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => router.replace("/"));
  }, [router]);

  useEffect(() => {
    if (!user) return;
    getConversations()
      .then(setConversations)
      .finally(() => setLoading(false));
  }, [user]);

  if (!user) return null;

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <Link href="/market" className="text-xl font-bold text-slate-900">
          Workplace Market
        </Link>
        <span className="text-sm text-slate-600">
          {user.display_name} · {user.company_name}
        </span>
      </header>

      <div className="mx-auto max-w-2xl p-6">
        <h1 className="text-xl font-bold text-slate-900">Inbox</h1>

        {loading ? (
          <p className="mt-4 text-slate-500">Loading…</p>
        ) : conversations.length === 0 ? (
          <p className="mt-4 text-slate-500">No conversations yet.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {conversations.map((conv) => {
              const other = conv.buyer.id === user.id ? conv.seller : conv.buyer;
              return (
                <Link
                  key={conv.id}
                  href={`/messages/${conv.id}`}
                  className="flex items-center justify-between rounded-2xl bg-white p-4 shadow hover:bg-slate-50"
                >
                  <div>
                    <p className="font-semibold text-slate-900">
                      {other.display_name} · {other.company_name}
                    </p>
                    <p className="text-sm text-slate-500">Listing #{conv.listing_id}</p>
                  </div>
                  {conv.unread_count > 0 && (
                    <span className="rounded-full bg-blue-600 px-2 py-1 text-xs font-semibold text-white">
                      {conv.unread_count}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
