"use client";

import { useEffect, useState } from "react";

const HEALTH_URL = "http://localhost:8000/health";

type ConnectionStatus = "checking" | "connected" | "disconnected";

export default function BackendStatus() {
  const [status, setStatus] = useState<ConnectionStatus>("checking");

  useEffect(() => {
    let cancelled = false;

    async function checkBackend() {
      try {
        const response = await fetch(HEALTH_URL);
        const data = await response.json();

        if (cancelled) {
          return;
        }

        if (response.ok && data.status === "ok") {
          setStatus("connected");
        } else {
          setStatus("disconnected");
        }
      } catch {
        if (!cancelled) {
          setStatus("disconnected");
        }
      }
    }

    checkBackend();
    const intervalId = window.setInterval(checkBackend, 4000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const label =
    status === "checking"
      ? "Backend: Checking..."
      : status === "connected"
        ? "Backend: Connected ✓"
        : "Backend: Disconnected";

  return (
    <p className="mb-8 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
      {label}
    </p>
  );
}
