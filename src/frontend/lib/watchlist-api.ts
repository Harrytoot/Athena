import type { StockSearchResult, Watchlist } from "@/types/watchlist";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function getWatchlists(): Promise<Watchlist[]> {
  return request("/watchlists");
}

export async function createWatchlist(name: string, color?: string): Promise<Watchlist> {
  return request("/watchlists", {
    method: "POST",
    body: JSON.stringify({ name, color }),
  });
}

export async function deleteWatchlist(id: string): Promise<void> {
  return request(`/watchlists/${id}`, { method: "DELETE" });
}

export async function addStockItem(watchlistId: string, symbol: string, name: string, tags?: string[], note?: string): Promise<Watchlist> {
  return request(`/watchlists/${watchlistId}/items`, {
    method: "POST",
    body: JSON.stringify({ symbol, name, tags: tags || [], note: note || "" }),
  });
}

export async function removeStockItem(watchlistId: string, itemId: string): Promise<void> {
  return request(`/watchlists/${watchlistId}/items/${itemId}`, { method: "DELETE" });
}

export async function searchStocks(query: string): Promise<StockSearchResult[]> {
  return request(`/watchlists/stock/search?q=${encodeURIComponent(query)}`);
}
