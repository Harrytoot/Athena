"use client";

import { Check, AlertTriangle } from "lucide-react";
import type { DecisionDTO } from "@/types/decision";
import { cn } from "@/lib/utils";

export default function RiskSummaryPanel({ decision }: { decision: DecisionDTO }) {
  return (
    <div className="px-4 py-3 space-y-3">
      <div>
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-up/80">
          Key Consensus
        </div>
        <div className="space-y-1.5">
          {decision.consensusItems.map((item, i) => (
            <div key={i} className="flex items-start gap-2">
              <Check size={12}
                className={cn("mt-0.5 shrink-0",
                  item.type === "bullish" ? "text-up" : item.type === "bearish" ? "text-down" : "text-muted-foreground"
                )}
              />
              <span className="text-[10px] text-foreground/80 leading-relaxed">{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-down/80">
          Key Risks
        </div>
        <div className="space-y-1.5">
          {decision.riskItems.map((item, i) => (
            <div key={i}
              className={cn(
                "flex items-start gap-2 rounded border px-2.5 py-2",
                item.severity === "high" ? "bg-down/5 border-down/20" : "bg-background/40 border-divider/50"
              )}
            >
              <AlertTriangle size={12}
                className={cn("mt-0.5 shrink-0",
                  item.severity === "high" ? "text-down" : item.severity === "medium" ? "text-amber-400" : "text-muted-foreground"
                )}
              />
              <span className="text-[10px] text-foreground/80 leading-relaxed">{item.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
