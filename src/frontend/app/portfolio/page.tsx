"use client";

import { useCallback, useEffect, useState } from "react";
import type { PortfolioDTO } from "@/types/portfolio";
import { addPosition, createPortfolio, deletePosition, getPortfolio } from "@/lib/portfolio-api";
import { searchStocks } from "@/lib/watchlist-api";
import type { StockSearchResult } from "@/types/watchlist";
import { cn } from "@/lib/utils";

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [symbol, setSymbol] = useState("");
  const [shares, setShares] = useState(0);
  const [costPrice, setCostPrice] = useState(0);
  const [searchResults, setSearchResults] = useState<StockSearchResult[]>([]);
  const [stockName, setStockName] = useState("");

  const refresh = useCallback(async () => {
    try {
      const data = await getPortfolio();
      setPortfolio(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleCreatePortfolio = async () => {
    const name = prompt("投资组合名称：", "我的组合");
    if (!name) return;
    const cash = prompt("初始现金（元）：", "1000000");
    if (!cash) return;
    try {
      const data = await createPortfolio(name, parseFloat(cash));
      setPortfolio(data);
    } catch {}
  };

  const handleSearch = async (q: string) => {
    setSymbol(q);
    if (q.length > 1) {
      try {
        const results = await searchStocks(q);
        setSearchResults(results);
      } catch { setSearchResults([]); }
    } else {
      setSearchResults([]);
    }
  };

  const selectStock = (stock: StockSearchResult) => {
    setSymbol(stock.symbol);
    setStockName(stock.name);
    setSearchResults([]);
  };

  const handleAddPosition = async () => {
    if (!symbol || !shares || !costPrice) return;
    try {
      const result = await addPosition({ symbol, name: stockName || symbol, shares, costPrice });
      if (result) {
        setPortfolio(result);
        setShowAddForm(false);
        setSymbol("");
        setStockName("");
        setShares(0);
        setCostPrice(0);
      }
    } catch {}
  };

  const handleDeletePosition = async (positionId: string) => {
    try {
      await deletePosition(positionId);
      await refresh();
    } catch {}
  };

  if (loading) return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" /></div>;

  if (!portfolio) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-lg font-medium text-gray-700">尚未创建投资组合</div>
          <button onClick={handleCreatePortfolio} className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
            创建投资组合
          </button>
        </div>
      </div>
    );
  }

  const isUp = portfolio.totalPnl >= 0;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">{portfolio.name}</h1>

        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard label="总资产" value={formatMoney(portfolio.totalAssets)} />
          <SummaryCard label="持仓市值" value={formatMoney(portfolio.totalMarketValue)} />
          <SummaryCard label="现金" value={formatMoney(portfolio.cash)} />
          <SummaryCard
            label="浮动盈亏"
            value={`${isUp ? "+" : ""}${formatMoney(portfolio.totalPnl)}`}
            valueClass={isUp ? "text-red-600" : "text-green-600"}
            sub={`${isUp ? "+" : ""}${portfolio.totalPnlPct.toFixed(2)}%`}
            subClass={isUp ? "text-red-500" : "text-green-500"}
          />
        </div>

        {/* Positions */}
        <div className="rounded-lg border bg-white shadow-sm">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h2 className="font-semibold text-gray-700">持仓明细 ({portfolio.positionCount})</h2>
            <button
              onClick={() => setShowAddForm(true)}
              className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
            >
              + 添加持仓
            </button>
          </div>

          {showAddForm && (
            <div className="border-b p-4">
              <div className="grid grid-cols-4 gap-3">
                <div className="relative">
                  <input
                    type="text" value={symbol}
                    onChange={(e) => handleSearch(e.target.value)}
                    placeholder="股票代码"
                    className="w-full rounded border px-2 py-1.5 text-sm"
                  />
                  {searchResults.length > 0 && (
                    <div className="absolute z-10 mt-1 w-full rounded border bg-white shadow-lg">
                      {searchResults.map((s) => (
                        <button key={s.symbol} onClick={() => selectStock(s)} className="block w-full px-2 py-1 text-left text-sm hover:bg-gray-50">
                          {s.symbol} {s.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <input type="text" value={stockName} onChange={(e) => setStockName(e.target.value)} placeholder="股票名称" className="rounded border px-2 py-1.5 text-sm" />
                <input type="number" value={shares || ""} onChange={(e) => setShares(Number(e.target.value))} placeholder="持仓数量（股）" className="rounded border px-2 py-1.5 text-sm" />
                <input type="number" value={costPrice || ""} onChange={(e) => setCostPrice(Number(e.target.value))} placeholder="成本价（元）" className="rounded border px-2 py-1.5 text-sm" />
              </div>
              <div className="mt-3 flex gap-2">
                <button onClick={handleAddPosition} className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700">确认添加</button>
                <button onClick={() => setShowAddForm(false)} className="rounded border px-3 py-1 text-sm text-gray-600 hover:bg-gray-50">取消</button>
              </div>
            </div>
          )}

          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50 text-left text-xs font-semibold uppercase text-gray-500">
                <th className="px-4 py-3">代码</th>
                <th className="px-4 py-3">名称</th>
                <th className="px-4 py-3 text-right">持仓数量</th>
                <th className="px-4 py-3 text-right">成本价</th>
                <th className="px-4 py-3 text-right">最新价</th>
                <th className="px-4 py-3 text-right">市值</th>
                <th className="px-4 py-3 text-right">盈亏</th>
                <th className="px-4 py-3 text-right">仓位</th>
                <th className="px-4 py-3 w-12"></th>
              </tr>
            </thead>
            <tbody>
              {portfolio.positions.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-12 text-center text-sm text-gray-400">暂无持仓，点击"添加持仓"开始</td></tr>
              ) : (
                portfolio.positions.map((pos) => {
                  const pnlUp = pos.pnl >= 0;
                  return (
                    <tr key={pos.id} className="border-b text-sm hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono font-medium">{pos.symbol}</td>
                      <td className="px-4 py-3">{pos.name}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{pos.shares}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{pos.costPrice.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-gray-400">{pos.currentPrice?.toFixed(2) ?? "--"}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatMoney(pos.marketValue)}</td>
                      <td className={cn("px-4 py-3 text-right tabular-nums", pnlUp ? "text-red-600" : "text-green-600")}>
                        {pnlUp ? "+" : ""}{formatMoney(pos.pnl)}
                        <div className="text-xs">{pnlUp ? "+" : ""}{pos.pnlPct.toFixed(2)}%</div>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">{pos.weightPct.toFixed(1)}%</td>
                      <td className="px-4 py-3">
                        <button onClick={() => handleDeletePosition(pos.id)} className="text-gray-400 hover:text-red-500">×</button>
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
  );
}

function formatMoney(v: number) {
  if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(2)}亿`;
  if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(2)}万`;
  return v.toFixed(2);
}

function SummaryCard({ label, value, valueClass, sub, subClass }: { label: string; value: string; valueClass?: string; sub?: string; subClass?: string }) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`mt-1 text-xl font-bold ${valueClass || "text-gray-900"}`}>{value}</div>
      {sub && <div className={`mt-0.5 text-xs ${subClass || "text-gray-400"}`}>{sub}</div>}
    </div>
  );
}
