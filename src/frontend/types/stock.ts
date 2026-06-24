export interface MacdIndicator {
  diff: number;
  dea: number;
  histogram: number;
}

export interface TechnicalIndicators {
  ma5: number;
  ma20: number;
  rsi: number;
  macd: MacdIndicator;
}

export interface MoneyFlow {
  mainForceInflow: number;
  retailInflow: number;
  northboundInflow: number;
}

export interface AiAnalysis {
  summary: string;
  riskLevel: string;
  sentiment: string;
}

export interface StockDetail {
  symbol: string;
  name: string;
  price: number;
  changePct: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  turnover: number;
  peRatio?: number;
  pbRatio?: number;
  marketCap?: number;
  technicalIndicators: TechnicalIndicators;
  moneyFlow: MoneyFlow;
  aiAnalysis: AiAnalysis;
}
