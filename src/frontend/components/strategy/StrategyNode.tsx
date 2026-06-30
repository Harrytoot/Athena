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

  return (
    <div
      className="min-w-[130px] rounded-md border bg-background/80 backdrop-blur-sm px-2.5 py-1.5 text-xs transition-all"
      style={{
        borderColor: selected ? color : "#232838",
        borderLeftColor: color,
        borderLeftWidth: "2px",
        boxShadow: selected ? `0 0 16px ${color}30, 0 4px 12px rgba(0,0,0,0.5)` : "0 2px 6px rgba(0,0,0,0.4)",
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
            border: "1.5px solid #080A10",
            width: 7, height: 7,
          }}
        />
      ))}

      <div className="flex items-center gap-1.5">
        <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
        <span className="font-semibold text-foreground text-[11px]">{nodeData.label}</span>
      </div>
      <div className="mt-0.5 text-[10px] text-muted-foreground/60">{nodeData.sublabel}</div>

      {handles.outputs.map((handleId, i) => (
        <Handle
          key={handleId}
          type="source"
          position={Position.Right}
          id={handleId}
          style={{
            top: handles.outputs.length > 1 ? `${((i + 1) / (handles.outputs.length + 1)) * 100}%` : "50%",
            background: color,
            border: "1.5px solid #080A10",
            width: 7, height: 7,
          }}
        />
      ))}
    </div>
  );
}

export const StrategyNode = memo(StrategyNodeComponent);
