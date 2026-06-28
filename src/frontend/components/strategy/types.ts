export type NodeCategory = "datasource" | "indicator" | "signal" | "risk" | "execution";

export interface NodeTemplate {
  category: NodeCategory;
  type: string;
  label: string;
  sublabel: string;
  defaultData: Record<string, unknown>;
}

export const HANDLE_COMPATIBILITY: Record<string, string[]> = {
  source: ["indicator_in"],
  indicator_out: ["signal_in"],
  signal_out: ["risk_in"],
  risk_out: ["execution_in"],
};

export const NODE_TEMPLATES: NodeTemplate[] = [
  {
    category: "datasource",
    type: "datasource",
    label: "数据源",
    sublabel: "行情 / 基本面",
    defaultData: { symbol: "000001", frequency: "daily", lookback: 200 },
  },
  {
    category: "indicator",
    type: "indicator_ma",
    label: "移动平均 MA",
    sublabel: "趋势跟踪",
    defaultData: { period: 20, source: "close" },
  },
  {
    category: "indicator",
    type: "indicator_rsi",
    label: "相对强弱 RSI",
    sublabel: "超买超卖",
    defaultData: { period: 14, overbought: 70, oversold: 30 },
  },
  {
    category: "indicator",
    type: "indicator_macd",
    label: "MACD",
    sublabel: "趋势动能",
    defaultData: { fast: 12, slow: 26, signal: 9 },
  },
  {
    category: "signal",
    type: "signal_cross",
    label: "交叉信号",
    sublabel: "金叉 / 死叉",
    defaultData: { threshold: 60, comparison: "cross_above" },
  },
  {
    category: "signal",
    type: "signal_threshold",
    label: "阈值信号",
    sublabel: "数值比较",
    defaultData: { threshold: 50, operator: "gte" },
  },
  {
    category: "risk",
    type: "risk_stop",
    label: "止损止盈",
    sublabel: "风控规则",
    defaultData: { stopLoss: 0.05, takeProfit: 0.15, positionSize: 0.2 },
  },
  {
    category: "execution",
    type: "execution_market",
    label: "市价执行",
    sublabel: "订单执行",
    defaultData: { orderType: "market", slippage: 0.001 },
  },
];

export function getHandles(category: NodeCategory): { inputs: string[]; outputs: string[] } {
  const map: Record<NodeCategory, { inputs: string[]; outputs: string[] }> = {
    datasource: { inputs: [], outputs: ["source"] },
    indicator: { inputs: ["indicator_in"], outputs: ["indicator_out"] },
    signal: { inputs: ["signal_in"], outputs: ["signal_out"] },
    risk: { inputs: ["risk_in"], outputs: ["risk_out"] },
    execution: { inputs: ["execution_in"], outputs: [] },
  };
  return map[category];
}

export function getCategoryColor(category: NodeCategory): string {
  const colors: Record<NodeCategory, string> = {
    datasource: "#00B8D9",
    indicator: "#FFD700",
    signal: "#4ECDC4",
    risk: "#FF6B6B",
    execution: "#A78BFA",
  };
  return colors[category];
}

export function validateConnection(
  sourceHandle: string | null,
  targetHandle: string | null
): boolean {
  if (!sourceHandle || !targetHandle) return false;
  const allowed = HANDLE_COMPATIBILITY[sourceHandle];
  return allowed ? allowed.includes(targetHandle) : false;
}
