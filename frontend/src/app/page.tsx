"use client";

import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  database: string;
};

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
      .then((res) => res.json())
      .then((data) => setHealth(data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-24">
      <h1 className="text-3xl font-bold">AI Engineer Studio</h1>

      {error && (
        <p className="text-red-500">Error reaching backend: {error}</p>
      )}

      {health ? (
        <div className="rounded-lg border p-4 text-center">
          <p>
            Backend status:{" "}
            <span className="font-mono text-green-600">{health.status}</span>
          </p>
          <p>
            Database:{" "}
            <span className="font-mono text-green-600">
              {health.database}
            </span>
          </p>
        </div>
      ) : (
        !error && <p>Checking backend connection...</p>
      )}
    </main>
  );
}
