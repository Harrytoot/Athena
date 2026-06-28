import { cn } from "@/lib/utils";
import type { IndexData } from "@/types/market";

export function IndexCard({ index, label }: { index: IndexData; label?: string }) {
  const isUp = index.change_pct >= 0;
  return (
    <div className="panel p-4">
      <div className="text-xs text-muted-foreground">{label ?? index.name}</div>
      <div className="mt-0.5 text-xs text-muted-foreground/60">{index.code}</div>
      <div className={cn("mt-2 font-mono text-2xl font-bold", isUp ? "text-up" : "text-down")}>
        {index.price.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      <div
        className={cn(
          "mt-1 inline-flex rounded px-1.5 py-0.5 font-mono text-sm font-medium",
          isUp ? "bg-up/15 text-up" : "bg-down/15 text-down"
        )}
      >
        {isUp ? "+" : ""}{index.change_pct.toFixed(2)}%
      </div>
    </div>
  );
}
