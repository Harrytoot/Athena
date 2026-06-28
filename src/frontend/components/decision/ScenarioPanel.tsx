"use client";

import type { DecisionDTO } from "@/types/decision";

export default function ScenarioPanel({ decision }: { decision: DecisionDTO }) {
  const maxAbs = Math.max(
    ...decision.scenarios.map((s) => Math.abs(s.returnPct)),
    1
  );

  return (
    <div className="px-4 py-3">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Scenario Analysis
      </div>
      <div className="space-y-2">
        {decision.scenarios.map((scenario) => (
          <div key={scenario.label} className="flex items-center gap-3">
            <span className="w-20 text-xs font-medium text-foreground">{scenario.label}</span>
            <div className="relative flex-1 h-6 rounded bg-secondary overflow-hidden">
              <div
                className="absolute inset-y-0 rounded transition-all duration-500"
                style={{
                  width: `${(Math.abs(scenario.returnPct) / maxAbs) * 100}%`,
                  left: scenario.returnPct >= 0 ? "50%" : `${50 - (Math.abs(scenario.returnPct) / maxAbs) * 50}%`,
                  background: scenario.returnPct >= 0
                    ? `linear-gradient(90deg, ${scenario.color}30, ${scenario.color}80)`
                    : `linear-gradient(270deg, ${scenario.color}30, ${scenario.color}80)`,
                }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="font-mono text-xs font-bold" style={{ color: scenario.color }}>
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
