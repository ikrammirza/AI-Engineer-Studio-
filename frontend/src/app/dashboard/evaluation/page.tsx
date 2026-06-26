"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { evaluation, type Dataset } from "@/lib/api";

export default function EvaluationPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([evaluation.listDatasets(), evaluation.listRuns()])
      .then(([d, r]) => { setDatasets(d); setRuns(r); })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  const handleUpload = async () => {
    if (!form.name.trim() || !fileRef.current?.files?.[0]) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("name", form.name);
      formData.append("description", form.description);
      formData.append("file", fileRef.current.files[0]);
      const dataset = await evaluation.uploadDataset(formData);
      setDatasets((prev) => [dataset, ...prev]);
      setShowUpload(false);
      setForm({ name: "", description: "" });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <p className="p-8 text-gray-500">Loading...</p>;

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Evaluation Engine</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Upload test datasets and auto-score your prompts
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
              onClick={() => setShowUpload(true)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
            >
              + Upload Dataset
            </button>
          </div>
        </div>

        {/* Upload form */}
        {showUpload && (
          <div className="mb-6 rounded-xl border bg-white p-6 shadow-sm">
            <h2 className="mb-1 text-lg font-semibold">Upload CSV Dataset</h2>
            <p className="mb-4 text-xs text-gray-400">
              CSV must have <code className="bg-gray-100 px-1 rounded">question</code> and{" "}
              <code className="bg-gray-100 px-1 rounded">expected</code> columns.
            </p>
            {error && (
              <p className="mb-3 rounded bg-red-50 p-2 text-sm text-red-600">{error}</p>
            )}
            <div className="flex flex-col gap-3">
              <input
                placeholder="Dataset name *"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                placeholder="Description (optional)"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="rounded-lg border-2 border-dashed border-gray-200 p-6 text-center">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  id="csv-upload"
                />
                <label
                  htmlFor="csv-upload"
                  className="cursor-pointer text-sm text-blue-600 hover:underline"
                >
                  Click to select CSV file
                </label>
                <p className="mt-1 text-xs text-gray-400">
                  {fileRef.current?.files?.[0]?.name || "No file selected"}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {uploading ? "Uploading..." : "Upload Dataset"}
                </button>
                <button
                  onClick={() => setShowUpload(false)}
                  className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-6">
          {/* Datasets */}
          <div>
            <h2 className="mb-3 text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Datasets ({datasets.length})
            </h2>
            {datasets.length === 0 ? (
              <div className="rounded-xl border bg-white p-8 text-center shadow-sm">
                <p className="text-sm text-gray-400">No datasets yet.</p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="mt-2 text-sm text-blue-600 hover:underline"
                >
                  Upload your first CSV →
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {datasets.map((d) => (
                  <div
                    key={d.id}
                    className="rounded-xl border bg-white p-4 shadow-sm"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-gray-800 text-sm">{d.name}</p>
                        {d.description && (
                          <p className="text-xs text-gray-400 mt-0.5">{d.description}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">
                          {d.row_count} questions · {new Date(d.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Link
                        href={`/dashboard/evaluation/run?dataset=${d.id}`}
                        className="rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-600 hover:bg-blue-100"
                      >
                        Run Eval →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent runs */}
          <div>
            <h2 className="mb-3 text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Recent Runs ({runs.length})
            </h2>
            {runs.length === 0 ? (
              <div className="rounded-xl border bg-white p-8 text-center shadow-sm">
                <p className="text-sm text-gray-400">No evaluation runs yet.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {runs.map((run) => (
                  <Link
                    key={run.id}
                    href={`/dashboard/evaluation/runs/${run.id}`}
                    className="rounded-xl border bg-white p-4 shadow-sm hover:shadow-md transition-shadow block"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        run.status === "completed"
                          ? "bg-green-100 text-green-700"
                          : "bg-yellow-100 text-yellow-700"
                      }`}>
                        {run.status}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(run.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="text-xs text-gray-400">Accuracy</p>
                        <p className="text-lg font-bold text-gray-900">
                          {run.accuracy != null
                            ? `${(run.accuracy * 100).toFixed(0)}%`
                            : "—"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400">Avg Score</p>
                        <p className="text-lg font-bold text-gray-900">
                          {run.avg_score != null
                            ? run.avg_score.toFixed(2)
                            : "—"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400">Model</p>
                        <p className="text-sm font-medium text-gray-700">
                          {run.model_key.split("/")[1]}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400">Method</p>
                        <p className="text-sm font-medium text-gray-700">
                          {run.scoring_method}
                        </p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
