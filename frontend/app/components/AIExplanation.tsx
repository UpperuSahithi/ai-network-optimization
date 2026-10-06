"use client";

import React from "react";
import { OptimizeResponse } from "../types";

interface AIExplanationProps {
  optimizationResult: OptimizeResponse | null;
}

export default function AIExplanation({ optimizationResult }: AIExplanationProps) {
  if (!optimizationResult) {
    return null;
  }

  const { links, link_weights } = optimizationResult;

  // Filter links whose weights were modified significantly by PPO (relative to unit weight 1.0)
  const modifiedLinks = links.filter((l) => Math.abs(l.weight - 1.0) > 0.05);
  const unchangedLinks = links.filter((l) => Math.abs(l.weight - 1.0) <= 0.05);

  return (
    <div className="rounded-xl border border-indigo-200 bg-linear-to-b from-indigo-50/40 to-white p-6 shadow-sm">
      <div className="flex items-center gap-2 pb-3 border-b border-indigo-100">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
          AI
        </span>
        <div>
          <h3 className="text-lg font-semibold text-slate-900">What did the AI change?</h3>
          <p className="text-xs text-slate-500">
            Reinforcement Learning policy explanation & weight adjustments
          </p>
        </div>
      </div>

      {/* Mechanism explanation */}
      <div className="mt-4 rounded-lg bg-white border border-indigo-100 p-4 shadow-xs">
        <p className="text-sm text-slate-700 leading-relaxed">
          <strong className="text-indigo-950 font-semibold">
            Higher routing weight makes a link less preferred by the shortest-path routing algorithm, allowing traffic to use alternate paths.
          </strong>
        </p>
        <p className="mt-2 text-xs text-slate-500 leading-relaxed">
          PPO does not directly control individual packets at runtime. Instead, the agent learns to optimize continuous{" "}
          <span className="font-mono text-indigo-700">link weights</span> passed into the shortest-path routing algorithm.
          By assigning higher synthetic cost to bottleneck links, excess traffic is naturally diverted across underutilized links in the topology.
        </p>
      </div>

      {/* Modified links breakdown */}
      <div className="mt-5">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
            Key Routing Decisions ({modifiedLinks.length} Links Re-weighted)
          </h4>
          <span className="text-[11px] text-slate-400">
            Total links analyzed: {link_weights.length}
          </span>
        </div>

        {modifiedLinks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {modifiedLinks.map((link) => {
              const weightDiff = link.weight - 1.0;
              const weightPct = (weightDiff * 100).toFixed(1);
              const trafficChange = link.traffic_ppo - link.traffic_baseline;
              const trafficRelieved = trafficChange < 0;

              return (
                <div
                  key={`${link.source}-${link.destination}`}
                  className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-xs hover:border-indigo-300 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                        Link {link.source} → {link.destination}
                      </span>
                      {trafficRelieved && (
                        <span className="inline-flex items-center text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          Bottleneck Relieved
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                      Weight: {link.weight.toFixed(4)} ({weightDiff > 0 ? `+${weightPct}%` : `${weightPct}%`})
                    </span>
                  </div>

                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="rounded bg-slate-50 p-2">
                      <span className="block text-[10px] text-slate-400 uppercase">Static Baseline</span>
                      <span className="font-mono text-slate-700 font-medium">
                        Traffic: {link.traffic_baseline.toFixed(1)} / {link.capacity.toFixed(0)} Gbps
                      </span>
                      <span className={`block text-[11px] ${link.congested_baseline ? "text-rose-600 font-semibold" : "text-slate-500"}`}>
                        Util: {(link.utilization_baseline * 100).toFixed(0)}% {link.congested_baseline ? "⚠️ Overload" : ""}
                      </span>
                    </div>

                    <div className="rounded bg-indigo-50/50 p-2 border border-indigo-100/60">
                      <span className="block text-[10px] text-indigo-500 uppercase font-semibold">After PPO</span>
                      <span className="font-mono text-indigo-950 font-medium">
                        Traffic: {link.traffic_ppo.toFixed(1)} / {link.capacity.toFixed(0)} Gbps
                      </span>
                      <span className={`block text-[11px] ${link.congested_ppo ? "text-amber-700 font-medium" : "text-emerald-700 font-semibold"}`}>
                        Util: {(link.utilization_ppo * 100).toFixed(0)}% {!link.congested_ppo && link.congested_baseline ? "✓ Healthy" : ""}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic bg-white p-3 rounded-lg border border-slate-200">
            PPO maintained near-unit weights for this scenario (uniform baseline was already optimal).
          </p>
        )}

        {/* Unchanged links summary */}
        {unchangedLinks.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
            <span className="text-slate-400">Default-weight links (w ≈ 1.0):</span>
            {unchangedLinks.map((l) => (
              <span
                key={`${l.source}-${l.destination}`}
                className="font-mono text-[11px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded"
              >
                {l.source}→{l.destination}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
