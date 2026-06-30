"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { DecisionDTO, Action } from "@/types/decision";
import type { TradeSide } from "@/types/execution";
import { useExecutionStore } from "@/stores/execution-store";

const actionConfig: Record<Action, { label: string; baseClass: string }> = {
  APPROVE: {
    label: "APPROVE",
    baseClass: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_24px_rgba(0,184,217,0.25)]",
  },
  HOLD: {
    label: "MODIFY",
    baseClass: "border border-border text-muted-foreground hover:border-primary/50 hover:text-foreground bg-transparent",
  },
  REJECT: {
    label: "REJECT",
    baseClass: "border border-border text-muted-foreground hover:border-destructive hover:text-destructive bg-transparent",
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
    <div className="px-3 py-3">
      {decision.explanation && (
        <div className="mb-3 rounded-md border border-divider bg-background/50 p-2.5">
          <p className="text-[10px] text-muted-foreground leading-relaxed whitespace-pre-wrap">
            {decision.explanation}
          </p>
        </div>
      )}

      <div className="mb-2.5 rounded-md border border-border/50 bg-secondary/40 px-3 py-2 text-center">
        <span className="text-[9px] uppercase tracking-wider text-muted-foreground">建议操作：</span>
        <span className="ml-1 font-mono text-xs font-bold text-foreground">{decision.actionLabel}</span>
      </div>

      <div className="grid grid-cols-3 gap-1.5">
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
                "rounded-lg py-2 text-[10px] font-bold tracking-wider transition-all duration-200",
                cfg.baseClass,
                isActive && "ring-1 ring-primary/50",
                justClicked && "scale-95 opacity-80"
              )}
            >
              {justClicked ? "\u2713" : cfg.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
