"use client";

import type { DecisionDTO } from "@/types/decision";
import { getSignalColor, getSignalTextColor, getSignalBgColor } from "@/types/decision";

export default function SignalConsensusPanel({ decision }: { decision: DecisionDTO }) {
  const color = getSignalColor(decision.signal);
  const confPct = decision.confidence;
  const circumference = 2 * Math.PI * 38;
  const offset = circumference - (confPct / 100) * circumference;

  return (
    <div className="px-4 py-4 text-center">
      {/* Confidence Ring */}
      <svg width="96" height="96" className="mx-auto mb-3">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <circle cx="48" cy="48" r="38" fill="none" stroke="#232838" strokeWidth="6" />
        <circle
          cx="48" cy="48" r="38"
          fill="none" stroke={color} strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 48 48)"
          filter="url(#glow)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text x="48" y="46" textAnchor="middle" className="font-mono text-xl font-bold" fill={color}>
          {confPct}%
        </text>
        <text x="48" y="58" textAnchor="middle" className="text-[9px]" fill="#6B7280">
          Score
        </text>
      </svg>

      {/* Signal Badge */}
      <div
        className={`inline-block rounded-lg px-5 py-2.5 ${getSignalBgColor(decision.signal)}`}
        style={{ boxShadow: `0 0 32px ${color}25` }}
      >
        <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Signal Consensus
        </div>
        <div
          className={`mt-1 text-3xl font-black tracking-wide ${getSignalTextColor(decision.signal)}`}
          style={{ textShadow: `0 0 20px ${color}40` }}
        >
          {decision.signalLabel}
        </div>
        <div className="mt-0.5 font-mono text-sm font-semibold text-foreground">
          {decision.symbol}
        </div>
      </div>
    </div>
  );
}
