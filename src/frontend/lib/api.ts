import type { StockDetail } from "@/types/stock";
import type { DecisionDTO } from "@/types/decision";
import type { MarketOverview } from "@/types/market";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchApi<T>(path: string, timeoutMs = 15000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, { signal: controller.signal });
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }
    return res.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("数据源响应超时，请检查系统状态");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export async function getMarketOverview() {
  return fetchApi<MarketOverview>("/market/overview");
}

export async function getMarketScore() {
  return fetchApi<{
    score: number;
    regime: string;
    components: {
      csi300: { value: number; score: number; weight: number };
      turnover: { value: number; score: number; weight: number };
      breadth: { value: number; decliners: number; score: number; weight: number };
      northbound: { value: number; score: number; weight: number };
    };
    source: string;
    updatedAt: string;
  }>("/market/score");
}

export async function getStockDetail(symbol: string): Promise<StockDetail> {
  return fetchApi<StockDetail>(`/stocks/${symbol}`);
}

export async function getDecision(symbol: string): Promise<DecisionDTO> {
  return fetchApi<DecisionDTO>(`/decision/${symbol}`);
}
