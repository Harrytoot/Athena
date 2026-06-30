"use client";

import type { DecisionDTO } from "@/types/decision";

export default function ScenarioPanel({ decision }: { decision: DecisionDTO }) {
  const maxAbs = Math.max(...decision.scenarios.map((s) => Math.abs(s.returnPct)), 1);

  const scenarioLabels: Record<string, string> = {
    Bull: "Bull",
    Base: "Base",
    Bear: "Bear",
  };

  return (
    <div className="px-4 py-3">
      <div className="mb-2.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        Expected Scenarios
      </div>
      <div className="space-y-2">
        {decision.scenarios.map((scenario) => (
          <div key={scenario.label} className="flex items-center gap-2.5">
            <span className="w-14 text-[10px] font-medium text-muted-foreground">
              {scenarioLabels[scenario.label] ?? scenario.label}
            </span>
            <div className="relative flex-1 h-5.5 rounded-sm bg-secondary/50 overflow-hidden">
              <div
                className="absolute inset-y-0 rounded-sm transition-all duration-500"
                style={{
                  width: `${(Math.abs(scenario.returnPct) / maxAbs) * 100}%`,
                  left: scenario.returnPct >= 0 ? "50%" : `${50 - (Math.abs(scenario.returnPct) / maxAbs) * 50}%`,
                  background: scenario.returnPct >= 0
                    ? `linear-gradient(90deg, ${scenario.color}20, ${scenario.color})`
                    : `linear-gradient(270deg, ${scenario.color}20, ${scenario.color})`,
                }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="font-mono text-[10px] font-bold" style={{ color: scenario.color }}>
                  {scenario.returnPct >= 0 ? "+" : ""}{scenario.returnPct.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
