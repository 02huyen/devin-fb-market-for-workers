"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { User, Message, getMe, getMessages, sendMessage, markConversationRead } from "@/lib/api";

export default function ConversationPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [user, setUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => router.replace("/"));
  }, [router]);

  useEffect(() => {
    if (!user || Number.isNaN(id)) return;
    setLoading(true);
    getMessages(id)
      .then((data) => {
        setMessages(data);
        markConversationRead(id);
      })
      .finally(() => setLoading(false));
  }, [user, id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || Number.isNaN(id)) return;
    setSending(true);
    try {
      await sendMessage(id, { text });
      const updated = await getMessages(id);
      setMessages(updated);
      setText("");
    } finally {
      setSending(false);
    }
  }

  if (!user) return null;

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <Link href="/messages" className="text-xl font-bold text-slate-900">
          ← Inbox
        </Link>
        <span className="text-sm text-slate-600">
          {user.display_name} · {user.company_name}
        </span>
      </header>

      <div className="mx-auto max-w-2xl p-6">
        {loading ? (
          <p className="text-slate-500">Loading conversation…</p>
        ) : (
          <>
            <div className="space-y-3">
              {messages.map((m) => {
                const isMe = m.sender.id === user.id;
                return (
                  <div key={m.id} className={`flex ${isMe ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-xs rounded-2xl px-4 py-2 sm:max-w-md ${
                        isMe ? "bg-blue-600 text-white" : "bg-white text-slate-900 shadow"
                      }`}
                    >
                      <p className="text-sm">{m.text}</p>
                      <p className={`mt-1 text-xs ${isMe ? "text-blue-100" : "text-slate-500"}`}>
                        {m.sender.display_name} · {new Date(m.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            <form onSubmit={onSubmit} className="mt-6 flex gap-2">
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Type a message…"
                className="flex-1 rounded-lg border border-slate-300 px-4 py-2"
              />
              <button
                type="submit"
                disabled={sending || !text.trim()}
                className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {sending ? "Sending…" : "Send"}
              </button>
            </form>
          </>
        )}
      </div>
    </main>
  );
}
