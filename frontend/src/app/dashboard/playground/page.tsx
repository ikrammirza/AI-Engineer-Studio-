"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { playground, prompts, type ModelDefinition, type ModelResult, type Prompt } from "@/lib/api";

const PROVIDER_COLORS: Record<string, string> = {
  groq: "bg-orange-100 text-orange-700",
  openai: "bg-green-100 text-green-700",
  anthropic: "bg-purple-100 text-purple-700",
};

function ModelResultCard({ result }: { result: ModelResult }) {
  return (
    <div className={`rounded-xl border bg-white shadow-sm flex flex-col ${result.error ? "border-red-200" : ""}`}>
      {/* Card header */}
      <div className="border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PROVIDER_COLORS[result.provider] || "bg-gray-100 text-gray-600"}`}>
            {result.provider}
          </span>
          <span className="text-sm font-semibold text-gray-800">{result.model_name}</span>
        </div>
        {result.error ? (
          <span className="text-xs text-red-500">Error</span>
        ) : (
          <span className="text-xs text-green-600 font-medium">{result.latency_ms}ms</span>
        )}
      </div>

      {/* Output */}
      <div className="flex-1 px-4 py-3">
        {result.error ? (
          <p className="text-sm text-red-500">{result.error}</p>
        ) : (
          <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {result.output}
          </p>
        )}
      </div>

      {/* Stats footer */}
      {!result.error && (
        <div className="border-t px-4 py-2 flex items-center gap-4 bg-gray-50 rounded-b-xl">
          <div className="text-center">
            <p className="text-xs text-gray-400">Input tokens</p>
            <p className="text-xs font-semibold text-gray-700">{result.input_tokens}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-400">Output tokens</p>
            <p className="text-xs font-semibold text-gray-700">{result.output_tokens}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-400">Cost</p>
            <p className="text-xs font-semibold text-gray-700">
              ${result.cost_usd < 0.0001 ? "<0.0001" : result.cost_usd.toFixed(4)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-400">Latency</p>
            <p className="text-xs font-semibold text-gray-700">{result.latency_ms}ms</p>
          </div>
        </div>
      )}
    </div>
  );
}

function WinnerBadge({ results }: { results: ModelResult[] }) {
  const valid = results.filter((r) => !r.error);
  if (valid.length < 2) return null;

  const fastest = valid.reduce((a, b) => (a.latency_ms < b.latency_ms ? a : b));
  const cheapest = valid.reduce((a, b) => (a.cost_usd < b.cost_usd ? a : b));

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Summary</h3>
      <div className="flex gap-6">
        <div>
          <p className="text-xs text-gray-400">Fastest</p>
          <p className="text-sm font-semibold text-green-600">
            {fastest.model_name} ({fastest.latency_ms}ms)
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Cheapest</p>
          <p className="text-sm font-semibold text-blue-600">
            {cheapest.model_name} (${cheapest.cost_usd.toFixed(4)})
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Total cost</p>
          <p className="text-sm font-semibold text-gray-700">
            ${results.reduce((a, b) => a + b.cost_usd, 0).toFixed(4)}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function PlaygroundPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const promptId = searchParams.get("prompt");

  const [availableModels, setAvailableModels] = useState<ModelDefinition[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>(["groq/llama-3.3-70b"]);
  const [systemPrompt, setSystemPrompt] = useState("You are a helpful assistant.");
  const [userPrompt, setUserPrompt] = useState("");
  const [results, setResults] = useState<ModelResult[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedPrompts, setSavedPrompts] = useState<Prompt[]>([]);
  const [selectedSavedPrompt, setSelectedSavedPrompt] = useState<string>("");

  useEffect(() => {
    playground.models()
      .then(setAvailableModels)
      .catch(() => router.push("/login"));

    prompts.list()
      .then(setSavedPrompts)
      .catch(() => {});
  }, [router]);

  // Load prompt from URL param (when coming from prompt editor)
  useEffect(() => {
    if (promptId) {
      prompts.get(promptId).then((p) => {
        if (p.latest_version) {
          setUserPrompt(p.latest_version.content);
          setSelectedSavedPrompt(promptId);
        }
      }).catch(() => {});
    }
  }, [promptId]);

  const toggleModel = (key: string) => {
    setSelectedModels((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const handleRun = async () => {
    if (!userPrompt.trim() || selectedModels.length === 0) return;
    setRunning(true);
    setError(null);
    setResults([]);
    try {
      const response = await playground.run({
        prompt: userPrompt,
        system: systemPrompt,
        model_keys: selectedModels,
      });
      setResults(response.results);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setRunning(false);
    }
  };

  const handleLoadSavedPrompt = (id: string) => {
    setSelectedSavedPrompt(id);
    const p = savedPrompts.find((p) => p.id === id);
    if (p?.latest_version) {
      setUserPrompt(p.latest_version.content);
    }
  };

  const groqModels = availableModels.filter((m) => m.provider === "groq");
  const otherModels = availableModels.filter((m) => m.provider !== "groq");

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
            ← Dashboard
          </Link>
          <span className="text-gray-300">/</span>
          <h1 className="text-sm font-semibold text-gray-900">Model Playground</h1>
        </div>
        <p className="text-xs text-gray-400">
          Run prompts across multiple models simultaneously
        </p>
      </div>

      <div className="mx-auto max-w-7xl p-6 flex gap-6">
        {/* Left panel — controls */}
        <div className="w-80 flex-shrink-0 flex flex-col gap-4">

          {/* Load saved prompt */}
          {savedPrompts.length > 0 && (
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Load Saved Prompt
              </label>
              <select
                value={selectedSavedPrompt}
                onChange={(e) => handleLoadSavedPrompt(e.target.value)}
                className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">— Select a prompt —</option>
                {savedPrompts.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Model selector */}
          <div className="rounded-xl border bg-white p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Select Models</h2>

            {groqModels.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-orange-600 font-medium mb-2">Groq (Free)</p>
                {groqModels.map((m) => (
                  <label key={m.key} className="flex items-center gap-2 py-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedModels.includes(m.key)}
                      onChange={() => toggleModel(m.key)}
                      className="rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800">{m.name}</p>
                      <p className="text-xs text-gray-400">
                        ${m.input_cost_per_1k}/1k in · ${m.output_cost_per_1k}/1k out
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            )}

            {otherModels.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 font-medium mb-2">Other (Requires API key)</p>
                {otherModels.map((m) => (
                  <label key={m.key} className="flex items-center gap-2 py-1.5 cursor-pointer opacity-60">
                    <input
                      type="checkbox"
                      checked={selectedModels.includes(m.key)}
                      onChange={() => toggleModel(m.key)}
                      className="rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800">{m.name}</p>
                      <p className="text-xs text-gray-400 capitalize">{m.provider}</p>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* System prompt */}
          <div className="rounded-xl border bg-white p-4 shadow-sm">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              System Prompt
            </label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={3}
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          {/* Run button */}
          <button
            onClick={handleRun}
            disabled={running || selectedModels.length === 0 || !userPrompt.trim()}
            className="rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 shadow-sm"
          >
            {running
              ? `Running across ${selectedModels.length} model${selectedModels.length !== 1 ? "s" : ""}...`
              : `▶ Run on ${selectedModels.length} model${selectedModels.length !== 1 ? "s" : ""}`}
          </button>

          {error && (
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</p>
          )}
        </div>

        {/* Right panel — prompt + results */}
        <div className="flex-1 flex flex-col gap-4">
          {/* User prompt input */}
          <div className="rounded-xl border bg-white shadow-sm">
            <div className="border-b px-4 py-3">
              <span className="text-sm font-semibold text-gray-700">User Prompt</span>
            </div>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              rows={6}
              placeholder="Enter your prompt here... or load a saved prompt from the left panel."
              className="w-full px-4 py-3 text-sm text-gray-800 outline-none resize-none font-mono rounded-b-xl"
            />
          </div>

          {/* Loading state */}
          {running && (
            <div className="rounded-xl border bg-white p-8 text-center shadow-sm">
              <div className="animate-pulse">
                <p className="text-gray-500 text-sm">
                  Running prompt across {selectedModels.length} model{selectedModels.length !== 1 ? "s" : ""} in parallel...
                </p>
              </div>
            </div>
          )}

          {/* Results */}
          {results.length > 0 && !running && (
            <>
              <WinnerBadge results={results} />
              <div className={`grid gap-4 ${results.length === 1 ? "grid-cols-1" : results.length === 2 ? "grid-cols-2" : "grid-cols-3"}`}>
                {results.map((result) => (
                  <ModelResultCard key={result.model_key} result={result} />
                ))}
              </div>
            </>
          )}

          {/* Empty state */}
          {results.length === 0 && !running && (
            <div className="rounded-xl border bg-white p-12 text-center shadow-sm">
              <p className="text-gray-400 text-sm">
                Select models, write a prompt, and hit Run to see results side by side.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
