const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface MarketOverview {
  marketRegime: "Bull" | "Bear" | "Range" | "Volatile";
  temperature: number;
  indices: {
    shanghai: { code: string; name: string; price: number; change_pct: number };
    shenzhen: { code: string; name: string; price: number; change_pct: number };
    chi_next: { code: string; name: string; price: number; change_pct: number };
  };
  turnover: number;
  upCount: number;
  downCount: number;
  northbound: number;
  hotIndustries: { name: string; change_pct: number }[];
  hotConcepts: { name: string; change_pct: number }[];
  summary: string;
  updatedAt: string;
}

export interface DashboardData {
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

export async function getMarketOverview(): Promise<MarketOverview> {
  return fetchApi<MarketOverview>("/market/overview");
}

export async function getDashboard(): Promise<DashboardData> {
  return fetchApi<DashboardData>("/dashboard");
}
