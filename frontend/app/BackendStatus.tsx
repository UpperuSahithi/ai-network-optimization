"use client";

import { useEffect, useState } from "react";

const HEALTH_URL = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/health`
  : "http://localhost:8000/health";

export type ConnectionStatus = "checking" | "connected" | "disconnected";

interface BackendStatusProps {
  onStatusChange?: (status: ConnectionStatus) => void;
}

export default function BackendStatus({ onStatusChange }: BackendStatusProps) {
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
          onStatusChange?.("connected");
        } else {
          setStatus("disconnected");
          onStatusChange?.("disconnected");
        }
      } catch {
        if (!cancelled) {
          setStatus("disconnected");
          onStatusChange?.("disconnected");
        }
      }
    }

    checkBackend();
    const intervalId = window.setInterval(checkBackend, 4000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [onStatusChange]);

  const isConnected = status === "connected";
  const isChecking = status === "checking";

  return (
    <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 shadow-xs">
      <span
        className={`h-2 w-2 rounded-full ${
          isChecking
            ? "bg-amber-400 animate-pulse"
            : isConnected
              ? "bg-emerald-500"
              : "bg-rose-500"
        }`}
      />
      <span className="font-medium">
        {isChecking
          ? "Backend: Checking..."
          : isConnected
            ? "Backend: Connected (FastAPI :8000)"
            : "Backend: Disconnected (FastAPI :8000)"}
      </span>
    </div>
  );
}
