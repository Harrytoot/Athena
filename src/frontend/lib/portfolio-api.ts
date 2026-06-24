import type { PortfolioDTO, PositionCreate } from "@/types/portfolio";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    if (res.status === 404) return null as T;
    if (res.status === 204) return undefined as T;
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export async function getPortfolio(): Promise<PortfolioDTO | null> {
  return request("/portfolio");
}

export async function createPortfolio(name: string, cash: number): Promise<PortfolioDTO> {
  return request("/portfolio", { method: "POST", body: JSON.stringify({ name, cash }) });
}

export async function addPosition(data: PositionCreate): Promise<PortfolioDTO | null> {
  return request("/portfolio/positions", { method: "POST", body: JSON.stringify(data) });
}

export async function updatePosition(positionId: string, data: { shares?: number; costPrice?: number }): Promise<PortfolioDTO | null> {
  return request(`/portfolio/positions/${positionId}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function deletePosition(positionId: string): Promise<void> {
  return request(`/portfolio/positions/${positionId}`, { method: "DELETE" });
}
