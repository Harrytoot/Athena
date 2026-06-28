export type OrderType = "MARKET" | "LIMIT" | "TWAP" | "VWAP";

export type TradeSide = "BUY" | "SELL";

export interface AlgoParams {
  durationMinutes?: number;
  maxParticipationRate?: number;
}

export interface ExecutionPreviewRequest {
  symbol: string;
  side: TradeSide;
  size: number;
  orderType: OrderType;
  price: number;
  limitPrice?: number;
  algoParams?: AlgoParams;
}

export interface ExecutionPreviewResponse {
  slippageBps: number;
  slippageAmount: number;
  marketImpactBps: number;
  marketImpactAmount: number;
  estimatedAvgPrice: number;
  estimatedTotalCost: number;
  participationRate: number;
  dailyVolatility: number;
  stressTestLoss: number;
  stressTestScenario: string;
  note: string;
}

export interface PaperTradeRequest {
  symbol: string;
  side: TradeSide;
  size: number;
  orderType: OrderType;
  price: number;
  limitPrice?: number;
  algoParams?: AlgoParams;
}

export interface PaperTradeResponse {
  orderId: string;
  status: string;
  symbol: string;
  side: string;
  size: number;
  filledPrice: number;
  submittedAt: string;
}

export interface ExecutionSheetContext {
  symbol: string;
  name: string;
  price: number;
  side: TradeSide;
  defaultSize: number;
}
