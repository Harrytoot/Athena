"use client";

import { useCallback, useEffect, useState } from "react";
import type { StockSearchResult, Watchlist } from "@/types/watchlist";
import {
  addStockItem,
  createWatchlist,
  deleteWatchlist,
  getWatchlists,
  removeStockItem,
} from "@/lib/watchlist-api";
import { GroupSidebar } from "@/components/ui/GroupSidebar";
import { StockSearch } from "@/components/ui/StockSearch";

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
    } catch {
      // backend not ready
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    refresh();
  }, []);

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
      if (selectedId === id) {
        setSelectedId(null);
      }
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
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <GroupSidebar
        groups={groups}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />

      <div className="flex-1 p-6">
        {selectedGroup ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h1 className="text-xl font-bold text-gray-900">{selectedGroup.name}</h1>
              <StockSearch onSelect={handleAddStock} />
            </div>

            <div className="rounded-lg border bg-white shadow-sm">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase">
                    <th className="px-4 py-3">代码</th>
                    <th className="px-4 py-3">名称</th>
                    <th className="px-4 py-3 text-right">最新价</th>
                    <th className="px-4 py-3 text-right">涨跌幅</th>
                    <th className="px-4 py-3">标签</th>
                    <th className="px-4 py-3">备注</th>
                    <th className="px-4 py-3 w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  {selectedGroup.items.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-12 text-center text-sm text-gray-400">
                        暂无股票，请使用顶部搜索框添加
                      </td>
                    </tr>
                  ) : (
                    selectedGroup.items.map((item) => (
                      <tr key={item.id} className="border-b text-sm hover:bg-gray-50">
                        <td className="px-4 py-3 font-mono font-medium text-gray-900">
                          {item.symbol}
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-700">{item.name}</td>
                        <td className="px-4 py-3 text-right tabular-nums text-gray-900">
                          {item.currentPrice?.toFixed(2) ?? "--"}
                        </td>
                        <td className={`px-4 py-3 text-right tabular-nums ${(item.changePct ?? 0) >= 0 ? "text-red-600" : "text-green-600"}`}>
                          {item.changePct != null ? `${item.changePct >= 0 ? "+" : ""}${item.changePct.toFixed(2)}%` : "--"}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {item.tags.map((tag) => (
                              <span key={tag} className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-500 max-w-[200px] truncate">
                          {item.note || "--"}
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => handleRemoveStock(item.id)}
                            className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
                          >
                            ×
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            请选择或创建一个自选分组
          </div>
        )}
      </div>
    </div>
  );
}
