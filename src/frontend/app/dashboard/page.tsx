"use client";

import { useEffect, useState, useMemo } from "react";
import { getMarketOverview, getMarketScore } from "@/lib/api";
import type { MarketOverview, IndexData } from "@/types/market";
import { cn } from "@/lib/utils";

function Sparkline({ data, width = 80, height = 20, color }: { data: number[]; width?: number; height?: number; color: string }) {
  if (data.length < 2) return <svg width={width} height={height} />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * (width - 2) + 1},${height - ((v - min) / range) * (height - 4) - 2}`).join(" ");
  return (
    <svg width={width} height={height} className="shrink-0">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function generateSparklineData(base: number, volatility: number): number[] {
  const points = 30;
  const data: number[] = [];
  let val = base;
  for (let i = 0; i < points; i++) {
    val *= 1 + (Math.random() - 0.48) * volatility;
    data.push(val);
  }
  return data;
}

function TickerTape({ indices }: { indices: { shanghai: IndexData; shenzhen: IndexData; chi_next: IndexData } }) {
  const items = [
    { label: "上证", data: indices.shanghai, sparkData: useMemo(() => generateSparklineData(indices.shanghai.price, 0.008), [indices.shanghai.price]) },
    { label: "深证", data: indices.shenzhen, sparkData: useMemo(() => generateSparklineData(indices.shenzhen.price, 0.01), [indices.shenzhen.price]) },
    { label: "创业板", data: indices.chi_next, sparkData: useMemo(() => generateSparklineData(indices.chi_next.price, 0.012), [indices.chi_next.price]) },
  ];

  return (
    <div className="bento-card p-2 flex items-center gap-1 h-full">
      {items.map((item, idx) => {
        const isUp = item.data.change_pct >= 0;
        const color = isUp ? "#00B8D9" : "#FF5630";
        return (
          <div key={item.label} className={cn("flex-1 flex items-center gap-2 px-2", idx < 2 && "border-r border-divider")}>
            <div className="min-w-0 flex-1">
              <div className="text-[10px] text-muted-foreground leading-none">{item.label}</div>
              <div className="flex items-baseline gap-1.5 mt-0.5">
                <span className="font-mono text-sm font-bold text-foreground tabular-nums">
                  {item.data.price.toLocaleString("zh-CN", item.data.price >= 1000 ? { maximumFractionDigits: 0 } : { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className={cn("font-mono text-[10px] font-semibold tabular-nums", isUp ? "text-up" : "text-down")}>
                  {isUp ? "+" : ""}{item.data.change_pct.toFixed(2)}%
                </span>
              </div>
            </div>
            <Sparkline data={item.sparkData} width={60} height={20} color={color} />
          </div>
        );
      })}
    </div>
  );
}

function MarketBreadthChart({ upCount, downCount, flatCount, limitUp, limitDown }: {
  upCount: number; downCount: number; flatCount: number; limitUp?: number; limitDown?: number;
}) {
  const total = upCount + downCount + flatCount + (limitUp ?? 0) + (limitDown ?? 0) || 1;
  const lu = (limitUp ?? 0) / total * 100;
  const u = upCount / total * 100;
  const f = flatCount / total * 100;
  const d = downCount / total * 100;
  const ld = (limitDown ?? 0) / total * 100;

  const segments = [
    { width: lu, color: "#00B8D9", label: "涨停", count: limitUp ?? 0 },
    { width: u, color: "#0891A3", label: "上涨", count: upCount },
    { width: f, color: "#2A2E39", label: "平盘", count: flatCount },
    { width: d, color: "#E0442D", label: "下跌", count: downCount },
    { width: ld, color: "#FF5630", label: "跌停", count: limitDown ?? 0 },
  ];

  return (
    <div className="bento-card p-3 flex flex-col h-full">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">Market Breadth</div>
      <div className="flex-1 flex flex-col justify-center">
        <div className="flex h-6 rounded-sm overflow-hidden">
          {segments.map((s, i) => s.width > 0 && (
            <div key={i} style={{ width: `${s.width}%`, backgroundColor: s.color }} className="transition-all duration-500" />
          ))}
        </div>
        <div className="flex gap-4 mt-2 justify-center">
          {segments.filter(s => s.count > 0).map((s, i) => (
            <div key={i} className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: s.color }} />
              <span className="text-[10px] text-muted-foreground">{s.label}</span>
              <span className="font-mono text-[10px] text-foreground tabular-nums">{s.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function IndustryTreemap() {
  const sectors = useMemo(() => {
    const data = [
      { name: "电子", turnover: 1250, change: 2.3 },
      { name: "医药", turnover: 980, change: -0.8 },
      { name: "计算机", turnover: 870, change: 3.1 },
      { name: "电力设备", turnover: 720, change: 1.5 },
      { name: "汽车", turnover: 680, change: -1.2 },
      { name: "食品饮料", turnover: 550, change: 0.4 },
      { name: "非银金融", turnover: 520, change: 2.8 },
      { name: "银行", turnover: 480, change: -0.3 },
      { name: "通信", turnover: 420, change: 4.2 },
      { name: "有色", turnover: 380, change: -1.8 },
      { name: "化工", turnover: 340, change: 0.9 },
      { name: "传媒", turnover: 290, change: 1.7 },
      { name: "军工", turnover: 260, change: -0.5 },
      { name: "机械", turnover: 230, change: 1.1 },
      { name: "家电", turnover: 200, change: 2.0 },
      { name: "煤炭", turnover: 180, change: -2.5 },
      { name: "地产", turnover: 150, change: -0.7 },
      { name: "建装", turnover: 130, change: 0.3 },
      { name: "环保", turnover: 100, change: 1.2 },
      { name: "农业", turnover: 80, change: -1.0 },
    ];
    const total = data.reduce((s, d) => s + d.turnover, 0);
    return data.map((d) => ({ ...d, pct: (d.turnover / total * 100).toFixed(1) }));
  }, []);

  const [hovered, setHovered] = useState<number | null>(null);

  const cols = 10;
  const total = sectors.reduce((s, d) => s + d.turnover, 0);

  // Simple grid-based treemap approximation
  let row = 0; let col = 0;
  const totalCols = cols;

  return (
    <div className="bento-card p-3 flex flex-col h-full">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">Sector Flow</div>
      <div className="flex-1 flex flex-col justify-center">
        <div className="grid grid-cols-10 gap-1 flex-1">
          {sectors.map((sector, i) => {
            const colorIntensity = Math.abs(sector.change) / 5;
            const isUp = sector.change >= 0;
            const r = isUp ? Math.round(0 + colorIntensity * 20) : Math.round(20 + colorIntensity * 40);
            const g = isUp ? Math.round(30 + colorIntensity * 50) : Math.round(20 - colorIntensity * 10);
            const b = isUp ? Math.round(30 + colorIntensity * 30) : Math.round(10);
            const opacity = isUp ? 0.3 + colorIntensity * 0.5 : 0.3 + colorIntensity * 0.4;
            const span = Math.max(1, Math.round((sector.turnover / total) * totalCols * 2));
            return (
              <div
                key={sector.name}
                className="relative rounded-sm flex items-center justify-center text-center cursor-pointer transition-all duration-200 hover:ring-1 hover:ring-primary/50 hover:z-10"
                style={{
                  gridColumn: `span ${span}`,
                  minHeight: "28px",
                  backgroundColor: `rgba(${r}, ${g}, ${b}, ${opacity})`,
                }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              >
                <span className={cn("text-[9px] font-medium leading-none truncate px-0.5", isUp ? "text-up" : "text-down")}>
                  {sector.name}
                </span>
                {hovered === i && (
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-card border border-border rounded px-2 py-1 whitespace-nowrap z-20 shadow-lg">
                    <div className="text-[10px] font-semibold text-foreground">{sector.name}</div>
                    <div className="flex gap-2 mt-0.5">
                      <span className="text-[9px] text-muted-foreground">成交 {sector.turnover}亿</span>
                      <span className={cn("font-mono text-[9px]", isUp ? "text-up" : "text-down")}>
                        {isUp ? "+" : ""}{sector.change}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function MarketSentimentGauge({ score }: { score: number }) {
  const angle = (score / 100) * 180;
  const color = score >= 70 ? "#00B8D9" : score >= 40 ? "#EAB308" : "#FF5630";
  const label = score >= 70 ? "Bullish" : score >= 40 ? "Neutral" : "Bearish";

  return (
    <div className="bento-card p-3 flex flex-col items-center justify-center h-full">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-1">Market Sentiment</div>
      <svg viewBox="0 0 120 70" className="w-full max-w-[120px]">
        <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="#2A2E39" strokeWidth="10" strokeLinecap="round" />
        <path
          d="M 10 60 A 50 50 0 0 1 110 60"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${(angle / 180) * 157} 157`}
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
        <text x="60" y="48" textAnchor="middle" className="font-mono text-xl font-bold" fill={color}>
          {Math.round(score)}
        </text>
        <text x="60" y="60" textAnchor="middle" className="text-[9px]" fill="#8B95A5">
          {label}
        </text>
      </svg>
    </div>
  );
}

function isEmptyMarketData(data: MarketOverview): boolean {
  return (
    data.indices.shanghai.price === 0 &&
    data.temperature === 0 &&
    data.turnover === 0 &&
    data.upCount === 0 &&
    data.downCount === 0
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<MarketOverview | null>(null);
  const [scoreData, setScoreData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const overview = await getMarketOverview();
        if (cancelled) return;
        setData(overview);
        try {
          const score = await getMarketScore();
          if (!cancelled) setScoreData(score);
        } catch {}
      } catch {
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchData();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="font-mono text-xs text-muted-foreground animate-pulse">正在连接数据源...</div>
      </div>
    );
  }

  if (error || !data || isEmptyMarketData(data)) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg font-medium">等待数据就绪</div>
          <div className="mt-1 text-xs">请确保后端服务已启动</div>
        </div>
      </div>
    );
  }

  const sentimentScore = scoreData?.score ?? data.temperature;

  return (
    <div className="h-full p-2 flex flex-col gap-2">
      {/* Top: Ticker Tape + Sentiment Gauge */}
      <div className="flex gap-2" style={{ height: "14%" }}>
        <div className="flex-[3]" style={{ minWidth: 0 }}>
          <TickerTape indices={data.indices} />
        </div>
        <div className="flex-1" style={{ minWidth: 0 }}>
          <MarketSentimentGauge score={sentimentScore} />
        </div>
      </div>

      {/* Bottom: Market Breadth + Treemap */}
      <div className="flex gap-2 flex-1" style={{ height: "86%" }}>
        <div className="flex-1" style={{ minWidth: 0 }}>
          <MarketBreadthChart
            upCount={data.upCount}
            downCount={data.downCount}
            flatCount={Math.max(0, 4500 - data.upCount - data.downCount)}
            limitUp={Math.floor(data.upCount * 0.05)}
            limitDown={Math.floor(data.downCount * 0.05)}
          />
        </div>
        <div className="flex-[3]" style={{ minWidth: 0 }}>
          <IndustryTreemap />
        </div>
      </div>
    </div>
  );
}
