"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { prompts, type Prompt } from "@/lib/api";

export default function PromptsPage() {
  const router = useRouter();
  const [promptList, setPromptList] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [newForm, setNewForm] = useState({ name: "", description: "", content: "" });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    prompts.list()
      .then(setPromptList)
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  const handleCreate = async () => {
    if (!newForm.name.trim() || !newForm.content.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await prompts.create({
        name: newForm.name,
        description: newForm.description || undefined,
        content: newForm.content,
        commit_message: "Initial version",
      });
      router.push(`/dashboard/prompts/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create prompt");
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    await prompts.delete(id);
    setPromptList((prev) => prev.filter((p) => p.id !== id));
  };

  if (loading) return <p className="p-8 text-gray-500">Loading prompts...</p>;

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Prompts</h1>
            <p className="text-sm text-gray-500">
              {promptList.length} prompt{promptList.length !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              href="/dashboard"
              className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
            >
              ← Dashboard
            </Link>
            <button
              onClick={() => setShowNew(true)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
            >
              + New Prompt
            </button>
          </div>
        </div>

        {/* New prompt form */}
        {showNew && (
          <div className="mb-6 rounded-xl border bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold">New Prompt</h2>
            {error && (
              <p className="mb-3 rounded bg-red-50 p-2 text-sm text-red-600">{error}</p>
            )}
            <div className="flex flex-col gap-3">
              <input
                placeholder="Prompt name *"
                value={newForm.name}
                onChange={(e) => setNewForm({ ...newForm, name: e.target.value })}
                className="rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                placeholder="Description (optional)"
                value={newForm.description}
                onChange={(e) => setNewForm({ ...newForm, description: e.target.value })}
                className="rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              />
              <textarea
                placeholder="Prompt content * — use {{variable}} for variables"
                value={newForm.content}
                onChange={(e) => setNewForm({ ...newForm, content: e.target.value })}
                rows={5}
                className="rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={creating}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create Prompt"}
                </button>
                <button
                  onClick={() => setShowNew(false)}
                  className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Prompt list */}
        {promptList.length === 0 && !showNew ? (
          <div className="rounded-xl border bg-white p-12 text-center shadow-sm">
            <p className="text-gray-400">No prompts yet.</p>
            <button
              onClick={() => setShowNew(true)}
              className="mt-3 text-sm text-blue-600 hover:underline"
            >
              Create your first prompt →
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {promptList.map((prompt) => (
              <div
                key={prompt.id}
                className="flex items-center justify-between rounded-xl border bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/dashboard/prompts/${prompt.id}`}
                    className="text-base font-semibold text-gray-900 hover:text-blue-600"
                  >
                    {prompt.name}
                  </Link>
                  {prompt.description && (
                    <p className="mt-0.5 text-sm text-gray-500 truncate">
                      {prompt.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center gap-3 text-xs text-gray-400">
                    <span>{prompt.version_count} version{prompt.version_count !== 1 ? "s" : ""}</span>
                    {prompt.latest_version?.variables?.length > 0 && (
                      <span>
                        Variables: {prompt.latest_version.variables.map((v) => `{{${v}}}`).join(", ")}
                      </span>
                    )}
                    <span>Updated {new Date(prompt.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <Link
                    href={`/dashboard/prompts/${prompt.id}`}
                    className="rounded-lg border px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100"
                  >
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDelete(prompt.id, prompt.name)}
                    className="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-500 hover:bg-red-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
