"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
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

  useEffect(() => {
    auth.me()
      .then((data) => setUser(data as User))
      .catch(() => router.push("/login"));
  }, [router]);

  const handleLogout = () => {
    auth.logout();
    router.push("/login");
  };

  if (!user) return <p className="p-8 text-gray-500">Loading...</p>;

  const features = [
    {
      title: "Prompt Management",
      description: "Create, version, and compare prompts like Git commits.",
      href: "/dashboard/prompts",
      emoji: "📝",
      status: "Ready",
    },
    {
      title: "Model Playground",
      description: "Run prompts across Groq, GPT, Claude side by side.",
      href: "/dashboard/playground",
      emoji: "🧪",
      status: "Ready",
    },
    {
      title: "Evaluation Engine",
      description: "Upload test datasets and auto-score prompt quality.",
      href: "#",
      emoji: "📊",
      status: "Phase 4",
    },
    {
      title: "AI Tracing",
      description: "Debug every request end-to-end like Chrome DevTools.",
      href: "#",
      emoji: "🔍",
      status: "Phase 5",
    },
    {
      title: "RAG Debugger",
      description: "See which chunks were retrieved and why.",
      href: "#",
      emoji: "📄",
      status: "Phase 6",
    },
    {
      title: "Monitoring",
      description: "Track cost, latency, errors, and hallucination rate.",
      href: "#",
      emoji: "📈",
      status: "Phase 8",
    },
  ];

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="border-b bg-white px-8 py-4 flex items-center justify-between">
        <h1 className="text-lg font-bold text-gray-900">AI Engineer Studio</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">{user.email}</span>
          <button
            onClick={handleLogout}
            className="rounded-lg border px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
          >
            Log out
          </button>
        </div>
      </div>

      <div className="mx-auto max-w-5xl p-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">
            Welcome back, {user.full_name || user.email.split("@")[0]}
          </h2>
          <p className="mt-1 text-gray-500">Your AI engineering workspace.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f) => (
            <Link
              key={f.title}
              href={f.href}
              className={`rounded-xl border bg-white p-5 shadow-sm transition-shadow ${
                f.href !== "#"
                  ? "hover:shadow-md cursor-pointer"
                  : "opacity-60 cursor-default pointer-events-none"
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-2xl">{f.emoji}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  f.status === "Ready"
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-500"
                }`}>
                  {f.status}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
              <p className="text-sm text-gray-500">{f.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
