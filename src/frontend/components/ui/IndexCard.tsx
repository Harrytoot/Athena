import { cn } from "@/lib/utils";
import type { IndexData } from "@/types/market";

function formatPrice(v: number) {
  return v.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatPct(v: number) {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

export function IndexCard({ index, label }: { index: IndexData; label?: string }) {
  const isUp = index.change_pct >= 0;
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="text-sm text-gray-500">{label ?? index.name}</div>
      <div className="mt-1 text-xs text-gray-400">{index.code}</div>
      <div className={cn("mt-2 text-2xl font-bold", isUp ? "text-red-600" : "text-green-600")}>
        {formatPrice(index.price)}
      </div>
      <div
        className={cn(
          "mt-1 inline-flex rounded px-1.5 py-0.5 text-sm font-medium",
          isUp ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"
        )}
      >
        {formatPct(index.change_pct)}
      </div>
    </div>
  );
}
