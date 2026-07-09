"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { verifyToken } from "@/lib/api";

function VerifyInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError("Missing token");
      return;
    }
    verifyToken(token)
      .then(() => router.replace("/market"))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Verification failed")
      );
  }, [token, router]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        {error ? (
          <>
            <p className="text-red-600">{error}</p>
            <a href="/" className="mt-4 inline-block text-blue-600 underline">
              Back to sign in
            </a>
          </>
        ) : (
          <p className="text-slate-700">Verifying your work email…</p>
        )}
      </div>
    </main>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <VerifyInner />
    </Suspense>
  );
}
