"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { DecisionDTO, Action } from "@/types/decision";
import type { TradeSide } from "@/types/execution";
import { useExecutionStore } from "@/stores/execution-store";

const actionConfig: Record<Action, { label: string; baseClass: string; hoverClass: string }> = {
  APPROVE: {
    label: "APPROVE",
    baseClass: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_20px_rgba(0,184,217,0.2)]",
    hoverClass: "",
  },
  HOLD: {
    label: "MODIFY",
    baseClass: "border border-border text-muted-foreground hover:border-primary/50 hover:text-foreground bg-transparent",
    hoverClass: "",
  },
  REJECT: {
    label: "REJECT",
    baseClass: "border border-border text-muted-foreground hover:border-destructive hover:text-destructive bg-transparent",
    hoverClass: "",
  },
};

function getTradeSide(signal: DecisionDTO["signal"]): TradeSide {
  if (signal === "STRONG_BUY" || signal === "BUY") return "BUY";
  if (signal === "STRONG_SELL" || signal === "SELL") return "SELL";
  return "BUY";
}

export default function ActionPanel({ decision, price }: { decision: DecisionDTO; price: number }) {
  const [clicked, setClicked] = useState<Action | null>(null);
  const currentAction = decision.action;
  const openSheet = useExecutionStore((s) => s.openSheet);

  const handleClick = (action: Action) => {
    if (action === "APPROVE" || action === "HOLD") {
      openSheet({
        symbol: decision.symbol,
        name: decision.signalLabel,
        price,
        side: getTradeSide(decision.signal),
        defaultSize: 1000,
      });
    } else {
      setClicked(action);
      setTimeout(() => setClicked(null), 1500);
    }
  };

  return (
    <div className="px-4 py-3">
      {decision.explanation && (
        <div className="mb-5 rounded-md border border-[#2A2E39] bg-[#0B0E14]/50 p-3">
          <p className="text-xs text-[#8F9BBA] leading-relaxed whitespace-pre-wrap">
            {decision.explanation}
          </p>
        </div>
      )}

      <div className="mb-2 rounded-md border border-border/50 bg-secondary/50 px-3 py-2 text-center">
        <span className="text-[11px] uppercase tracking-wider text-muted-foreground">
          建议操作：
        </span>
        <span className="ml-1 font-mono text-sm font-bold text-foreground">
          {decision.actionLabel}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {(["APPROVE", "HOLD", "REJECT"] as Action[]).map((action) => {
          const cfg = actionConfig[action];
          const isActive = currentAction === action;
          const justClicked = clicked === action;
          return (
            <button
              key={action}
              onClick={() => handleClick(action)}
              disabled={justClicked}
              className={cn(
                "rounded-lg py-2 text-xs font-semibold transition-all duration-200",
                cfg.baseClass,
                isActive && "ring-1 ring-primary/50",
                justClicked && "scale-95 opacity-80"
              )}
            >
              {justClicked ? "✓" : cfg.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
