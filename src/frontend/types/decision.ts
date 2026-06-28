export type Signal = "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL";

export interface ConsensusItem {
  text: string;
  type: "bullish" | "neutral" | "bearish";
}

export interface RiskItem {
  text: string;
  severity: "high" | "medium" | "low";
}

export interface ScenarioEntry {
  label: string;
  returnPct: number;
  color: string;
}

export type Action = "APPROVE" | "HOLD" | "REJECT";

export interface FactorSemantic {
  name: string;
  label: string;
  value: number;
  weight: number;
  contribution: number;
  isBullish: boolean;
  assessment: string;
}

export interface SignalSemantic {
  direction: string;
  directionLabel: string;
  strength: number;
  baseConfidence: number;
}

export interface RiskSemantic {
  overallLevel: string;
  drawdownRisk: number;
  volatilityRisk: number;
  correlationRisk: number;
  scenarioVulnerability: number;
  warnings: string[];
}

export interface ScenarioSemantic {
  stabilityScore: number;
  worstCaseScoreChange: number;
  stateChangeCount: number;
  entries: Record<string, unknown>[];
}

export interface ExecutionSemantic {
  feasibility: number;
  estimatedSlippageBps: number;
  estimatedFillRate: number;
  qualityGrade: string;
  warnings: string[];
}

export interface Contradiction {
  contradictionType: string;
  severity: string;
  description: string;
}

export interface ConsistencyReport {
  isConsistent: boolean;
  contradictions: Contradiction[];
  consistencyScore: number;
}

export interface DecisionDTO {
  symbol: string;
  name: string;
  signal: Signal;
  signalLabel: string;
  confidence: number;
  consensusItems: ConsensusItem[];
  riskItems: RiskItem[];
  scenarios: ScenarioEntry[];
  action: Action;
  actionLabel: string;
  explanation: string;
  factors: FactorSemantic[];
  signalSemantic: SignalSemantic | null;
  riskSemantic: RiskSemantic | null;
  scenarioSemantic: ScenarioSemantic | null;
  executionSemantic: ExecutionSemantic | null;
  consistency: ConsistencyReport | null;
  confidenceScoreNormalized: number | null;
  semanticVersion: string;
}

export function getSignalColor(signal: Signal): string {
  const map: Record<Signal, string> = {
    STRONG_BUY: "#00E5FF",
    BUY: "#00B8D9",
    NEUTRAL: "#8B95A5",
    SELL: "#FF5630",
    STRONG_SELL: "#FF1744",
  };
  return map[signal];
}

export function getSignalTextColor(signal: Signal): string {
  if (signal === "STRONG_BUY" || signal === "BUY") return "text-up";
  if (signal === "SELL" || signal === "STRONG_SELL") return "text-down";
  return "text-muted-foreground";
}

export function getSignalBgColor(signal: Signal): string {
  if (signal === "STRONG_BUY" || signal === "BUY") return "bg-up/10";
  if (signal === "SELL" || signal === "STRONG_SELL") return "bg-down/10";
  return "bg-muted/10";
}
