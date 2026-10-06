"use client";

import React from "react";
import { TopologyType, TrafficPatternType } from "../types";

interface ConfigPanelProps {
  nodes: number;
  setNodes: (n: number) => void;
  topology: TopologyType;
  setTopology: (t: TopologyType) => void;
  capacity: number;
  setCapacity: (c: number) => void;
  pattern: TrafficPatternType;
  setPattern: (p: TrafficPatternType) => void;
  onRunOptimization: () => void;
  onRunSimulation: () => void;
  isOptimizing: boolean;
  isSimulating: boolean;
  isBackendConnected: boolean;
}

export default function ConfigPanel({
  nodes,
  setNodes,
  topology,
  setTopology,
  capacity,
  setCapacity,
  pattern,
  setPattern,
  onRunOptimization,
  onRunSimulation,
  isOptimizing,
  isSimulating,
  isBackendConnected,
}: ConfigPanelProps) {
  const isRecommended = nodes === 5 && topology === "ring" && pattern === "hotspot";

  const handleApplyPreset = () => {
    setNodes(5);
    setTopology("ring");
    setCapacity(10);
    setPattern("hotspot");
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Network Configuration</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure topology and traffic scenario for evaluation
          </p>
        </div>
        {!isRecommended && (
          <button
            type="button"
            onClick={handleApplyPreset}
            className="text-xs font-medium text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-100 transition-colors"
          >
            Load 5-Node Ring Preset
          </button>
        )}
      </div>

      <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Topology */}
        <div>
          <label htmlFor="topology" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Topology
          </label>
          <select
            id="topology"
            value={topology}
            onChange={(e) => setTopology(e.target.value as TopologyType)}
            disabled={isOptimizing || isSimulating}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-xs focus:border-indigo-500 focus:outline-hidden focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-50 disabled:text-slate-400"
          >
            <option value="ring">Ring (5 nodes trained)</option>
            <option value="mesh">Mesh (Full interconnect)</option>
            <option value="line">Line (Linear chain)</option>
            <option value="star">Star (Central hub)</option>
            <option value="bus">Bus (Shared line)</option>
          </select>
        </div>

        {/* Number of Nodes */}
        <div>
          <label htmlFor="nodes" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Number of Nodes
          </label>
          <input
            id="nodes"
            type="number"
            min={2}
            max={20}
            value={nodes}
            onChange={(e) => setNodes(Math.max(2, parseInt(e.target.value) || 2))}
            disabled={isOptimizing || isSimulating}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-xs focus:border-indigo-500 focus:outline-hidden focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-50 disabled:text-slate-400"
          />
        </div>

        {/* Link Capacity */}
        <div>
          <label htmlFor="capacity" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Link Capacity (Gbps)
          </label>
          <input
            id="capacity"
            type="number"
            min={1}
            max={100}
            step={1}
            value={capacity}
            onChange={(e) => setCapacity(Math.max(1, parseFloat(e.target.value) || 1))}
            disabled={isOptimizing || isSimulating}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-xs focus:border-indigo-500 focus:outline-hidden focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-50 disabled:text-slate-400"
          />
        </div>

        {/* Traffic Pattern */}
        <div>
          <label htmlFor="pattern" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Traffic Pattern
          </label>
          <select
            id="pattern"
            value={pattern}
            onChange={(e) => setPattern(e.target.value as TrafficPatternType)}
            disabled={isOptimizing || isSimulating}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-xs focus:border-indigo-500 focus:outline-hidden focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-50 disabled:text-slate-400"
          >
            <option value="hotspot">Hotspot (Asymmetric Bottleneck)</option>
            <option value="uniform">Uniform (All-to-All)</option>
          </select>
        </div>
      </div>

      {/* Model status highlight */}
      <div className="mt-4 rounded-lg bg-indigo-50/70 border border-indigo-100/80 px-3.5 py-2.5 text-xs text-indigo-900 flex items-start gap-2">
        <span className="text-indigo-600 font-bold shrink-0 mt-0.5">⚡</span>
        <div>
          <span className="font-semibold">Trained PPO Model Available:</span>{" "}
          <span className="font-mono text-indigo-800">ppo_ring_5nodes_hotspot.zip</span>.
          Select <strong className="font-medium">5-node Ring</strong> with <strong className="font-medium">Hotspot</strong> traffic to see PPO eliminate bottleneck packet drops by 65%+.
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex flex-col sm:flex-row gap-3">
        <button
          type="button"
          onClick={onRunOptimization}
          disabled={isOptimizing || isSimulating || !isBackendConnected}
          className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-slate-300 transition-colors"
        >
          {isOptimizing ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              Optimizing via PPO...
            </>
          ) : (
            <>
              <span>⚡</span> Run AI Optimization
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onRunSimulation}
          disabled={isOptimizing || isSimulating || !isBackendConnected}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-xs hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400 transition-colors"
        >
          {isSimulating ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-700" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
              </svg>
              Simulating...
            </>
          ) : (
            "Run Simulation"
          )}
        </button>
      </div>
    </div>
  );
}
