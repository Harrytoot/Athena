"use client";

import { useMemo } from "react";
import LightweightChart from "@/components/charts/LightweightChart";
import { generateMockKline } from "@/lib/mock-kline";

export default function StockChartPanel({ symbol }: { symbol: string }) {
  const mockData = useMemo(() => generateMockKline(symbol, 200), [symbol]);
  return <LightweightChart data={mockData} className="h-full w-full" />;
}
