import { cn } from "@/lib/utils";
import type { HotItem } from "@/types/market";

export function HotSectorList({ title, items }: { title: string; items: HotItem[] }) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-gray-700">{title}</h3>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div key={item.name} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-5 w-5 items-center justify-center rounded text-xs font-bold text-white",
                  i < 3 ? "bg-red-500" : "bg-gray-400"
                )}
              >
                {i + 1}
              </span>
              {item.name}
            </span>
            <span className={cn("font-medium", item.change_pct >= 0 ? "text-red-600" : "text-green-600")}>
              {item.change_pct >= 0 ? "+" : ""}
              {item.change_pct.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
