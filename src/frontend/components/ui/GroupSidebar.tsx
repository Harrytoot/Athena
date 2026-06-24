"use client";

import { useState } from "react";
import type { Watchlist } from "@/types/watchlist";
import { cn } from "@/lib/utils";

export function GroupSidebar({
  groups,
  selectedId,
  onSelect,
  onCreate,
  onDelete,
}: {
  groups: Watchlist[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
}) {
  const [newName, setNewName] = useState("");
  const [showInput, setShowInput] = useState(false);

  const handleCreate = () => {
    if (newName.trim()) {
      onCreate();
      setNewName("");
      setShowInput(false);
    }
  };

  return (
    <div className="w-60 border-r bg-white p-3">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">自选分组</h2>
        <button
          onClick={() => setShowInput(true)}
          className="rounded px-2 py-0.5 text-xs text-blue-600 hover:bg-blue-50"
        >
          + 新建
        </button>
      </div>

      {showInput && (
        <div className="mb-2 flex gap-1">
          <input
            autoFocus
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleCreate(); if (e.key === "Escape") setShowInput(false); }}
            className="flex-1 rounded border px-2 py-1 text-xs"
            placeholder="分组名称"
          />
        </div>
      )}

      <div className="space-y-0.5">
        {groups.map((g) => (
          <div
            key={g.id}
            onClick={() => onSelect(g.id)}
            className={cn(
              "group flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors",
              selectedId === g.id
                ? "bg-blue-50 text-blue-700"
                : "text-gray-600 hover:bg-gray-50"
            )}
          >
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: g.color }} />
              <span>{g.name}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-xs text-gray-400">{g.itemCount}</span>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(g.id); }}
                className="hidden rounded p-0.5 text-xs text-gray-400 hover:text-red-500 group-hover:inline-block"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
