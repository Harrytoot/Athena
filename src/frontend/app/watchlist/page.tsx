"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import type { StockSearchResult, Watchlist } from "@/types/watchlist";
import {
  addStockItem,
  createWatchlist,
  deleteWatchlist,
  getWatchlists,
  removeStockItem,
} from "@/lib/watchlist-api";
import { cn } from "@/lib/utils";

function RsiCell({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted-foreground">--</span>;
  return (
    <span className={cn("font-mono text-xs tabular-nums font-semibold", value < 30 ? "text-up" : value > 70 ? "text-down" : "text-muted-foreground")}>
      {value.toFixed(1)}
    </span>
  );
}

function MaStatusBadge({ status }: { status: string }) {
  return (
    <span className={cn("inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold", status === "Bull" ? "bg-up/15 text-up" : status === "Bear" ? "bg-down/15 text-down" : "bg-muted/30 text-muted-foreground")}>
      {status === "Bull" ? "多头" : status === "Bear" ? "空头" : "--"}
    </span>
  );
}

function mockRsi(): number {
  return Math.round((Math.random() * 60 + 20) * 10) / 10;
}

function mockMaStatus(): string {
  const r = Math.random();
  if (r < 0.4) return "Bull";
  if (r < 0.7) return "Bear";
  return "Neutral";
}

export default function WatchlistPage() {
  const [groups, setGroups] = useState<Watchlist[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const selectedGroup = groups.find((g) => g.id === selectedId) ?? null;

  const refresh = useCallback(async () => {
    try {
      const data = await getWatchlists();
      setGroups(data);
      if (data.length > 0 && !data.find((g) => g.id === selectedId)) {
        setSelectedId(data[0].id);
      }
    } catch {} finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => { refresh(); }, []);

  const handleCreate = async () => {
    const name = prompt("分组名称：");
    if (!name) return;
    try {
      const created = await createWatchlist(name);
      await refresh();
      setSelectedId(created.id);
    } catch {}
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteWatchlist(id);
      setGroups((prev) => prev.filter((g) => g.id !== id));
      if (selectedId === id) setSelectedId(null);
    } catch {}
  };

  const handleAddStock = async (stock: StockSearchResult) => {
    if (!selectedId) return;
    try {
      await addStockItem(selectedId, stock.symbol, stock.name);
      await refresh();
    } catch {}
  };

  const handleRemoveStock = async (itemId: string) => {
    if (!selectedId) return;
    try {
      await removeStockItem(selectedId, itemId);
      await refresh();
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="font-mono text-xs text-muted-foreground animate-pulse">加载自选数据...</div>
      </div>
    );
  }

  const columns = [
    { key: "symbol", label: "代码", width: "w-[80px]" },
    { key: "name", label: "名称", width: "w-[80px]" },
    { key: "price", label: "现价", width: "w-[80px]", right: true },
    { key: "change", label: "涨幅", width: "w-[70px]", right: true },
    { key: "volRatio", label: "量比", width: "w-[60px]", right: true },
    { key: "turnover", label: "换手", width: "w-[65px]", right: true },
    { key: "rsi", label: "RSI(14)", width: "w-[65px]", right: true },
    { key: "ma", label: "MA状态", width: "w-[65px]" },
    { key: "action", label: "", width: "w-[30px]" },
  ];

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-divider px-3 py-1.5 shrink-0">
        <span className="text-[11px] font-semibold text-muted-foreground mr-2">自选监控</span>
        <div className="flex gap-1">
          {groups.map((g) => (
            <button
              key={g.id}
              onClick={() => setSelectedId(g.id)}
              className={cn(
                "rounded px-2 py-0.5 text-[11px] transition-colors",
                selectedId === g.id
                  ? "bg-primary/20 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}
            >
              {g.name}
            </button>
          ))}
        </div>
        <button onClick={handleCreate} className="text-[11px] text-muted-foreground hover:text-foreground px-1">
          +
        </button>
      </div>

      <div className="flex-1 overflow-auto">
        {selectedGroup ? (
          <table className="w-full">
            <thead className="sticky top-0 z-10 bg-background">
              <tr className="border-b border-divider text-[10px] font-semibold uppercase text-muted-foreground">
                {columns.map((col) => (
                  <th key={col.key} className={cn("px-2 py-1.5", col.right ? "text-right" : "text-left", col.width)}>
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {selectedGroup.items.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-2 py-16 text-center text-[11px] text-muted-foreground">
                    暂无标的，使用搜索添加自选
                  </td>
                </tr>
              ) : (
                selectedGroup.items.map((item) => {
                  const changePct = item.changePct ?? 0;
                  const isUp = changePct >= 0;
                  return (
                    <tr key={item.id} className="border-b border-divider/50 text-[11px] hover:bg-secondary/30 transition-colors">
                      <td className="px-2 py-1.5">
                        <Link href={`/stocks/${item.symbol}`} className="font-mono text-primary hover:underline">
                          {item.symbol}
                        </Link>
                      </td>
                      <td className="px-2 py-1.5">
                        <Link href={`/stocks/${item.symbol}`} className="text-foreground/80 hover:text-foreground">
                          {item.name}
                        </Link>
                      </td>
                      <td className="px-2 py-1.5 font-mono text-right tabular-nums text-foreground">
                        {item.currentPrice?.toFixed(2) ?? "--"}
                      </td>
                      <td className={cn("px-2 py-1.5 font-mono text-right tabular-nums font-semibold", isUp ? "text-up" : "text-down")}>
                        {item.changePct != null ? `${isUp ? "+" : ""}${changePct.toFixed(2)}%` : "--"}
                      </td>
                      <td className="px-2 py-1.5 font-mono text-right tabular-nums text-muted-foreground">
                        {(item as any).volRatio?.toFixed(2) ?? "--"}
                      </td>
                      <td className="px-2 py-1.5 font-mono text-right tabular-nums text-muted-foreground">
                        {(item as any).turnover?.toFixed(2) ?? "--"}%
                      </td>
                      <td className="px-2 py-1.5">
                        <RsiCell value={mockRsi()} />
                      </td>
                      <td className="px-2 py-1.5">
                        <MaStatusBadge status={mockMaStatus()} />
                      </td>
                      <td className="px-2 py-1.5">
                        <button
                          onClick={() => handleRemoveStock(item.id)}
                          className="text-muted-foreground/40 hover:text-down text-[11px]"
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        ) : (
          <div className="flex h-full items-center justify-center text-[11px] text-muted-foreground">
            {groups.length === 0 ? "点击 + 创建自选分组" : "选择一个分组"}
          </div>
        )}
      </div>
    </div>
  );
}
