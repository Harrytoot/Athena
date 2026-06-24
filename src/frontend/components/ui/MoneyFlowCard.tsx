import { cn } from "@/lib/utils";
import type { MoneyFlow } from "@/types/stock";

export function MoneyFlowCard({ data }: { data: MoneyFlow }) {
  const items = [
    { label: "主力资金", value: data.mainForceInflow },
    { label: "散户资金", value: data.retailInflow },
    { label: "北向资金", value: data.northboundInflow },
  ];

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-gray-700">资金面</h3>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.label}>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">{item.label}</span>
              <span className={cn("font-medium tabular-nums", item.value >= 0 ? "text-red-600" : "text-green-600")}>
                {item.value >= 0 ? "+" : ""}{item.value.toFixed(2)}万
              </span>
            </div>
            <div className="mt-1 h-2 w-full rounded-full bg-gray-100">
              <div
                className={cn("h-2 rounded-full", item.value >= 0 ? "bg-red-400" : "bg-green-400")}
                style={{ width: `${Math.min(Math.abs(item.value) / 50, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
