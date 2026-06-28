"use client";

import { useEffect } from "react";
import { useDecisionStore } from "@/stores/decision-store";
import SignalConsensusPanel from "./SignalConsensusPanel";
import RiskSummaryPanel from "./RiskSummaryPanel";
import ScenarioPanel from "./ScenarioPanel";
import ActionPanel from "./ActionPanel";
import ExecutionSheet from "@/components/execution/ExecutionSheet";

interface DecisionCenterProps {
  symbol: string;
  name: string;
  price: number;
}

export default function DecisionCenter({ symbol, name, price }: DecisionCenterProps) {
  const decision = useDecisionStore((s) => s.decision);
  const loading = useDecisionStore((s) => s.loading);
  const fetchDecision = useDecisionStore((s) => s.fetchDecision);

  useEffect(() => {
    fetchDecision(symbol, name);
  }, [symbol, name, fetchDecision]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-[#00B8D9]/20 bg-card">
        <div className="text-center text-xs text-muted-foreground animate-pulse">
          决策分析中...
        </div>
      </div>
    );
  }

  if (!decision) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-[#00B8D9]/20 bg-card">
        <div className="text-center text-xs text-muted-foreground">无决策数据</div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-[#00B8D9]/30 bg-card shadow-[0_0_15px_rgba(0,184,217,0.05)]">
      <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
        <div className="h-2 w-2 rounded-full bg-primary shadow-[0_0_6px_rgba(0,184,217,0.6)]" />
        <span className="text-xs font-semibold uppercase tracking-widest text-primary">
          Decision Center
        </span>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-border">
        <SignalConsensusPanel decision={decision} />
        <RiskSummaryPanel decision={decision} />
        <ScenarioPanel decision={decision} />
      </div>

      <div className="border-t border-border">
        <ActionPanel decision={decision} price={price} />
      </div>

      <ExecutionSheet />
    </div>
  );
}
