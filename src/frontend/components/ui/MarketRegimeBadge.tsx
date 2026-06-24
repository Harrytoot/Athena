import { cn } from "@/lib/utils";

type MarketRegime = "Bull" | "Bear" | "Range" | "Volatile";

const regimeConfig: Record<MarketRegime, { label: string; color: string; bg: string }> = {
  Bull: { label: "牛市", color: "text-red-600", bg: "bg-red-50 border-red-200" },
  Bear: { label: "熊市", color: "text-green-600", bg: "bg-green-50 border-green-200" },
  Range: { label: "震荡", color: "text-amber-600", bg: "bg-amber-50 border-amber-200" },
  Volatile: { label: "高波动", color: "text-purple-600", bg: "bg-purple-50 border-purple-200" },
};

export function MarketRegimeBadge({ regime }: { regime: MarketRegime }) {
  const config = regimeConfig[regime] ?? regimeConfig.Range;
  return (
    <span className={cn("inline-flex items-center rounded-md border px-2.5 py-0.5 text-sm font-semibold", config.bg, config.color)}>
      {config.label}
    </span>
  );
}
