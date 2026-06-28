import type { BacktestResult } from "@/types/backtest";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function runBacktest(symbol: string = "000001", days: number = 120): Promise<BacktestResult> {
  const res = await fetch(`${API_BASE}/backtest/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, days }),
  });
  if (!res.ok) {
    throw new Error(`Backtest API error: ${res.status}`);
  }
  return res.json();
}
