"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

type User = {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    auth
      .me()
      .then((data) => setUser(data as User))
      .catch(() => {
        router.push("/login");
      });
  }, [router]);

  const handleLogout = () => {
    auth.logout();
    router.push("/login");
  };

  if (error) return <p className="p-8 text-red-500">{error}</p>;
  if (!user) return <p className="p-8 text-gray-500">Loading...</p>;

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <button
            onClick={handleLogout}
            className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
          >
            Log out
          </button>
        </div>

        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-gray-800">
            Welcome, {user.full_name || user.email}!
          </h2>
          <div className="space-y-2 text-sm text-gray-600">
            <p><span className="font-medium">Email:</span> {user.email}</p>
            <p><span className="font-medium">User ID:</span> {user.id}</p>
            <p><span className="font-medium">Member since:</span>{" "}
              {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-xl border bg-white p-6 shadow-sm">
          <h2 className="mb-2 text-lg font-semibold text-gray-800">
            Phase 1 Complete ✅
          </h2>
          <p className="text-sm text-gray-500">
            Foundation is ready. Next up: Prompt Management (Phase 2).
          </p>
        </div>
      </div>
    </main>
  );
}
