"use client";

import { useCallback, useEffect, useState } from "react";
import type { PortfolioDTO } from "@/types/portfolio";
import { addPosition, createPortfolio, getPortfolio } from "@/lib/portfolio-api";
import { searchStocks } from "@/lib/watchlist-api";
import type { StockSearchResult } from "@/types/watchlist";
import { cn } from "@/lib/utils";

function formatMoney(v: number) {
  const n = Number(v);
  if (Math.abs(n) >= 1e8) return `${(n / 1e8).toFixed(2)}亿`;
  if (Math.abs(n) >= 1e4) return `${(n / 1e4).toFixed(2)}万`;
  return n.toFixed(2);
}

function KpiCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="flex-1 px-3 py-1.5 border-r border-divider last:border-r-0">
      <div className="text-[9px] text-muted-foreground uppercase tracking-wide">{label}</div>
      <div className={cn("font-mono text-sm font-bold tabular-nums mt-0.5", color ?? "text-foreground")}>
        {value}
      </div>
      {sub && <div className="text-[9px] text-muted-foreground mt-0.5">{sub}</div>}
    </div>
  );
}

function ExposureDonut({ portfolio }: { portfolio: PortfolioDTO }) {
  const total = portfolio.totalAssets || 1;
  const stockPct = (portfolio.totalMarketValue / total) * 100;
  const cashPct = 100 - stockPct;
  const circumference = 2 * Math.PI * 30;

  return (
    <div className="bento-card p-3 flex flex-col h-full">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">Exposure</div>
      <div className="flex-1 flex items-center justify-center gap-4">
        <svg viewBox="0 0 72 72" className="w-28 h-28">
          <circle cx="36" cy="36" r="30" fill="none" stroke="#2A2E39" strokeWidth="8" />
          <circle cx="36" cy="36" r="30" fill="none" stroke="#00B8D9" strokeWidth="8"
            strokeDasharray={`${(stockPct / 100) * circumference} ${circumference}`}
            strokeLinecap="round" transform="rotate(-90 36 36)"
            style={{ transition: "stroke-dasharray 0.5s ease" }}
          />
          <text x="36" y="34" textAnchor="middle" className="font-mono text-sm font-bold" fill="currentColor">
            {stockPct.toFixed(0)}%
          </text>
          <text x="36" y="46" textAnchor="middle" className="text-[8px]" fill="#8B95A5">
            Stock
          </text>
        </svg>
        <div className="space-y-2 text-[10px]">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-up" />
            <span className="text-muted-foreground">股票</span>
            <span className="font-mono text-foreground tabular-nums">{formatMoney(portfolio.totalMarketValue)}</span>
            <span className="font-mono text-up">({stockPct.toFixed(1)}%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-muted-foreground/40" />
            <span className="text-muted-foreground">现金</span>
            <span className="font-mono text-foreground tabular-nums">{formatMoney(portfolio.cash)}</span>
            <span className="font-mono text-muted-foreground">({cashPct.toFixed(1)}%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function PerformanceMiniChart({ portfolio }: { portfolio: PortfolioDTO }) {
  const points = 40;
  const data = Array.from({ length: points }, (_, i) => {
    const t = i / points;
    return {
      strat: 1 + t * (0.05 + Math.sin(t * 8) * 0.03) + (Math.random() - 0.5) * 0.01,
      bench: 1 + t * 0.02 + (Math.random() - 0.5) * 0.008,
    };
  });

  const allVals = data.flatMap((d) => [d.strat, d.bench]);
  const min = Math.min(...allVals);
  const max = Math.max(...allVals);
  const range = max - min || 1;
  const w = 300; const h = 100;
  const toY = (v: number) => h - ((v - min) / range) * (h - 6) - 3;

  const stratPath = data.map((d, i) => `${i === 0 ? "M" : "L"}${(i / (points - 1)) * (w - 4) + 2},${toY(d.strat)}`).join(" ");
  const benchPath = data.map((d, i) => `${i === 0 ? "M" : "L"}${(i / (points - 1)) * (w - 4) + 2},${toY(d.bench)}`).join(" ");

  return (
    <div className="bento-card p-3 flex flex-col h-full">
      <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">NAV vs HS300</div>
      <div className="flex-1 flex items-center justify-center">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          <path d={benchPath} fill="none" stroke="#4A5568" strokeWidth="1" strokeDasharray="3,2" />
          <path d={stratPath} fill="none" stroke="#00B8D9" strokeWidth="1.5" />
        </svg>
      </div>
      <div className="flex items-center gap-3 mt-1">
        <div className="flex items-center gap-1">
          <span className="h-1.5 w-4 rounded-full bg-up" />
          <span className="text-[9px] text-up">策略</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="h-px w-4 border-t border-dashed border-[#4A5568]" />
          <span className="text-[9px] text-muted-foreground">HS300</span>
        </div>
      </div>
    </div>
  );
}

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [symbol, setSymbol] = useState("");
  const [stockName, setStockName] = useState("");
  const [shares, setShares] = useState(0);
  const [costPrice, setCostPrice] = useState(0);
  const [searchResults, setSearchResults] = useState<StockSearchResult[]>([]);

  const refresh = useCallback(async () => {
    try {
      const data = await getPortfolio();
      setPortfolio(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleSearch = async (q: string) => {
    setSymbol(q);
    if (q.length > 1) {
      try { setSearchResults(await searchStocks(q)); } catch { setSearchResults([]); }
    } else { setSearchResults([]); }
  };

  const selectStock = (stock: StockSearchResult) => {
    setSymbol(stock.symbol); setStockName(stock.name); setSearchResults([]);
  };

  const handleAddPosition = async () => {
    if (!symbol || !shares || !costPrice) return;
    try {
      const result = await addPosition({ symbol, name: stockName || symbol, shares, costPrice });
      if (result) {
        setPortfolio(result); setShowAddForm(false);
        setSymbol(""); setStockName(""); setShares(0); setCostPrice(0);
      }
    } catch {}
  };

  if (loading) {
    return <div className="flex h-full items-center justify-center"><div className="font-mono text-xs text-muted-foreground animate-pulse">加载组合数据...</div></div>;
  }

  if (!portfolio) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="text-sm font-medium text-muted-foreground">尚未创建投资组合</div>
          <button onClick={async () => {
            const name = prompt("投资组合名称：", "我的组合");
            if (!name) return;
            const cash = prompt("初始现金（元）：", "1000000");
            if (!cash) return;
            try { const data = await createPortfolio(name, parseFloat(cash)); setPortfolio(data); } catch {}
          }} className="mt-3 rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/80">
            创建投资组合
          </button>
        </div>
      </div>
    );
  }

  const isUp = portfolio.totalPnl >= 0;

  return (
    <div className="h-full flex flex-col">
      {/* Top KPI Bar */}
      <div className="flex items-center border-b border-divider bg-card/50 px-2 shrink-0">
        <div className="flex items-center gap-2 px-2 py-1.5">
          <span className="text-[11px] font-semibold text-foreground">{portfolio.name}</span>
          <button onClick={() => setShowAddForm(!showAddForm)} className="text-[10px] px-2 py-0.5 rounded bg-primary/20 text-primary hover:bg-primary/30">
            {showAddForm ? "取消" : "+ 持仓"}
          </button>
        </div>
        <div className="flex flex-1">
          <KpiCard label="总资产" value={`¥${formatMoney(portfolio.totalAssets)}`} />
          <KpiCard label="可用" value={`¥${formatMoney(portfolio.cash)}`} />
          <KpiCard label="当日PnL" value={`${isUp ? "+" : ""}${formatMoney(portfolio.totalPnl)}`} color={isUp ? "text-up" : "text-down"} sub="今日" />
          <KpiCard label="收益率" value={`${isUp ? "+" : ""}${portfolio.totalPnlPct.toFixed(2)}%`} color={isUp ? "text-up" : "text-down"} />
        </div>
      </div>

      {/* Add Position Form */}
      {showAddForm && (
        <div className="border-b border-divider bg-card/30 px-3 py-2">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input type="text" value={symbol} onChange={(e) => handleSearch(e.target.value)} placeholder="代码" className="w-full rounded border border-border bg-background px-2 py-1 text-[11px] text-foreground" />
              {searchResults.length > 0 && (
                <div className="absolute z-10 mt-0.5 w-full rounded border border-border bg-card shadow-lg">
                  {searchResults.map((s) => (
                    <button key={s.symbol} onClick={() => selectStock(s)} className="block w-full px-2 py-1 text-left text-[11px] text-foreground hover:bg-secondary">
                      {s.symbol} {s.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <input type="text" value={stockName} onChange={(e) => setStockName(e.target.value)} placeholder="名称" className="flex-1 rounded border border-border bg-background px-2 py-1 text-[11px] text-foreground" />
            <input type="number" value={shares || ""} onChange={(e) => setShares(Number(e.target.value))} placeholder="股数" className="w-20 rounded border border-border bg-background px-2 py-1 text-[11px] text-foreground" />
            <input type="number" value={costPrice || ""} onChange={(e) => setCostPrice(Number(e.target.value))} placeholder="成本" className="w-24 rounded border border-border bg-background px-2 py-1 text-[11px] text-foreground" />
            <button onClick={handleAddPosition} className="rounded bg-primary px-3 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/80">确认</button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col gap-2 p-2 min-h-0">
        {/* Middle: Charts Row */}
        <div className="flex gap-2" style={{ height: "40%" }}>
          <div className="flex-1" style={{ minWidth: 0 }}>
            <ExposureDonut portfolio={portfolio} />
          </div>
          <div className="flex-[2]" style={{ minWidth: 0 }}>
            <PerformanceMiniChart portfolio={portfolio} />
          </div>
        </div>

        {/* Bottom: Position Table */}
        <div className="bento-card flex-1 flex flex-col min-h-0">
          <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground px-3 py-2 border-b border-divider">
            持仓明细 ({portfolio.positionCount})
          </div>
          <div className="flex-1 overflow-auto">
            <table className="w-full">
              <thead className="sticky top-0 z-10 bg-card">
                <tr className="text-[10px] font-semibold text-muted-foreground uppercase border-b border-divider">
                  <th className="px-3 py-1.5 text-left w-[80px]">代码</th>
                  <th className="px-3 py-1.5 text-left w-[80px]">名称</th>
                  <th className="px-3 py-1.5 text-right w-[70px]">股数</th>
                  <th className="px-3 py-1.5 text-right w-[70px]">成本</th>
                  <th className="px-3 py-1.5 text-right w-[70px]">现价</th>
                  <th className="px-3 py-1.5 text-right w-[80px]">市值</th>
                  <th className="px-3 py-1.5 text-right w-[70px]">仓位%</th>
                  <th className="px-3 py-1.5 text-right w-[80px]">浮盈%</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.positions.length === 0 ? (
                  <tr><td colSpan={8} className="px-3 py-16 text-center text-[11px] text-muted-foreground">暂无持仓</td></tr>
                ) : (
                  portfolio.positions.map((pos) => {
                    const pnlUp = pos.pnl >= 0;
                    return (
                      <tr key={pos.id} className="border-b border-divider/30 text-[11px] hover:bg-secondary/20">
                        <td className="px-3 py-1.5 font-mono text-primary">{pos.symbol}</td>
                        <td className="px-3 py-1.5 text-foreground/80">{pos.name}</td>
                        <td className="px-3 py-1.5 font-mono text-right tabular-nums text-foreground">{pos.shares.toLocaleString()}</td>
                        <td className="px-3 py-1.5 font-mono text-right tabular-nums text-muted-foreground">{pos.costPrice.toFixed(2)}</td>
                        <td className="px-3 py-1.5 font-mono text-right tabular-nums text-muted-foreground">{pos.currentPrice?.toFixed(2) ?? "--"}</td>
                        <td className="px-3 py-1.5 font-mono text-right tabular-nums text-foreground">{formatMoney(pos.marketValue)}</td>
                        <td className="px-3 py-1.5 font-mono text-right tabular-nums text-muted-foreground">{pos.weightPct.toFixed(1)}%</td>
                        <td className={cn("px-3 py-1.5 font-mono text-right tabular-nums font-semibold", pnlUp ? "text-up" : "text-down")}>
                          {pnlUp ? "+" : ""}{pos.pnlPct.toFixed(2)}%
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
