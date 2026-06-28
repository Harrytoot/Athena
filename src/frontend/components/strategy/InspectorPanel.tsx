"use client";

import { useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, Trash2 } from "lucide-react";
import { useStrategyStore } from "@/stores/strategy-store";
import { getCategoryColor } from "@/components/strategy/types";

export default function InspectorPanel() {
  const selectedNodeId = useStrategyStore((s) => s.selectedNodeId);
  const nodes = useStrategyStore((s) => s.nodes);
  const selectNode = useStrategyStore((s) => s.selectNode);
  const updateNodeProperties = useStrategyStore((s) => s.updateNodeProperties);
  const removeNode = useStrategyStore((s) => s.removeNode);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);
  const inputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => {
    inputRefs.current = {};
  }, [selectedNodeId]);

  const handleChange = (key: string, value: unknown) => {
    if (!selectedNodeId) return;
    const num = Number(value);
    updateNodeProperties(selectedNodeId, { [key]: isNaN(num) ? value : num });
  };

  return (
    <AnimatePresence>
      {selectedNode ? (
        <motion.div
          key="inspector"
          initial={{ x: 300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 300, opacity: 0 }}
          transition={{ type: "spring", stiffness: 400, damping: 35 }}
          className="flex h-full w-64 flex-shrink-0 flex-col border-l border-border bg-card"
        >
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <div className="flex items-center gap-2">
              <div
                className="h-2.5 w-2.5 rounded-full"
                style={{ background: getCategoryColor(selectedNode.data.category) }}
              />
              <span className="text-sm font-semibold text-foreground">{selectedNode.data.label}</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => removeNode(selectedNode.id)}
                className="rounded p-1 text-muted-foreground hover:bg-destructive/15 hover:text-destructive"
              >
                <Trash2 size={14} />
              </button>
              <button
                onClick={() => selectNode(null)}
                className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            <div className="text-xs text-muted-foreground">{selectedNode.data.sublabel}</div>

            {Object.entries(selectedNode.data.properties).map(([key, value]) => (
              <div key={key} className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">{key}</label>
                <input
                  ref={(el) => { inputRefs.current[key] = el; }}
                  type={typeof value === "number" ? "number" : "text"}
                  value={String(value)}
                  step={typeof value === "number" ? "any" : undefined}
                  onChange={(e) => handleChange(key, e.target.value)}
                  className="w-full rounded border border-border bg-background px-2 py-1.5 font-mono text-xs text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            ))}

            {Object.keys(selectedNode.data.properties).length === 0 && (
              <div className="text-xs text-muted-foreground/60">该节点无可调参数</div>
            )}
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
