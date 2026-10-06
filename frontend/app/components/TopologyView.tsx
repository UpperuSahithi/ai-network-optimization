"use client";

import React, { useState } from "react";
import { TopologyType, OptimizeResponse, SimulationResponse, LinkItem } from "../types";

interface TopologyViewProps {
  nodesCount: number;
  topology: TopologyType;
  optimizationResult: OptimizeResponse | null;
  simulationResult: SimulationResponse | null;
}

interface NodeCoord {
  id: number;
  x: number;
  y: number;
}

export default function TopologyView({
  nodesCount,
  topology,
  optimizationResult,
  simulationResult,
}: TopologyViewProps) {
  const [viewMode, setViewMode] = useState<"ppo" | "baseline">("ppo");
  const [hoveredLink, setHoveredLink] = useState<LinkItem | null>(null);

  const effectiveNodes =
    optimizationResult?.configuration.number_of_nodes ??
    simulationResult?.config.number_of_nodes ??
    nodesCount;
  const effectiveTopology =
    optimizationResult?.configuration.topology ??
    simulationResult?.config.topology ??
    topology;

  // Compute node coordinates deterministically
  const svgWidth = 540;
  const svgHeight = 360;
  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;

  const nodeCoords: NodeCoord[] = [];

  if (effectiveTopology === "ring") {
    const radius = Math.min(centerX - 60, centerY - 50);
    for (let i = 0; i < effectiveNodes; i++) {
      const angle = (2 * Math.PI * i) / effectiveNodes - Math.PI / 2;
      nodeCoords.push({
        id: i,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      });
    }
  } else if (effectiveTopology === "star") {
    // Node 0 at center, others around in circle
    nodeCoords.push({ id: 0, x: centerX, y: centerY });
    const outerCount = Math.max(1, effectiveNodes - 1);
    const radius = Math.min(centerX - 60, centerY - 50);
    for (let i = 1; i < effectiveNodes; i++) {
      const angle = (2 * Math.PI * (i - 1)) / outerCount - Math.PI / 2;
      nodeCoords.push({
        id: i,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      });
    }
  } else if (effectiveTopology === "line" || effectiveTopology === "bus") {
    // Linear horizontal layout
    const margin = 60;
    const spacing = (svgWidth - 2 * margin) / Math.max(1, effectiveNodes - 1);
    for (let i = 0; i < effectiveNodes; i++) {
      nodeCoords.push({
        id: i,
        x: margin + i * spacing,
        y: centerY,
      });
    }
  } else {
    // Mesh layout (circular polygon)
    const radius = Math.min(centerX - 60, centerY - 50);
    for (let i = 0; i < effectiveNodes; i++) {
      const angle = (2 * Math.PI * i) / effectiveNodes - Math.PI / 2;
      nodeCoords.push({
        id: i,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      });
    }
  }

  // Get active links to draw
  // If optimizationResult exists, use actual link telemetry from PPO & baseline
  const linksToDraw: Array<{
    source: number;
    destination: number;
    linkData?: LinkItem;
    isCongested: boolean;
    isModifiedWeight: boolean;
    weight: number;
    traffic: number;
    capacity: number;
  }> = [];

  if (optimizationResult?.links) {
    // Group reciprocal links to draw single clean segments, or show directed
    // In our simulator, links are directed pairs. We will render directed links or aggregated pairs.
    const seenPairs = new Set<string>();

    optimizationResult.links.forEach((link) => {
      const minId = Math.min(link.source, link.destination);
      const maxId = Math.max(link.source, link.destination);
      const pairKey = `${minId}-${maxId}`;

      // Pick representative direction or higher utilization
      if (!seenPairs.has(pairKey)) {
        seenPairs.add(pairKey);

        const isPpoMode = viewMode === "ppo";
        const isCongested = isPpoMode ? link.congested_ppo : link.congested_baseline;
        const isModifiedWeight = Math.abs(link.weight - 1.0) > 0.05;
        const traffic = isPpoMode ? link.traffic_ppo : link.traffic_baseline;

        linksToDraw.push({
          source: link.source,
          destination: link.destination,
          linkData: link,
          isCongested,
          isModifiedWeight,
          weight: link.weight,
          traffic,
          capacity: link.capacity,
        });
      }
    });
  } else if (simulationResult?.metrics.links) {
    const seenPairs = new Set<string>();
    simulationResult.metrics.links.forEach((link) => {
      const minId = Math.min(link.source, link.destination);
      const maxId = Math.max(link.source, link.destination);
      const pairKey = `${minId}-${maxId}`;

      if (!seenPairs.has(pairKey)) {
        seenPairs.add(pairKey);
        linksToDraw.push({
          source: link.source,
          destination: link.destination,
          linkData: {
            source: link.source,
            destination: link.destination,
            capacity: link.capacity,
            latency: link.latency,
            traffic_baseline: link.traffic,
            traffic_ppo: link.traffic,
            utilization_baseline: link.utilization,
            utilization_ppo: link.utilization,
            congested_baseline: link.congested,
            congested_ppo: link.congested,
            weight: 1.0,
          },
          isCongested: link.congested,
          isModifiedWeight: false,
          weight: 1.0,
          traffic: link.traffic,
          capacity: link.capacity,
        });
      }
    });
  } else {
    // Generate default links for the topology
    if (effectiveTopology === "ring") {
      for (let i = 0; i < effectiveNodes; i++) {
        linksToDraw.push({
          source: i,
          destination: (i + 1) % effectiveNodes,
          isCongested: false,
          isModifiedWeight: false,
          weight: 1.0,
          traffic: 0,
          capacity: 10,
        });
      }
    } else if (effectiveTopology === "star") {
      for (let i = 1; i < effectiveNodes; i++) {
        linksToDraw.push({
          source: 0,
          destination: i,
          isCongested: false,
          isModifiedWeight: false,
          weight: 1.0,
          traffic: 0,
          capacity: 10,
        });
      }
    } else if (effectiveTopology === "line" || effectiveTopology === "bus") {
      for (let i = 0; i < effectiveNodes - 1; i++) {
        linksToDraw.push({
          source: i,
          destination: i + 1,
          isCongested: false,
          isModifiedWeight: false,
          weight: 1.0,
          traffic: 0,
          capacity: 10,
        });
      }
    } else {
      // Mesh
      for (let i = 0; i < effectiveNodes; i++) {
        for (let j = i + 1; j < effectiveNodes; j++) {
          linksToDraw.push({
            source: i,
            destination: j,
            isCongested: false,
            isModifiedWeight: false,
            weight: 1.0,
            traffic: 0,
            capacity: 10,
          });
        }
      }
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">2D Network Topology</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {effectiveTopology.toUpperCase()} topology ({effectiveNodes} nodes) • Interactive Link Inspector
          </p>
        </div>

        {/* View Mode Toggle when optimization is loaded */}
        {optimizationResult && (
          <div className="flex items-center rounded-lg bg-slate-100 p-1 text-xs font-medium">
            <button
              type="button"
              onClick={() => setViewMode("ppo")}
              className={`rounded-md px-3 py-1.5 transition-all ${
                viewMode === "ppo"
                  ? "bg-white text-indigo-700 shadow-xs font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              PPO AI View
            </button>
            <button
              type="button"
              onClick={() => setViewMode("baseline")}
              className={`rounded-md px-3 py-1.5 transition-all ${
                viewMode === "baseline"
                  ? "bg-white text-slate-900 shadow-xs font-semibold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Static Baseline View
            </button>
          </div>
        )}
      </div>

      {/* SVG Canvas */}
      <div className="mt-4 flex justify-center bg-slate-50/70 rounded-xl p-3 border border-slate-100 relative overflow-hidden">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full max-w-[560px] h-auto select-none"
        >
          {/* Background grid dots */}
          <pattern id="grid-dots" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="#cbd5e1" opacity="0.4" />
          </pattern>
          <rect width={svgWidth} height={svgHeight} fill="url(#grid-dots)" />

          {/* Links */}
          <g>
            {linksToDraw.map((link) => {
              const src = nodeCoords[link.source];
              const dst = nodeCoords[link.destination];
              if (!src || !dst) return null;

              const midX = (src.x + dst.x) / 2;
              const midY = (src.y + dst.y) / 2;

              let strokeColor = "#94a3b8"; // default slate
              let strokeWidth = 2.5;
              const strokeDasharray = "none";

              if (link.isCongested) {
                strokeColor = "#ef4444"; // red for congested
                strokeWidth = 4;
              } else if (viewMode === "ppo" && link.isModifiedWeight) {
                strokeColor = "#6366f1"; // indigo for PPO adjusted
                strokeWidth = 3.5;
              }

              return (
                <g
                  key={`link-${link.source}-${link.destination}`}
                  className="cursor-pointer group"
                  onMouseEnter={() => setHoveredLink(link.linkData ?? null)}
                  onMouseLeave={() => setHoveredLink(null)}
                >
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={dst.x}
                    y2={dst.y}
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                    strokeDasharray={strokeDasharray}
                    strokeLinecap="round"
                    className="transition-colors duration-200"
                  />

                  {/* Midpoint badge for modified weights or congestion */}
                  {viewMode === "ppo" && link.isModifiedWeight && (
                    <g transform={`translate(${midX}, ${midY})`}>
                      <rect
                        x="-20"
                        y="-10"
                        width="40"
                        height="20"
                        rx="4"
                        fill="#4f46e5"
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                      <text
                        x="0"
                        y="3"
                        textAnchor="middle"
                        fill="#ffffff"
                        fontSize="9"
                        fontWeight="bold"
                        fontFamily="monospace"
                      >
                        w:{link.weight.toFixed(2)}
                      </text>
                    </g>
                  )}

                  {link.isCongested && (
                    <g transform={`translate(${midX}, ${midY + (link.isModifiedWeight ? 14 : 0)})`}>
                      <circle cx="0" cy="0" r="8" fill="#ef4444" stroke="#ffffff" strokeWidth="1.5" />
                      <text x="0" y="3" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="bold">
                        !
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </g>

          {/* Nodes */}
          <g>
            {nodeCoords.map((node) => (
              <g key={`node-${node.id}`} className="cursor-pointer">
                {/* Node Outer Halo */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={22}
                  fill="#ffffff"
                  stroke="#e2e8f0"
                  strokeWidth="2"
                  className="shadow-sm"
                />
                {/* Node Core */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={16}
                  fill="#0f172a"
                  className="transition-transform duration-150 hover:scale-105"
                />
                {/* Node Label */}
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="12"
                  fontWeight="bold"
                  fontFamily="system-ui, sans-serif"
                >
                  {node.id}
                </text>
              </g>
            ))}
          </g>
        </svg>
      </div>

      {/* Inspector / Details bar */}
      <div className="mt-3 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2 border-t border-slate-100 pt-3">
        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-5 rounded-full bg-slate-400"></span>
            <span>Normal Link</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-5 rounded-full bg-rose-500"></span>
            <span>Congested (&gt;100% capacity)</span>
          </div>
          {optimizationResult && (
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-5 rounded-full bg-indigo-600"></span>
              <span>PPO Re-weighted (Synthetic Cost)</span>
            </div>
          )}
        </div>

        {/* Hover Inspector */}
        {hoveredLink && (
          <div className="font-mono text-xs bg-slate-900 text-white px-2.5 py-1 rounded-md shadow-xs">
            Link {hoveredLink.source}→{hoveredLink.destination}: Base {hoveredLink.traffic_baseline.toFixed(1)}G | PPO {hoveredLink.traffic_ppo.toFixed(1)}G (w: {hoveredLink.weight.toFixed(2)})
          </div>
        )}
      </div>
    </div>
  );
}
