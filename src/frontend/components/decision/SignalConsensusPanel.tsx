"use client";

import type { DecisionDTO } from "@/types/decision";
import { getSignalColor, getSignalTextColor, getSignalBgColor } from "@/types/decision";

export default function SignalConsensusPanel({ decision }: { decision: DecisionDTO }) {
  const color = getSignalColor(decision.signal);
  const confPct = decision.confidence;
  const circumference = 2 * Math.PI * 34;
  const offset = circumference - (confPct / 100) * circumference;

  return (
    <div className="px-4 py-5 text-center">
      <svg width="88" height="88" className="mx-auto mb-3">
        <circle cx="44" cy="44" r="34" fill="none" stroke="#2A2E39" strokeWidth="6" />
        <circle
          cx="44" cy="44" r="34"
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 44 44)"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text x="44" y="42" textAnchor="middle" className="font-mono text-lg font-bold" fill={color}>
          {confPct}%
        </text>
        <text x="44" y="56" textAnchor="middle" className="text-[10px]" fill="#8B95A5">
          Confidence
        </text>
      </svg>

      <div
        className={`inline-block rounded-lg px-4 py-2 ${getSignalBgColor(decision.signal)}`}
        style={{ boxShadow: `0 0 24px ${color}20` }}
      >
        <div className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
          Signal Consensus
        </div>
        <div
          className={`mt-1 text-2xl font-black ${getSignalTextColor(decision.signal)}`}
          style={{ textShadow: `0 0 16px ${color}40` }}
        >
          {decision.signalLabel}
        </div>
        <div className="mt-0.5 font-mono text-xl font-bold text-foreground">
          {decision.symbol}
        </div>
      </div>
    </div>
  );
}
