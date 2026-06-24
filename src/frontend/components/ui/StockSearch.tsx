"use client";

import { useState } from "react";
import type { StockSearchResult } from "@/types/watchlist";
import { searchStocks } from "@/lib/watchlist-api";

export function StockSearch({
  onSelect,
}: {
  onSelect: (stock: StockSearchResult) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (q: string) => {
    setQuery(q);
    if (q.length < 1) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const data = await searchStocks(q);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => handleSearch(e.target.value)}
        placeholder="搜索股票代码或名称..."
        className="w-80 rounded-lg border px-3 py-2 text-sm outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
      />

      {results.length > 0 && (
        <div className="absolute z-10 mt-1 w-80 rounded-lg border bg-white shadow-lg">
          {results.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => {
                onSelect(stock);
                setQuery("");
                setResults([]);
              }}
              className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-gray-50"
            >
              <span>
                <span className="font-medium text-gray-900">{stock.symbol}</span>
                <span className="ml-2 text-gray-600">{stock.name}</span>
              </span>
              <span className="text-xs text-gray-400">{stock.market === "SH" ? "沪" : "深"}</span>
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="absolute right-3 top-2.5">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        </div>
      )}
    </div>
  );
}
