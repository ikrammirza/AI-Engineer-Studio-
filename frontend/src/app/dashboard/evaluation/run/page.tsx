"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { evaluation, prompts, playground, type Dataset, type Prompt, type ModelDefinition } from "@/lib/api";

const SCORING_METHODS = [
  {
    id: "contains",
    label: "Contains Match",
    description: "Passes if the answer contains the expected string",
  },
  {
    id: "exact",
    label: "Exact Match",
    description: "Passes if the answer matches exactly (case-insensitive)",
  },
  {
    id: "llm",
    label: "LLM as Judge",
    description: "Uses Groq Llama to score quality 0.0–1.0 (most accurate)",
  },
];

export default function NewRunPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedDataset = searchParams.get("dataset");

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [promptList, setPromptList] = useState<Prompt[]>([]);
  const [models, setModels] = useState<ModelDefinition[]>([]);

  const [selectedDataset, setSelectedDataset] = useState(preselectedDataset || "");
  const [selectedPrompt, setSelectedPrompt] = useState("");
  const [selectedModel, setSelectedModel] = useState("groq/llama-3.3-70b");
  const [scoringMethod, setScoringMethod] = useState("contains");

  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      evaluation.listDatasets(),
      prompts.list(),
      playground.models(),
    ])
      .then(([d, p, m]) => {
        setDatasets(d);
        setPromptList(p);
        setModels(m);
        if (p.length > 0) setSelectedPrompt(p[0].id);
      })
      .catch(() => router.push("/login"));
  }, [router]);

  const handleRun = async () => {
    if (!selectedDataset || !selectedPrompt || !selectedModel) return;
    setRunning(true);
    setError(null);
    try {
      const run = await evaluation.runEvaluation({
        dataset_id: selectedDataset,
        prompt_id: selectedPrompt,
        model_key: selectedModel,
        scoring_method: scoringMethod,
      });
      router.push(`/dashboard/evaluation/runs/${run.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
      setRunning(false);
    }
  };

  const selectedDatasetInfo = datasets.find((d) => d.id === selectedDataset);
  const selectedPromptInfo = promptList.find((p) => p.id === selectedPrompt);

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center gap-3">
          <Link
            href="/dashboard/evaluation"
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Evaluation
          </Link>
          <span className="text-gray-300">/</span>
          <h1 className="text-sm font-semibold text-gray-900">New Evaluation Run</h1>
        </div>

        <div className="flex flex-col gap-4">
          {/* Dataset */}
          <div className="rounded-xl border bg-white p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              1. Select Dataset
            </label>
            {datasets.length === 0 ? (
              <p className="text-sm text-gray-400">
                No datasets yet.{" "}
                <Link href="/dashboard/evaluation" className="text-blue-600 hover:underline">
                  Upload one first →
                </Link>
              </p>
            ) : (
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">— Select a dataset —</option>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.row_count} questions)
                  </option>
                ))}
              </select>
            )}
            {selectedDatasetInfo && (
              <p className="mt-2 text-xs text-gray-400">
                {selectedDatasetInfo.row_count} questions will be evaluated
              </p>
            )}
          </div>

          {/* Prompt */}
          <div className="rounded-xl border bg-white p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              2. Select Prompt
            </label>
            {promptList.length === 0 ? (
              <p className="text-sm text-gray-400">
                No prompts yet.{" "}
                <Link href="/dashboard/prompts" className="text-blue-600 hover:underline">
                  Create one first →
                </Link>
              </p>
            ) : (
              <select
                value={selectedPrompt}
                onChange={(e) => setSelectedPrompt(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              >
                {promptList.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} (v{p.latest_version?.version_number || 1})
                  </option>
                ))}
              </select>
            )}
            {selectedPromptInfo?.latest_version && (
              <div className="mt-2 rounded-lg bg-gray-50 p-3">
                <p className="text-xs text-gray-500 font-mono line-clamp-3">
                  {selectedPromptInfo.latest_version.content}
                </p>
                {selectedPromptInfo.latest_version.variables.length > 0 && (
                  <p className="mt-1 text-xs text-purple-500">
                    Variables: {selectedPromptInfo.latest_version.variables.map((v) => `{{${v}}}`).join(", ")}
                    {" "}— <span className="text-gray-400">
                      {"{{question}}"} will be auto-filled from dataset
                    </span>
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Model */}
          <div className="rounded-xl border bg-white p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              3. Select Model
            </label>
            <div className="flex flex-col gap-2">
              {models.map((m) => (
                <label
                  key={m.key}
                  className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${
                    selectedModel === m.key
                      ? "border-blue-500 bg-blue-50"
                      : "hover:bg-gray-50"
                  }`}
                >
                  <input
                    type="radio"
                    name="model"
                    value={m.key}
                    checked={selectedModel === m.key}
                    onChange={() => setSelectedModel(m.key)}
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">{m.name}</p>
                    <p className="text-xs text-gray-400 capitalize">{m.provider}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Scoring method */}
          <div className="rounded-xl border bg-white p-5 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              4. Scoring Method
            </label>
            <div className="flex flex-col gap-2">
              {SCORING_METHODS.map((method) => (
                <label
                  key={method.id}
                  className={`flex items-start gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${
                    scoringMethod === method.id
                      ? "border-blue-500 bg-blue-50"
                      : "hover:bg-gray-50"
                  }`}
                >
                  <input
                    type="radio"
                    name="scoring"
                    value={method.id}
                    checked={scoringMethod === method.id}
                    onChange={() => setScoringMethod(method.id)}
                    className="mt-0.5"
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{method.label}</p>
                    <p className="text-xs text-gray-400">{method.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</p>
          )}

          {/* Run button */}
          <button
            onClick={handleRun}
            disabled={running || !selectedDataset || !selectedPrompt}
            className="rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 shadow-sm"
          >
            {running
              ? `Running evaluation on ${selectedDatasetInfo?.row_count || "..."} questions...`
              : "▶ Run Evaluation"}
          </button>

          {running && (
            <div className="rounded-xl border bg-white p-6 text-center shadow-sm">
              <div className="animate-pulse">
                <p className="text-gray-500 text-sm">
                  Evaluating all questions and scoring with {scoringMethod} method...
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  This may take a minute depending on dataset size.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
