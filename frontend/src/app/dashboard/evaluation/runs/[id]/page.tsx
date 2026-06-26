"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { evaluation, type EvaluationRun, type QuestionResult } from "@/lib/api";

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${
            pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-gray-600 w-8">{pct}%</span>
    </div>
  );
}

function QuestionCard({ result, index }: { result: QuestionResult; index: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      className={`rounded-xl border p-4 shadow-sm cursor-pointer transition-colors ${
        result.passed ? "bg-white" : "bg-red-50 border-red-100"
      }`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-3">
        <span className={`mt-0.5 text-lg flex-shrink-0 ${result.passed ? "text-green-500" : "text-red-500"}`}>
          {result.passed ? "✓" : "✗"}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-gray-800 truncate">
              Q{index + 1}: {result.question}
            </p>
            <span className="text-xs font-mono text-gray-500 flex-shrink-0">
              {result.score.toFixed(2)}
            </span>
          </div>
          <ScoreBar score={result.score} />

          {expanded && (
            <div className="mt-3 flex flex-col gap-2">
              <div className="rounded-lg bg-green-50 p-3">
                <p className="text-xs font-medium text-green-700 mb-1">Expected</p>
                <p className="text-sm text-gray-700">{result.expected}</p>
              </div>
              <div className={`rounded-lg p-3 ${result.passed ? "bg-blue-50" : "bg-red-50"}`}>
                <p className={`text-xs font-medium mb-1 ${result.passed ? "text-blue-700" : "text-red-700"}`}>
                  Actual
                </p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.actual || "— no output —"}</p>
              </div>
              {result.reasoning && (
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-xs font-medium text-gray-500 mb-1">Judge reasoning</p>
                  <p className="text-xs text-gray-600">{result.reasoning}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function RunResultsPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const [run, setRun] = useState<EvaluationRun | null>(null);

  useEffect(() => {
    evaluation.getRun(id)
      .then(setRun)
      .catch(() => router.push("/dashboard/evaluation"));
  }, [id, router]);

  if (!run) return <p className="p-8 text-gray-500">Loading results...</p>;

  const passed = run.results.filter((r) => r.passed).length;
  const failed = run.results.length - passed;
  const accuracyPct = run.accuracy != null ? Math.round(run.accuracy * 100) : 0;

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-3xl">
        {/* Header */}
        <div className="mb-6 flex items-center gap-3">
          <Link
            href="/dashboard/evaluation"
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Evaluation
          </Link>
          <span className="text-gray-300">/</span>
          <h1 className="text-sm font-semibold text-gray-900">Run Results</h1>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="rounded-xl border bg-white p-4 shadow-sm text-center">
            <p className="text-3xl font-bold text-gray-900">{accuracyPct}%</p>
            <p className="text-xs text-gray-400 mt-1">Accuracy</p>
          </div>
          <div className="rounded-xl border bg-white p-4 shadow-sm text-center">
            <p className="text-3xl font-bold text-gray-900">
              {run.avg_score?.toFixed(2) ?? "—"}
            </p>
            <p className="text-xs text-gray-400 mt-1">Avg Score</p>
          </div>
          <div className="rounded-xl border bg-white p-4 shadow-sm text-center">
            <p className="text-3xl font-bold text-green-600">{passed}</p>
            <p className="text-xs text-gray-400 mt-1">Passed</p>
          </div>
          <div className="rounded-xl border bg-white p-4 shadow-sm text-center">
            <p className="text-3xl font-bold text-red-500">{failed}</p>
            <p className="text-xs text-gray-400 mt-1">Failed</p>
          </div>
        </div>

        {/* Run metadata */}
        <div className="rounded-xl border bg-white p-4 shadow-sm mb-6">
          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div>
              <span className="text-xs text-gray-400 block">Model</span>
              <span className="font-medium">{run.model_key.split("/")[1]}</span>
            </div>
            <div>
              <span className="text-xs text-gray-400 block">Scoring</span>
              <span className="font-medium capitalize">{run.scoring_method}</span>
            </div>
            <div>
              <span className="text-xs text-gray-400 block">Prompt version</span>
              <span className="font-medium">v{run.prompt_version_number ?? "—"}</span>
            </div>
            <div>
              <span className="text-xs text-gray-400 block">Questions</span>
              <span className="font-medium">{run.results.length}</span>
            </div>
            <div>
              <span className="text-xs text-gray-400 block">Completed</span>
              <span className="font-medium">
                {run.completed_at
                  ? new Date(run.completed_at).toLocaleString()
                  : "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Accuracy bar */}
        <div className="rounded-xl border bg-white p-4 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">Overall Accuracy</span>
            <span className="text-sm font-bold text-gray-900">{accuracyPct}%</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                accuracyPct >= 70 ? "bg-green-500" : accuracyPct >= 40 ? "bg-yellow-500" : "bg-red-500"
              }`}
              style={{ width: `${accuracyPct}%` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-400">0%</span>
            <span className="text-xs text-gray-400">100%</span>
          </div>
        </div>

        {/* Per-question results */}
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">
            Per-Question Results
          </h2>
          <p className="text-xs text-gray-400">Click any row to expand</p>
        </div>
        <div className="flex flex-col gap-2">
          {run.results.map((result, i) => (
            <QuestionCard key={i} result={result} index={i} />
          ))}
        </div>

        {/* Actions */}
        <div className="mt-6 flex gap-3">
          <Link
            href="/dashboard/evaluation/run"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Run Another Evaluation
          </Link>
          <Link
            href="/dashboard/evaluation"
            className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
          >
            Back to Evaluation
          </Link>
        </div>
      </div>
    </main>
  );
}
