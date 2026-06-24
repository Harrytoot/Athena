export interface PositionDTO {
  id: string;
  symbol: string;
  name: string;
  shares: number;
  costPrice: number;
  currentPrice?: number;
  marketValue: number;
  pnl: number;
  pnlPct: number;
  weightPct: number;
  createdAt: string;
}

export interface PortfolioDTO {
  id: string;
  name: string;
  cash: number;
  totalAssets: number;
  totalCost: number;
  totalMarketValue: number;
  totalPnl: number;
  totalPnlPct: number;
  positionCount: number;
  positions: PositionDTO[];
}

export interface PositionCreate {
  symbol: string;
  name: string;
  shares: number;
  costPrice: number;
}
