export interface RecommendationItemDTO {
  symbol: string;
  name: string;
  action: "buy" | "sell" | "hold" | "watch";
  priority: 1 | 2 | 3;
  source: "technical" | "fundamental" | "portfolio" | "market" | "diversification";
  confidence: number;
  reason: string;
  detail?: string;
}

export interface RecommendationDTO {
  generatedAt: string;
  marketRegime: string;
  marketTemperature: number;
  items: RecommendationItemDTO[];
  summary: string;
}
