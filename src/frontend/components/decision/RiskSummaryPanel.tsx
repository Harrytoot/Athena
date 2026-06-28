"use client";

import { Check, AlertTriangle, Info } from "lucide-react";
import type { DecisionDTO } from "@/types/decision";

const severityConfig = {
  high: { bg: "bg-down/10", border: "border-down/30", text: "text-down", icon: AlertTriangle },
  medium: { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400", icon: Info },
  low: { bg: "bg-muted/10", border: "border-border", text: "text-muted-foreground", icon: Info },
};

export default function RiskSummaryPanel({ decision }: { decision: DecisionDTO }) {
  return (
    <div className="px-4 py-3 space-y-3">
      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Key Consensus
        </div>
        <div className="space-y-1.5">
          {decision.consensusItems.map((item, i) => (
            <div key={i} className="flex items-start gap-2">
              <Check
                size={13}
                className={item.type === "bullish" ? "text-up mt-0.5 shrink-0" : item.type === "bearish" ? "text-down mt-0.5 shrink-0" : "text-muted-foreground mt-0.5 shrink-0"}
              />
              <span className="text-xs text-foreground/80 leading-relaxed">{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-down">
          Key Risks
        </div>
        <div className="space-y-1.5">
          {decision.riskItems.map((item, i) => {
            const cfg = severityConfig[item.severity];
            const Icon = cfg.icon;
            return (
              <div
                key={i}
                className={`flex items-start gap-2 rounded-md border px-2.5 py-2 ${cfg.bg} ${cfg.border}`}
              >
                <Icon size={13} className={`${cfg.text} mt-0.5 shrink-0`} />
                <span className="text-xs text-foreground/80 leading-relaxed">{item.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
