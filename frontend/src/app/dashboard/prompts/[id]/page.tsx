"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { prompts, type Prompt, type PromptVersion } from "@/lib/api";
import DiffViewer from "@/components/DiffViewer";

export default function PromptEditorPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [content, setContent] = useState("");
  const [commitMessage, setCommitMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Diff viewer state
  const [diffMode, setDiffMode] = useState(false);
  const [diffVersionA, setDiffVersionA] = useState<string>("");
  const [diffVersionB, setDiffVersionB] = useState<string>("");

  // Variable interpolation state
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [interpolated, setInterpolated] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [p, v] = await Promise.all([
        prompts.get(id),
        prompts.listVersions(id),
      ]);
      setPrompt(p);
      setVersions(v);
      setContent(p.latest_version?.content || "");

      // Init variable inputs
      const vars = p.latest_version?.variables || [];
      const init: Record<string, string> = {};
      vars.forEach((v) => (init[v] = ""));
      setVariables(init);

      // Default diff to last two versions
      if (v.length >= 2) {
        setDiffVersionA(v[1].id);
        setDiffVersionB(v[0].id);
      }
    } catch {
      router.push("/login");
    }
  }, [id, router]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSave = async () => {
    if (!content.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await prompts.saveVersion(id, {
        content,
        commit_message: commitMessage || undefined,
      });
      setCommitMessage("");
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleInterpolate = async () => {
    try {
      const result = await prompts.interpolate(content, variables);
      setInterpolated(result.result);
    } catch {
      setError("Interpolation failed");
    }
  };

  const getDiffVersionContent = (versionId: string) =>
    versions.find((v) => v.id === versionId)?.content || "";

  if (!prompt) return <p className="p-8 text-gray-500">Loading...</p>;

  const detectedVars = versions[0]?.variables || [];

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/prompts"
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Prompts
          </Link>
          <span className="text-gray-300">/</span>
          <h1 className="text-sm font-semibold text-gray-900">{prompt.name}</h1>
          {prompt.description && (
            <span className="text-sm text-gray-400">— {prompt.description}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {prompt.version_count} version{prompt.version_count !== 1 ? "s" : ""}
          </span>
          <button
            onClick={() => setDiffMode(!diffMode)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium ${
              diffMode ? "bg-purple-50 border-purple-300 text-purple-700" : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            {diffMode ? "Hide Diff" : "View Diff"}
          </button>
        </div>
      </div>

      <div className="mx-auto max-w-6xl p-6 flex gap-6">
        {/* Main editor */}
        <div className="flex-1 flex flex-col gap-4">
          {/* Editor */}
          <div className="rounded-xl border bg-white shadow-sm">
            <div className="border-b px-4 py-3 flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Prompt Editor</span>
              {detectedVars.length > 0 && (
                <span className="text-xs text-gray-400">
                  Variables: {detectedVars.map((v) => `{{${v}}}`).join(", ")}
                </span>
              )}
            </div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={16}
              className="w-full px-4 py-3 text-sm font-mono text-gray-800 outline-none resize-none rounded-b-xl"
              placeholder="Write your prompt here... Use {{variable_name}} for dynamic variables."
            />
          </div>

          {/* Save bar */}
          <div className="rounded-xl border bg-white p-4 shadow-sm flex items-center gap-3">
            <input
              placeholder="Commit message (optional)..."
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              className="flex-1 rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : saved ? "Saved ✓" : "Save Version"}
            </button>
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</p>
          )}

          {/* Variable interpolation */}
          {detectedVars.length > 0 && (
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-gray-700">
                Test Variable Interpolation
              </h3>
              <div className="flex flex-col gap-2 mb-3">
                {detectedVars.map((v) => (
                  <div key={v} className="flex items-center gap-2">
                    <span className="text-xs font-mono text-purple-600 w-32">{`{{${v}}}`}</span>
                    <input
                      placeholder={`Value for ${v}`}
                      value={variables[v] || ""}
                      onChange={(e) =>
                        setVariables({ ...variables, [v]: e.target.value })
                      }
                      className="flex-1 rounded-lg border px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-purple-400"
                    />
                  </div>
                ))}
              </div>
              <button
                onClick={handleInterpolate}
                className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-700"
              >
                Preview Interpolated Prompt
              </button>
              {interpolated && (
                <div className="mt-3 rounded-lg bg-purple-50 p-3 text-sm text-gray-700 font-mono whitespace-pre-wrap">
                  {interpolated}
                </div>
              )}
            </div>
          )}

          {/* Diff viewer */}
          {diffMode && versions.length >= 2 && (
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-gray-700">Diff Viewer</h3>
              <div className="flex gap-3 mb-3">
                <select
                  value={diffVersionA}
                  onChange={(e) => setDiffVersionA(e.target.value)}
                  className="flex-1 rounded-lg border px-3 py-2 text-sm outline-none"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      v{v.version_number} — {v.commit_message || "no message"}
                    </option>
                  ))}
                </select>
                <span className="self-center text-gray-400 text-sm">→</span>
                <select
                  value={diffVersionB}
                  onChange={(e) => setDiffVersionB(e.target.value)}
                  className="flex-1 rounded-lg border px-3 py-2 text-sm outline-none"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      v{v.version_number} — {v.commit_message || "no message"}
                    </option>
                  ))}
                </select>
              </div>
              <DiffViewer
                oldContent={getDiffVersionContent(diffVersionA)}
                newContent={getDiffVersionContent(diffVersionB)}
                oldLabel={`v${versions.find((v) => v.id === diffVersionA)?.version_number}`}
                newLabel={`v${versions.find((v) => v.id === diffVersionB)?.version_number}`}
              />
            </div>
          )}
        </div>

        {/* Version sidebar */}
        <div className="w-64 flex-shrink-0">
          <div className="rounded-xl border bg-white shadow-sm">
            <div className="border-b px-4 py-3">
              <span className="text-sm font-semibold text-gray-700">Version History</span>
            </div>
            <div className="max-h-[600px] overflow-y-auto">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className="border-b last:border-b-0 px-4 py-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => setContent(version.content)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-blue-600">
                      v{version.version_number}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(version.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 truncate">
                    {version.commit_message || "No commit message"}
                  </p>
                  {version.variables.length > 0 && (
                    <p className="mt-1 text-xs text-purple-500">
                      {version.variables.length} variable{version.variables.length !== 1 ? "s" : ""}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
