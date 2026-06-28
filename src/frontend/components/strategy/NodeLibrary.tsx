"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Database, Activity, Gauge, Shield, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { NODE_TEMPLATES, getCategoryColor, type NodeCategory, type NodeTemplate } from "@/components/strategy/types";
import { useStrategyStore } from "@/stores/strategy-store";

const CATEGORY_ICONS: Record<NodeCategory, typeof Database> = {
  datasource: Database,
  indicator: Activity,
  signal: Gauge,
  risk: Shield,
  execution: Zap,
};

const CATEGORY_LABELS: Record<NodeCategory, string> = {
  datasource: "数据源",
  indicator: "技术指标",
  signal: "信号生成",
  risk: "风控管理",
  execution: "订单执行",
};

export default function NodeLibrary() {
  const [collapsed, setCollapsed] = useState(false);
  const addNode = useStrategyStore((s) => s.addNode);

  const grouped = NODE_TEMPLATES.reduce(
    (acc, t) => {
      if (!acc[t.category]) acc[t.category] = [];
      acc[t.category].push(t);
      return acc;
    },
    {} as Record<NodeCategory, NodeTemplate[]>
  );

  const handleDragStart = (event: React.DragEvent, template: NodeTemplate) => {
    event.dataTransfer.setData("application/reactflow-template", JSON.stringify(template));
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <div className={cn("flex h-full flex-col border-r border-border bg-card transition-all", collapsed ? "w-10" : "w-52")}>
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex h-8 items-center justify-center border-b border-border text-muted-foreground hover:text-foreground"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {!collapsed && (
        <div className="flex-1 overflow-y-auto p-2 space-y-3">
          {(Object.keys(grouped) as NodeCategory[]).map((category) => (
            <div key={category}>
              <div className="mb-1 px-1 text-[11px] font-semibold uppercase text-muted-foreground/60">
                {CATEGORY_LABELS[category]}
              </div>
              {grouped[category].map((template) => {
                const Icon = CATEGORY_ICONS[category];
                const color = getCategoryColor(category);
                return (
                  <div
                    key={template.type}
                    draggable
                    onDragStart={(e) => handleDragStart(e, template)}
                    onClick={() =>
                      addNode(template.category, template.type, template.label, template.sublabel, template.defaultData)
                    }
                    className="mb-1 flex cursor-grab items-center gap-2 rounded-md border border-border/50 px-2 py-2 text-xs transition-colors hover:bg-secondary active:cursor-grabbing"
                    style={{ borderLeftColor: color, borderLeftWidth: "2px" }}
                  >
                    <Icon size={14} style={{ color }} />
                    <div className="min-w-0">
                      <div className="truncate font-medium text-foreground">{template.label}</div>
                      <div className="truncate text-muted-foreground/70">{template.sublabel}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
