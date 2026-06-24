function formatNum(v: number) {
  if (v >= 10000) {
    return `${(v / 10000).toFixed(0)}万亿`;
  }
  return v.toLocaleString("zh-CN");
}

function formatFlow(v: number) {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(1)}亿`;
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
    <div className="grid grid-cols-4 gap-4">
      <StatBox label="成交额" value={`${(turnover / 10000).toFixed(2)}万亿`} />
      <StatBox label="上涨家数" value={upCount.toLocaleString()} color="text-red-600" />
      <StatBox label="下跌家数" value={downCount.toLocaleString()} color="text-green-600" />
      <StatBox
        label="北向资金"
        value={formatFlow(northbound)}
        color={northbound >= 0 ? "text-red-600" : "text-green-600"}
      />
    </div>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="rounded-lg border bg-white p-4 text-center shadow-sm">
      <div className="text-sm text-gray-500">{label}</div>
      <div className={`mt-1 text-xl font-bold ${color ?? "text-gray-900"}`}>{value}</div>
    </div>
  );
}
