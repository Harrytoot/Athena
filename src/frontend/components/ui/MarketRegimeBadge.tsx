import { cn } from "@/lib/utils";

type MarketRegime = "Bull" | "Bear" | "Range" | "Volatile";

const regimeConfig: Record<MarketRegime, { label: string; color: string; bg: string }> = {
  Bull: { label: "牛市", color: "text-up", bg: "bg-up/15 border-up/30" },
  Bear: { label: "熊市", color: "text-down", bg: "bg-down/15 border-down/30" },
  Range: { label: "震荡", color: "text-amber-400", bg: "bg-amber-500/15 border-amber-500/30" },
  Volatile: { label: "高波动", color: "text-purple-400", bg: "bg-purple-500/15 border-purple-500/30" },
};

export function MarketRegimeBadge({ regime }: { regime: MarketRegime | string }) {
  const config = regimeConfig[regime as MarketRegime] ?? regimeConfig.Range;
  return (
    <span className={cn(
      "inline-flex items-center rounded-md border px-2.5 py-0.5 text-sm font-semibold",
      config.bg, config.color
    )}>
      {config.label}
    </span>
  );
}
