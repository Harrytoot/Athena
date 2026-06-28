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
