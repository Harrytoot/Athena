"use client";

import { useEffect, useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import type { BacktestResult, TradeMark } from "@/types/backtest";

function generateMockResult(): BacktestResult {
  const days = 120;
  const equityCurve = [];
  const benchmarkCurve = [];
  let nav = 1.0;
  let bench = 1.0;
  const trades: TradeMark[] = [];
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
  }

  return {
    totalObservations: days,
    signalCount: Math.floor(days * 0.4),
    longCount: Math.floor(days * 0.25), shortCount: Math.floor(days * 0.15), neutralCount: Math.floor(days * 0.6),
    scoreMin: 15, scoreMax: 88, scoreMean: 52,
    maxDrawdown: 0.12, annualReturn: 0.18, annualVolatility: 0.22,
    period5d: { ic: 0.045, rankIc: 0.052, sharpe: 1.2, winRate: 0.58, meanReturn: 0.002, nObservations: 115 },
    period10d: { ic: 0.062, rankIc: 0.071, sharpe: 1.5, winRate: 0.62, meanReturn: 0.004, nObservations: 110 },
    period20d: { ic: 0.078, rankIc: 0.085, sharpe: 1.8, winRate: 0.65, meanReturn: 0.007, nObservations: 100 },
    equityCurve, benchmarkCurve, trades,
    drawdownPeriods: [
      { maxDrawdown: 0.08, start: equityCurve[20]?.time ?? "", end: equityCurve[35]?.time ?? "", peakValue: 1.05, troughValue: 0.97 },
      { maxDrawdown: 0.12, start: equityCurve[60]?.time ?? "", end: equityCurve[80]?.time ?? "", peakValue: 1.12, troughValue: 0.99 },
    ],
  };
}

function KpiMatrix({ data }: { data: BacktestResult }) {
  const metrics = [
    { label: "年化收益", value: `${((data.annualReturn ?? 0) * 100).toFixed(1)}%`, color: "text-up" },
    { label: "Sharpe", value: (data.period20d?.sharpe ?? 0).toFixed(2), color: "text-up" },
    { label: "最大回撤", value: `${((data.maxDrawdown ?? 0) * 100).toFixed(1)}%`, color: "text-down" },
    { label: "胜率", value: `${((data.period20d?.winRate ?? 0) * 100).toFixed(1)}%`, color: "text-up" },
    { label: "盈亏比", value: "2.1", color: "text-foreground" },
    { label: "年化波动", value: `${((data.annualVolatility ?? 0) * 100).toFixed(1)}%`, color: "text-muted-foreground" },
    { label: "信号数", value: `${data.signalCount}`, color: "text-foreground" },
    { label: "IC均值", value: (data.period20d?.ic ?? 0).toFixed(3), color: "text-up" },
  ];

  return (
    <div className="bento-card p-3 flex flex-col">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">KPI Matrix</div>
      <div className="grid grid-cols-1 gap-1 flex-1">
        {metrics.map((m) => (
          <div key={m.label} className="flex items-center justify-between px-2 py-1 rounded hover:bg-secondary/20">
            <span className="text-[10px] text-muted-foreground">{m.label}</span>
            <span className={cn("font-mono text-xs font-semibold tabular-nums", m.color)}>{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CombinedChart({ data }: { data: BacktestResult }) {
  const navData = data.equityCurve;
  const benchData = data.benchmarkCurve;

  const allValues = [...navData.map((d) => d.value), ...benchData.map((d) => d.value)];
  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);
  const valRange = maxVal - minVal || 1;

  // Calculate drawdown
  const ddData: { time: string; dd: number; peak: number }[] = [];
  let runningPeak = 0;
  for (const d of navData) {
    runningPeak = Math.max(runningPeak, d.value);
    const dd = runningPeak > 0 ? (runningPeak - d.value) / runningPeak : 0;
    ddData.push({ time: d.time, dd, peak: runningPeak });
  }

  const maxDD = Math.max(...ddData.map((d) => d.dd), 0.01);

  const W = 600; const H = 280;
  const navH = H * 0.65;
  const ddH = H * 0.35;
  const padX = 45; const padY = 15;

  const scaleX = (i: number) => padX + (i / (navData.length - 1)) * (W - padX - 10);
  const scaleNavY = (v: number) => navH - padY - ((v - minVal) / valRange) * (navH - padY * 2);
  const scaleDdY = (v: number) => H - padY - (v / maxDD) * (ddH - padY * 1.5);

  const navPath = navData.map((d, i) => `${i === 0 ? "M" : "L"}${scaleX(i)},${scaleNavY(d.value)}`).join(" ");
  const benchPath = benchData.map((d, i) => `${i === 0 ? "M" : "L"}${scaleX(i)},${scaleNavY(d.value)}`).join(" ");

  const ddAreaPath = ddData.map((d, i) => {
    const x = scaleX(i);
    const y = scaleDdY(d.dd);
    const base = scaleDdY(0);
    return i === 0 ? `M${x},${base} L${x},${y}` : `L${x},${base} L${x},${y}`;
  }).join(" ") + ` L${scaleX(ddData.length - 1)},${scaleDdY(0)} Z`;

  const yTicks = 4;
  const yTickVals = Array.from({ length: yTicks }, (_, i) => minVal + (valRange * i) / (yTicks - 1));

  return (
    <div className="bento-card p-3 flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">NAV & Drawdown</span>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-[9px]"><span className="h-1.5 w-3 rounded-full bg-up" />策略</span>
          <span className="flex items-center gap-1 text-[9px]"><span className="h-px w-3 border-t border-dashed border-muted-foreground/40" />基准</span>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          {/* Divider line */}
          <line x1={padX} y1={navH} x2={W - 10} y2={navH} stroke="#232838" strokeWidth="0.5" strokeDasharray="3,3" />

          {/* Y-axis labels */}
          {yTickVals.map((v, i) => (
            <text key={i} x={padX - 5} y={scaleNavY(v) + 4} textAnchor="end" className="text-[7px]" fill="#5A6270">
              {v.toFixed(2)}
            </text>
          ))}

          {/* Underwater fill */}
          <path d={ddAreaPath} fill="rgba(255,86,48,0.15)" stroke="none" />

          {/* Benchmark line */}
          <path d={benchPath} fill="none" stroke="#5A6270" strokeWidth="1" strokeDasharray="3,3" />

          {/* Strategy NAV line */}
          <path d={navPath} fill="none" stroke="#00B8D9" strokeWidth="1.5" />

          {/* DD annotation */}
          <text x={W - 10} y={scaleDdY(maxDD) + 4} textAnchor="end" className="text-[7px]" fill="#FF5630">
            DD {(-maxDD * 100).toFixed(1)}%
          </text>
        </svg>
      </div>
    </div>
  );
}

function MonthlyHeatmap() {
  const years = 3;
  const months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"];

  const data = useMemo(() => {
    return Array.from({ length: years }, () =>
      months.map(() => (Math.random() - 0.45) * 0.15)
    );
  }, []);

  const maxAbs = Math.max(...data.flat().map(Math.abs), 0.001);

  return (
    <div className="bento-card p-3 flex flex-col">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">
        Monthly Returns Heatmap
      </div>
      <div className="flex-1 flex flex-col justify-center">
        <div className="flex gap-1 justify-center">
          {months.map((m) => (
            <div key={m} className="text-[8px] text-muted-foreground w-8 text-center">{m}月</div>
          ))}
        </div>
        {data.map((yearData, yi) => (
          <div key={yi} className="flex items-center gap-1 mt-1 justify-center">
            <span className="text-[8px] text-muted-foreground w-6 text-right mr-1">Y{yi + 1}</span>
            {yearData.map((val, mi) => {
              const intensity = Math.abs(val) / maxAbs;
              const isUp = val >= 0;
              const r = isUp ? Math.round(0 + intensity * 20) : Math.round(25 + intensity * 60);
              const g = isUp ? Math.round(25 + intensity * 50) : Math.round(5);
              const b = isUp ? Math.round(20 + intensity * 30) : Math.round(5);
              return (
                <div
                  key={mi}
                  className="w-8 h-6 rounded-sm flex items-center justify-center text-[8px] font-mono font-semibold tabular-nums"
                  style={{ backgroundColor: `rgba(${r},${g},${b},${0.3 + intensity * 0.5})`, color: isUp ? "#00B8D9" : "#FF5630" }}
                  title={`${(val * 100).toFixed(1)}%`}
                >
                  {val >= 0 ? "+" : ""}{(val * 100).toFixed(1)}%
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function BacktestPage() {
  const [data, setData] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(true);

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
        <div className="font-mono text-xs text-muted-foreground animate-pulse">加载回测数据...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground text-xs">回测数据不可用</div>
    );
  }

  return (
    <div className="h-full p-2 flex flex-col gap-2">
      {/* Header */}
      <div className="flex items-center gap-3 px-1 shrink-0">
        <h1 className="text-sm font-bold text-foreground">策略回测报告</h1>
        <span className="rounded bg-primary/15 px-2 py-0.5 text-[9px] text-primary">Tearsheet</span>
      </div>

      {/* Main: KPI Matrix + Chart */}
      <div className="flex gap-2 flex-1 min-h-0">
        <div className="w-44 shrink-0">
          <KpiMatrix data={data} />
        </div>

        <div className="flex-1 min-w-0">
          <CombinedChart data={data} />
        </div>
      </div>

      {/* Bottom: Monthly Heatmap */}
      <div className="shrink-0" style={{ height: "28%" }}>
        <MonthlyHeatmap />
      </div>
    </div>
  );
}
