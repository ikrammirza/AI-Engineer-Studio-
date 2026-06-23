"use client";

import { diffLines, Change } from "diff";

type Props = {
  oldContent: string;
  newContent: string;
  oldLabel?: string;
  newLabel?: string;
};

export default function DiffViewer({ oldContent, newContent, oldLabel = "Before", newLabel = "After" }: Props) {
  const changes: Change[] = diffLines(oldContent, newContent);

  return (
    <div className="rounded-lg border overflow-hidden text-sm font-mono">
      <div className="flex border-b bg-gray-50 text-xs text-gray-500">
        <div className="flex-1 px-4 py-2 border-r">{oldLabel}</div>
        <div className="flex-1 px-4 py-2">{newLabel}</div>
      </div>
      <div className="max-h-96 overflow-y-auto">
        {changes.map((change, i) => {
          const lines = change.value.split("\n").filter((_, idx, arr) =>
            idx < arr.length - 1 || change.value.endsWith("\n") ? true : idx < arr.length - 1
          );
          return lines.map((line, j) => (
            <div
              key={`${i}-${j}`}
              className={`flex px-4 py-0.5 ${
                change.added
                  ? "bg-green-50 text-green-800"
                  : change.removed
                  ? "bg-red-50 text-red-800"
                  : "text-gray-700"
              }`}
            >
              <span className="w-4 mr-3 select-none text-gray-400">
                {change.added ? "+" : change.removed ? "−" : " "}
              </span>
              <span className="whitespace-pre-wrap break-all">{line}</span>
            </div>
          ));
        })}
      </div>
    </div>
  );
}
