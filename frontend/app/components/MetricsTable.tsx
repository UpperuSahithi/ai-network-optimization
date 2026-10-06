"use client";

import React from "react";
import { OptimizeResponse, SimulationResponse } from "../types";

interface MetricsTableProps {
  optimizationResult: OptimizeResponse | null;
  simulationResult: SimulationResponse | null;
}

export default function MetricsTable({
  optimizationResult,
  simulationResult,
}: MetricsTableProps) {
  if (!optimizationResult && !simulationResult) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-8 text-center text-slate-500">
        <p className="font-medium text-sm">No evaluation results yet</p>
        <p className="text-xs text-slate-400 mt-1">
          Click <strong className="text-slate-600">Run AI Optimization</strong> to compare PPO vs Static Shortest-Path routing, or <strong className="text-slate-600">Run Simulation</strong> for baseline metrics.
        </p>
      </div>
    );
  }

  // Simulation-only result view
  if (simulationResult && !optimizationResult) {
    const m = simulationResult.metrics;
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Standard Simulation Metrics</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Static Shortest-Path routing (Dijkstra, unit link weights)
            </p>
          </div>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
            Baseline Run
          </span>
        </div>

        <div className="mt-5 grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="rounded-lg bg-slate-50 p-3 text-center border border-slate-100">
            <span className="block text-xs font-medium text-slate-500">Throughput</span>
            <span className="mt-1 block text-lg font-bold text-slate-900">{m.throughput.toFixed(2)}</span>
            <span className="text-[10px] text-slate-400">Gbps</span>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 text-center border border-slate-100">
            <span className="block text-xs font-medium text-slate-500">Avg Latency</span>
            <span className="mt-1 block text-lg font-bold text-slate-900">{m.latency.toFixed(2)}</span>
            <span className="text-[10px] text-slate-400">hops / ms</span>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 text-center border border-slate-100">
            <span className="block text-xs font-medium text-slate-500">Packet Loss</span>
            <span className={`mt-1 block text-lg font-bold ${m.packet_loss > 0 ? "text-rose-600" : "text-emerald-600"}`}>
              {(m.packet_loss * 100).toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-400">dropped ratio</span>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 text-center border border-slate-100">
            <span className="block text-xs font-medium text-slate-500">Congestion</span>
            <span className={`mt-1 block text-lg font-bold ${m.congestion > 0 ? "text-amber-600" : "text-emerald-600"}`}>
              {(m.congestion * 100).toFixed(0)}%
            </span>
            <span className="text-[10px] text-slate-400">overloaded links</span>
          </div>
          <div className="rounded-lg bg-slate-50 p-3 text-center border border-slate-100 col-span-2 sm:col-span-1">
            <span className="block text-xs font-medium text-slate-500">Avg Utilization</span>
            <span className="mt-1 block text-lg font-bold text-slate-900">{(m.link_utilization * 100).toFixed(0)}%</span>
            <span className="text-[10px] text-slate-400">capacity used</span>
          </div>
        </div>
      </div>
    );
  }

  // AI Optimization comparison view
  const { baseline, ppo, improvement } = optimizationResult!;

  const rows = [
    {
      name: "Throughput",
      unit: "Gbps",
      baseline: baseline.throughput.toFixed(2),
      ppo: ppo.throughput.toFixed(2),
      diffPct: improvement.throughput_percent,
      isBetter: ppo.throughput > baseline.throughput,
      isEqual: Math.abs(ppo.throughput - baseline.throughput) < 0.01,
      badgeText: improvement.throughput_percent >= 0 ? `+${improvement.throughput_percent}%` : `${improvement.throughput_percent}%`,
      description: "Total delivered traffic across network demands (higher is better)",
    },
    {
      name: "Latency",
      unit: "hops",
      baseline: baseline.latency.toFixed(2),
      ppo: ppo.latency.toFixed(2),
      diffPct: improvement.latency_percent,
      isBetter: ppo.latency <= baseline.latency,
      isEqual: Math.abs(ppo.latency - baseline.latency) < 0.01,
      badgeText: improvement.latency_percent >= 0 ? `-${improvement.latency_percent}%` : `+${Math.abs(improvement.latency_percent)}%`,
      description: "Average propagation path length / latency (lower is better)",
    },
    {
      name: "Packet Loss",
      unit: "%",
      baseline: `${(baseline.packet_loss * 100).toFixed(2)}%`,
      ppo: `${(ppo.packet_loss * 100).toFixed(2)}%`,
      diffPct: improvement.packet_loss_reduction_percent,
      isBetter: ppo.packet_loss < baseline.packet_loss,
      isEqual: Math.abs(ppo.packet_loss - baseline.packet_loss) < 0.001,
      badgeText: improvement.packet_loss_reduction_percent > 0 ? `↓ ${improvement.packet_loss_reduction_percent}% reduction` : "0%",
      description: "Fraction of traffic dropped due to capacity overflow (lower is better)",
    },
    {
      name: "Congestion",
      unit: "% links",
      baseline: `${(baseline.congestion * 100).toFixed(1)}%`,
      ppo: `${(ppo.congestion * 100).toFixed(1)}%`,
      diffPct: null,
      isBetter: ppo.congestion <= baseline.congestion,
      isEqual: Math.abs(ppo.congestion - baseline.congestion) < 0.01,
      badgeText: ppo.congestion < baseline.congestion ? "Decreased" : ppo.congestion === baseline.congestion ? "Neutral" : "Diversion load",
      description: "Fraction of links whose traffic load exceeds physical capacity",
    },
    {
      name: "Link Utilization",
      unit: "avg ratio",
      baseline: `${(baseline.link_utilization * 100).toFixed(1)}%`,
      ppo: `${(ppo.link_utilization * 100).toFixed(1)}%`,
      diffPct: null,
      isBetter: true,
      isEqual: Math.abs(ppo.link_utilization - baseline.link_utilization) < 0.01,
      badgeText: `${(ppo.link_utilization * 100).toFixed(0)}% avg`,
      description: "Average capacity utilization across active directional links",
    },
    {
      name: "Reward",
      unit: "score",
      baseline: baseline.reward !== undefined ? baseline.reward.toFixed(2) : "N/A",
      ppo: ppo.reward !== undefined ? ppo.reward.toFixed(2) : "N/A",
      diffPct: improvement.reward_percent,
      isBetter: (ppo.reward ?? 0) > (baseline.reward ?? 0),
      isEqual: Math.abs((ppo.reward ?? 0) - (baseline.reward ?? 0)) < 0.1,
      badgeText: improvement.reward_percent >= 0 ? `+${improvement.reward_percent}%` : `${improvement.reward_percent}%`,
      description: "PPO objective composite (rewards throughput, penalizes drops & latency)",
    },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Optimization Results Comparison</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Static Shortest-Path Baseline (weights = 1.0) vs. Trained PPO Agent
          </p>
        </div>
        <div className="flex items-center gap-2">
          {improvement.packet_loss_reduction_percent > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
              <span>✓</span> {improvement.packet_loss_reduction_percent}% Loss Reduced
            </span>
          )}
          {improvement.throughput_percent > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-800">
              <span>↑</span> +{improvement.throughput_percent}% Throughput
            </span>
          )}
        </div>
      </div>

      {/* Comparison Table */}
      <div className="mt-5 overflow-x-auto">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-3">Metric</th>
              <th className="py-3 px-3 text-right">Static Routing</th>
              <th className="py-3 px-3 text-right">PPO Agent</th>
              <th className="py-3 px-3 text-right">Improvement</th>
              <th className="py-3 px-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((row) => (
              <tr key={row.name} className="hover:bg-slate-50/80 transition-colors">
                <td className="py-3.5 px-3">
                  <div className="font-medium text-slate-900">{row.name}</div>
                  <div className="text-[11px] text-slate-400">{row.description}</div>
                </td>
                <td className="py-3.5 px-3 text-right font-mono text-slate-600">
                  {row.baseline}
                </td>
                <td className="py-3.5 px-3 text-right font-mono font-semibold text-indigo-950">
                  {row.ppo}
                </td>
                <td className="py-3.5 px-3 text-right font-mono text-xs font-semibold">
                  {row.badgeText}
                </td>
                <td className="py-3.5 px-3 text-center">
                  {row.isEqual ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600">
                      Equal
                    </span>
                  ) : row.isBetter ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Improved
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                      Tradeoff
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
