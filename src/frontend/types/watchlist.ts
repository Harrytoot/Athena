export interface WatchlistItem {
  id: string;
  symbol: string;
  name: string;
  tags: string[];
  note: string;
  sortOrder: number;
  currentPrice?: number;
  changePct?: number;
  createdAt: string;
}

export interface Watchlist {
  id: string;
  name: string;
  color: string;
  sortOrder: number;
  items: WatchlistItem[];
  itemCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  market: string;
}
