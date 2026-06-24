import type { TechnicalIndicators } from "@/types/stock";

export function TechnicalCard({ data, price }: { data: TechnicalIndicators; price: number }) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">技术指标</h3>

      {/* K-line placeholder */}
      <div className="mb-4 flex h-48 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-gray-50">
        <div className="text-center text-sm text-gray-400">
          <div className="mb-1 text-lg">📈</div>
          <div>K线图（预留）</div>
          <div className="text-xs">后续版本接入 TradingView / ECharts</div>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-4 text-center">
        <Indicator label="MA5" value={data.ma5.toFixed(2)} compare={price} />
        <Indicator label="MA20" value={data.ma20.toFixed(2)} compare={price} />
        <Indicator label="RSI" value={data.rsi.toFixed(1)} unit="" />
        <Indicator label="MACD DIFF" value={data.macd.diff.toFixed(2)} unit="" />
        <Indicator label="MACD DEA" value={data.macd.dea.toFixed(2)} unit="" />
        <Indicator label="MACD 柱" value={data.macd.histogram.toFixed(2)} unit="" />
      </div>
    </div>
  );
}

function Indicator({ label, value, compare, unit }: { label: string; value: string; compare?: number; unit?: string }) {
  const color = compare != null ? (parseFloat(value) > compare ? "text-red-600" : parseFloat(value) < compare ? "text-green-600" : "text-gray-900") : "text-gray-900";
  return (
    <div>
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`mt-1 text-sm font-semibold ${color}`}>{value}{unit ?? ""}</div>
    </div>
  );
}
