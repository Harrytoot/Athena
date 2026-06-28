"use client";

import { useCallback, useState } from "react";
import { useDebounce } from "@/hooks/useDebounce";
import { searchStocks } from "@/lib/watchlist-api";
import type { StockSearchResult } from "@/types/watchlist";

interface UseStockSearchReturn {
  query: string;
  results: StockSearchResult[];
  loading: boolean;
  setQuery: (q: string) => void;
  clearSearch: () => void;
}

export function useStockSearch(minChars: number = 1): UseStockSearchReturn {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const debouncedQuery = useDebounce(query, 300);

  const handleSearchRef = useCallback(async (q: string) => {
    if (q.length < minChars) {
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
  }, [minChars]);

  const clearSearch = useCallback(() => {
    setQuery("");
    setResults([]);
  }, []);

  return {
    query,
    results,
    loading,
    setQuery,
    clearSearch,
  };
}
