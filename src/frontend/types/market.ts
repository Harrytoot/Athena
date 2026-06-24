export interface IndexData {
  code: string;
  name: string;
  price: number;
  change_pct: number;
}

export interface HotItem {
  name: string;
  change_pct: number;
}

export interface MarketOverview {
  marketRegime: "Bull" | "Bear" | "Range" | "Volatile";
  temperature: number;
  indices: {
    shanghai: IndexData;
    shenzhen: IndexData;
    chi_next: IndexData;
  };
  turnover: number;
  upCount: number;
  downCount: number;
  northbound: number;
  hotIndustries: HotItem[];
  hotConcepts: HotItem[];
  summary: string;
  updatedAt: string;
}

export interface DashboardSummary {
  totalAssets: number;
  totalReturnPct: number;
  watchlistCount: number;
  positionCount: number;
  marketRegime: string;
  temperature: number;
  shanghaiChangePct: number;
  shenzhenChangePct: number;
  turnover: number;
  upCount: number;
  downCount: number;
  updatedAt: string;
}
