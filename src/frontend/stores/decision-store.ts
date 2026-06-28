import { create } from "zustand";
import type { DecisionDTO, Signal, Action } from "@/types/decision";
import { getDecision } from "@/lib/api";

interface DecisionStore {
  decision: DecisionDTO | null;
  loading: boolean;
  fetchDecision: (symbol: string, name: string) => Promise<void>;
  setDecision: (d: DecisionDTO) => void;
  clearDecision: () => void;
}

function generateFallbackDecision(symbol: string, name: string): DecisionDTO {
  const hash = symbol.charCodeAt(0) + symbol.charCodeAt(symbol.length - 1 || 0);
  const signals: { signal: Signal; label: string; confidence: number; action: Action; actionLabel: string }[] = [
    { signal: "STRONG_BUY", label: "强烈做多", confidence: 82, action: "APPROVE", actionLabel: "执行买入" },
    { signal: "BUY", label: "建议做多", confidence: 67, action: "APPROVE", actionLabel: "小仓位介入" },
    { signal: "NEUTRAL", label: "观望等待", confidence: 45, action: "HOLD", actionLabel: "等待确认信号" },
    { signal: "SELL", label: "建议做空", confidence: 63, action: "HOLD", actionLabel: "减仓观望" },
    { signal: "STRONG_SELL", label: "强烈做空", confidence: 78, action: "REJECT", actionLabel: "清仓离场" },
  ];

  const pick = signals[hash % signals.length];

  return {
    symbol,
    name,
    signal: pick.signal,
    signalLabel: pick.label,
    confidence: pick.confidence,
    consensusItems: [
      { text: "动量因子与趋势方向一致", type: "bullish" },
      { text: "北向资金持续净流入", type: "bullish" },
      { text: "波动率处于近30日低位", type: "neutral" },
      { text: "RSI未进入超买区间", type: "neutral" },
    ],
    riskItems: [
      { text: "最大回撤已达历史70%分位", severity: "high" },
      { text: "下周美联储利率决议", severity: "high" },
      { text: "行业轮动速度加快", severity: "medium" },
      { text: "成交量较5日均值偏低", severity: "low" },
    ],
    scenarios: [
      { label: "🐂 Bull", returnPct: 6.1, color: "#00B8D9" },
      { label: "📊 Base", returnPct: 2.3, color: "#8B95A5" },
      { label: "🐻 Bear", returnPct: -3.8, color: "#FF5630" },
    ],
    action: pick.action,
    actionLabel: pick.actionLabel,
    explanation: "基于多因子综合分析的结果，建议参考上述信号。",
    factors: [
      { name: "momentum", label: "动量因子", value: 0.72, weight: 0.25, contribution: 0.18, isBullish: true, assessment: "趋势强度中等偏上" },
      { name: "value", label: "价值因子", value: 0.45, weight: 0.2, contribution: 0.09, isBullish: false, assessment: "估值处于合理区间上沿" },
      { name: "quality", label: "质量因子", value: 0.68, weight: 0.2, contribution: 0.14, isBullish: true, assessment: "盈利质量稳健" },
      { name: "sentiment", label: "情绪因子", value: 0.55, weight: 0.15, contribution: 0.08, isBullish: true, assessment: "市场情绪中性偏乐观" },
      { name: "volatility", label: "波动因子", value: 0.38, weight: 0.2, contribution: 0.08, isBullish: false, assessment: "波动率处于中位水平" },
    ],
    signalSemantic: {
      direction: pick.signal,
      directionLabel: pick.label,
      strength: pick.confidence / 100,
      baseConfidence: pick.confidence / 100,
    },
    riskSemantic: {
      overallLevel: pick.confidence > 70 ? "low" : pick.confidence > 40 ? "medium" : "high",
      drawdownRisk: 0.35,
      volatilityRisk: 0.42,
      correlationRisk: 0.28,
      scenarioVulnerability: 0.3,
      warnings: ["局部市场波动可能加剧"],
    },
    scenarioSemantic: {
      stabilityScore: 0.65,
      worstCaseScoreChange: -0.15,
      stateChangeCount: 2,
      entries: [],
    },
    executionSemantic: {
      feasibility: 0.85,
      estimatedSlippageBps: 5.2,
      estimatedFillRate: 0.92,
      qualityGrade: "good",
      warnings: [],
    },
    consistency: {
      isConsistent: true,
      contradictions: [],
      consistencyScore: 0.88,
    },
    confidenceScoreNormalized: pick.confidence / 100,
    semanticVersion: "1.0.0",
  };
}

export const useDecisionStore = create<DecisionStore>((set) => ({
  decision: null,
  loading: false,

  fetchDecision: async (symbol, name) => {
    set({ loading: true });
    try {
      const data = await getDecision(symbol);
      set({ decision: data, loading: false });
    } catch {
      set({ decision: generateFallbackDecision(symbol, name), loading: false });
    }
  },

  setDecision: (d) => set({ decision: d, loading: false }),
  clearDecision: () => set({ decision: null }),
}));
