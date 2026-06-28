"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import type { BacktestResult } from "@/types/backtest";
import EquityChart from "@/components/charts/EquityChart";
import BacktestMetricsCharts from "@/components/charts/BacktestMetricsCharts";

function StatBox({ label, value, color, mono }: { label: string; value: string; color?: string; mono?: boolean }) {
  return (
    <div className="panel flex-1 p-3 text-center">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn("mt-1 text-lg font-bold", color ?? "text-foreground", mono && "font-mono")}>
        {value}
      </div>
    </div>
  );
}

function generateMockResult(): BacktestResult {
  const days = 120;
  const equityCurve = [];
  const benchmarkCurve = [];
  let nav = 1.0;
  let bench = 1.0;
  const trades = [];
  const start = new Date();
  start.setDate(start.getDate() - days);

  for (let i = 0; i < days; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    const time = d.toISOString().split("T")[0];
    nav *= 1 + (Math.random() - 0.48) * 0.02;
    bench *= 1 + (Math.random() - 0.5) * 0.015;
    equityCurve.push({ time, value: Math.round(nav * 10000) / 10000 });
    benchmarkCurve.push({ time, value: Math.round(bench * 10000) / 10000 });
    if (Math.random() < 0.1) {
      trades.push({ time, type: Math.random() > 0.5 ? "BUY" : "SELL", price: nav * 100 });
    }
  }

  return {
    totalObservations: days,
    signalCount: Math.floor(days * 0.4),
    longCount: Math.floor(days * 0.25),
    shortCount: Math.floor(days * 0.15),
    neutralCount: Math.floor(days * 0.6),
    scoreMin: 15,
    scoreMax: 88,
    scoreMean: 52,
    maxDrawdown: 0.12,
    annualReturn: 0.18,
    annualVolatility: 0.22,
    period5d: { ic: 0.045, rankIc: 0.052, sharpe: 1.2, winRate: 0.58, meanReturn: 0.002, nObservations: 115 },
    period10d: { ic: 0.062, rankIc: 0.071, sharpe: 1.5, winRate: 0.62, meanReturn: 0.004, nObservations: 110 },
    period20d: { ic: 0.078, rankIc: 0.085, sharpe: 1.8, winRate: 0.65, meanReturn: 0.007, nObservations: 100 },
    equityCurve,
    benchmarkCurve,
    trades,
    drawdownPeriods: [
      { maxDrawdown: 0.08, start: equityCurve[20]?.time ?? "", end: equityCurve[35]?.time ?? "", peakValue: 1.05, troughValue: 0.97 },
      { maxDrawdown: 0.12, start: equityCurve[60]?.time ?? "", end: equityCurve[80]?.time ?? "", peakValue: 1.12, troughValue: 0.99 },
    ],
  };
}

export default function BacktestPage() {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const { runBacktest } = await import("@/lib/backtest-api");
        const result = await runBacktest("000001", 120);
        if (!cancelled) { setData(result); setLoading(false); }
      } catch {
        if (!cancelled) {
          setData(generateMockResult());
          setLoading(false);
        }
      }
    }
    fetchData();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="font-mono text-sm text-muted-foreground animate-pulse">加载回测数据...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        回测数据不可用
      </div>
    );
  }

  const periodMetrics = [data.period5d, data.period10d, data.period20d];
  const bestSharpe = Math.max(...periodMetrics.map((p) => p.sharpe));
  const bestPeriod = periodMetrics.find((p) => p.sharpe === bestSharpe);

  return (
    <div className="flex h-full flex-col gap-3 p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-foreground">策略回测报告</h1>
        <span className="rounded bg-primary/15 px-2 py-0.5 font-mono text-xs text-primary">Mock Data</span>
        {error && <span className="text-xs text-down">{error}</span>}
      </div>

      {/* Summary Stats Row */}
      <div className="flex gap-3">
        <StatBox label="最优 Sharpe" value={bestSharpe.toFixed(3)} color="text-up" mono />
        <StatBox label="胜率" value={`${((bestPeriod?.winRate ?? 0) * 100).toFixed(1)}%`} color="text-up" />
        <StatBox label="最大回撤" value={`${((data.maxDrawdown ?? 0) * 100).toFixed(1)}%`} color="text-down" mono />
        <StatBox label="年化收益" value={`${((data.annualReturn ?? 0) * 100).toFixed(1)}%`} color="text-up" mono />
        <StatBox label="年化波动" value={`${((data.annualVolatility ?? 0) * 100).toFixed(1)}%`} color="text-muted-foreground" mono />
        <StatBox label="交易信号" value={`${data.signalCount}`} mono />
      </div>

      {/* Main Content: Equity Curve + Sidebar */}
      <div className="flex flex-1 gap-3 min-h-0">
        <div className="panel flex-1 overflow-hidden p-3">
          <h3 className="mb-2 text-sm font-semibold text-muted-foreground">
            净值曲线 <span className="font-normal text-up">策略</span> / <span className="font-normal text-muted-foreground">基准</span>
          </h3>
          <div className="h-[calc(100%-2rem)]">
            <EquityChart
              equityCurve={data.equityCurve}
              benchmarkCurve={data.benchmarkCurve}
              trades={data.trades}
              drawdownPeriods={data.drawdownPeriods}
              className="h-full w-full"
            />
          </div>
        </div>

        <div className="flex w-72 flex-shrink-0 flex-col gap-3">
          <BacktestMetricsCharts
            period5d={data.period5d}
            period10d={data.period10d}
            period20d={data.period20d}
          />

          {/* Period Metrics Table */}
          <div className="panel p-3">
            <h3 className="mb-2 text-sm font-semibold text-muted-foreground">分周期指标</h3>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted-foreground">
                  <th className="py-1 text-left font-medium">指标</th>
                  <th className="py-1 text-right font-medium">5日</th>
                  <th className="py-1 text-right font-medium">10日</th>
                  <th className="py-1 text-right font-medium">20日</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {(["ic", "rankIc", "sharpe", "winRate"] as const).map((key) => (
                  <tr key={key} className="border-t border-border/50">
                    <td className="py-1.5 text-muted-foreground">
                      {key === "ic" ? "IC" : key === "rankIc" ? "Rank IC" : key === "sharpe" ? "Sharpe" : "胜率"}
                    </td>
                    <td className={cn("py-1.5 text-right", (data.period5d[key] ?? 0) >= 0 ? "text-up" : "text-down")}>
                      {data.period5d[key]?.toFixed(key === "winRate" ? 2 : 4)}
                    </td>
                    <td className={cn("py-1.5 text-right", (data.period10d[key] ?? 0) >= 0 ? "text-up" : "text-down")}>
                      {data.period10d[key]?.toFixed(key === "winRate" ? 2 : 4)}
                    </td>
                    <td className={cn("py-1.5 text-right", (data.period20d[key] ?? 0) >= 0 ? "text-up" : "text-down")}>
                      {data.period20d[key]?.toFixed(key === "winRate" ? 2 : 4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Signal Distribution */}
          <div className="panel p-3">
            <h3 className="mb-2 text-sm font-semibold text-muted-foreground">信号分布</h3>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">总观测</span>
                <span className="font-mono text-foreground">{data.totalObservations}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-up">做多</span>
                <span className="font-mono text-up">{data.longCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-down">做空</span>
                <span className="font-mono text-down">{data.shortCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">中性</span>
                <span className="font-mono text-foreground">{data.neutralCount}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
