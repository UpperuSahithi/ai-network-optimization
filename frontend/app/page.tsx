"use client";

import { useState } from "react";
import BackendStatus, { ConnectionStatus } from "./BackendStatus";
import ConfigPanel from "./components/ConfigPanel";
import MetricsTable from "./components/MetricsTable";
import AIExplanation from "./components/AIExplanation";
import TopologyView from "./components/TopologyView";
import {
  TopologyType,
  TrafficPatternType,
  OptimizeResponse,
  SimulationResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [nodes, setNodes] = useState<number>(5);
  const [topology, setTopology] = useState<TopologyType>("ring");
  const [capacity, setCapacity] = useState<number>(10);
  const [pattern, setPattern] = useState<TrafficPatternType>("hotspot");

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("checking");
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [optimizationResult, setOptimizationResult] = useState<OptimizeResponse | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);

  const handleRunOptimization = async () => {
    setIsOptimizing(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE}/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          number_of_nodes: nodes,
          topology: topology,
          link_capacity: capacity,
          traffic_pattern: pattern,
        }),
      });

      const data = await response.json().catch(() => ({ detail: `Server error (${response.status})` }));

      if (!response.ok) {
        let msg = `Server error (${response.status})`;
        if (typeof data.detail === "string") {
          msg = data.detail;
        } else if (Array.isArray(data.detail)) {
          msg = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(", ");
        } else if (data.detail && typeof data.detail === "object") {
          msg = JSON.stringify(data.detail);
        }
        throw new Error(msg);
      }

      setOptimizationResult(data as OptimizeResponse);
      setSimulationResult(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to run AI optimization";
      setErrorMessage(msg);
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          number_of_nodes: nodes,
          topology: topology,
          link_capacity: capacity,
          traffic_load: pattern === "hotspot" ? 50 : 25,
        }),
      });

      const data = await response.json().catch(() => ({ detail: `Simulation error (${response.status})` }));

      if (!response.ok) {
        let msg = `Simulation error (${response.status})`;
        if (typeof data.detail === "string") {
          msg = data.detail;
        } else if (Array.isArray(data.detail)) {
          msg = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(", ");
        } else if (data.detail && typeof data.detail === "object") {
          msg = JSON.stringify(data.detail);
        }
        throw new Error(msg);
      }

      setSimulationResult(data as SimulationResponse);
      setOptimizationResult(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to run simulation";
      setErrorMessage(msg);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900 pb-16">
      {/* Top Navigation / Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-10 shadow-xs">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold shadow-xs">
              ⚡
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 tracking-tight leading-tight">
                AI Network Optimization
              </h1>
              <p className="text-xs text-slate-500">
                Reinforcement Learning (PPO) Dynamic Traffic Routing Dashboard
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <BackendStatus onStatusChange={setConnectionStatus} />
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-6">
        {/* Error Notification */}
        {errorMessage && (
          <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 shadow-xs">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <span className="text-rose-600 text-base font-bold shrink-0 mt-0.5">⚠️</span>
                <div>
                  <h4 className="text-sm font-semibold text-rose-900">Optimization Request Error</h4>
                  <p className="text-xs text-rose-700 mt-0.5">{errorMessage}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                className="text-xs font-semibold text-rose-600 hover:text-rose-800"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Configuration & Topology */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <ConfigPanel
              nodes={nodes}
              setNodes={setNodes}
              topology={topology}
              setTopology={setTopology}
              capacity={capacity}
              setCapacity={setCapacity}
              pattern={pattern}
              setPattern={setPattern}
              onRunOptimization={handleRunOptimization}
              onRunSimulation={handleRunSimulation}
              isOptimizing={isOptimizing}
              isSimulating={isSimulating}
              isBackendConnected={connectionStatus === "connected"}
            />

            <TopologyView
              nodesCount={nodes}
              topology={topology}
              optimizationResult={optimizationResult}
              simulationResult={simulationResult}
            />
          </div>

          {/* Right Column: Comparative Metrics & AI Explanation */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            <MetricsTable
              optimizationResult={optimizationResult}
              simulationResult={simulationResult}
            />

            <AIExplanation optimizationResult={optimizationResult} />
          </div>
        </div>
      </div>
    </main>
  );
}
