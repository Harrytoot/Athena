import { cn } from "@/lib/utils";

function formatNum(v: number) {
  if (v >= 10000) return `${(v / 10000).toFixed(0)}万亿`;
  return v.toLocaleString("zh-CN");
}

export function MarketStatsRow({
  turnover,
  upCount,
  downCount,
  northbound,
}: {
  turnover: number;
  upCount: number;
  downCount: number;
  northbound: number;
}) {
  return (
    <div className="grid grid-cols-4 gap-3">
      <StatBox label="成交额" value={`${(turnover / 10000).toFixed(2)}万亿`} />
      <StatBox label="上涨家数" value={upCount.toLocaleString()} color="text-up" />
      <StatBox label="下跌家数" value={downCount.toLocaleString()} color="text-down" />
      <StatBox
        label="北向资金"
        value={`${northbound >= 0 ? "+" : ""}${northbound.toFixed(1)}亿`}
        color={northbound >= 0 ? "text-up" : "text-down"}
      />
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="panel p-4 text-center">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn("mt-1 text-xl font-bold font-mono", color ?? "text-foreground")}>{value}</div>
    </div>
  );
}
