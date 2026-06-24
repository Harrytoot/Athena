import type { StockDetail } from "@/types/stock";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getMarketOverview() {
  return fetchApi<{ marketRegime: string; temperature: number; indices: any; turnover: number; upCount: number; downCount: number; northbound: number; hotIndustries: any[]; hotConcepts: any[]; summary: string; updatedAt: string }>("/market/overview");
}

export async function getStockDetail(symbol: string): Promise<StockDetail> {
  return fetchApi<StockDetail>(`/stocks/${symbol}`);
}
