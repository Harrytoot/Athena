"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { StrategyNodeData } from "@/stores/strategy-store";
import { getCategoryColor, getHandles } from "@/components/strategy/types";

function StrategyNodeComponent({ data, selected }: NodeProps) {
  const nodeData = data as unknown as StrategyNodeData;
  const category = nodeData.category;
  const color = getCategoryColor(category);
  const handles = getHandles(category);

  const summary = Object.entries(nodeData.properties)
    .slice(0, 2)
    .map(([k, v]) => `${k}: ${v}`)
    .join(" | ");

  return (
    <div
      className="min-w-[160px] rounded-lg border-2 bg-card px-3 py-2 text-xs transition-shadow"
      style={{
        borderColor: selected ? color : "transparent",
        borderLeftColor: color,
        borderLeftWidth: "3px",
        boxShadow: selected ? `0 0 12px ${color}40` : "0 1px 3px rgba(0,0,0,0.4)",
      }}
    >
      {handles.inputs.map((handleId, i) => (
        <Handle
          key={handleId}
          type="target"
          position={Position.Left}
          id={handleId}
          style={{
            top: handles.inputs.length > 1 ? `${((i + 1) / (handles.inputs.length + 1)) * 100}%` : "50%",
            background: color,
            border: "2px solid #151924",
            width: 8,
            height: 8,
          }}
        />
      ))}

      <div className="font-semibold text-foreground">{nodeData.label}</div>
      <div className="mt-0.5 text-muted-foreground/70">{nodeData.sublabel}</div>
      {summary && (
        <div
          className="mt-1 truncate rounded px-1.5 py-0.5 font-mono"
          style={{ background: `${color}15`, color }}
        >
          {summary}
        </div>
      )}

      {handles.outputs.map((handleId, i) => (
        <Handle
          key={handleId}
          type="source"
          position={Position.Right}
          id={handleId}
          style={{
            top: handles.outputs.length > 1 ? `${((i + 1) / (handles.outputs.length + 1)) * 100}%` : "50%",
            background: color,
            border: "2px solid #151924",
            width: 8,
            height: 8,
          }}
        />
      ))}
    </div>
  );
}

export const StrategyNode = memo(StrategyNodeComponent);
