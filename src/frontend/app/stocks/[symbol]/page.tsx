import Link from "next/link";
import { getStockDetail } from "@/lib/api";
import { AiSummaryCard } from "@/components/ui/AiSummaryCard";
import { MoneyFlowCard } from "@/components/ui/MoneyFlowCard";
import { TechnicalCard } from "@/components/ui/TechnicalCard";

export default async function StockDetailPage({
  params,
}: {
  params: { symbol: string };
}) {
  const { symbol } = params;
  let data;
  try {
    data = await getStockDetail(symbol);
  } catch {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <p className="text-lg font-medium">股票数据加载失败</p>
          <Link href="/watchlist" className="mt-2 text-sm text-blue-600 hover:underline">
            返回自选股
          </Link>
        </div>
      </div>
    );
  }

  const isUp = data.changePct >= 0;
  const color = isUp ? "text-red-600" : "text-green-600";
  const bg = isUp ? "bg-red-50" : "bg-green-50";

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Breadcrumb */}
        <div className="text-xs text-gray-400">
          <Link href="/watchlist" className="hover:text-blue-600">自选股</Link>
          <span className="mx-1">/</span>
          <span className="text-gray-600">{symbol}</span>
        </div>

        {/* Stock Header */}
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {data.name} <span className="text-lg font-normal text-gray-400">{data.symbol}</span>
              </h1>
              <div className="mt-2 flex items-baseline gap-3">
                <span className={`text-3xl font-bold ${color}`}>
                  {data.price.toFixed(2)}
                </span>
                <span className={`rounded px-2 py-0.5 text-sm font-semibold ${bg} ${color}`}>
                  {data.changePct >= 0 ? "+" : ""}{data.changePct.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-4 gap-4">
            <Stat label="开盘" value={data.open.toFixed(2)} />
            <Stat label="最高" value={data.high.toFixed(2)} color="text-red-600" />
            <Stat label="最低" value={data.low.toFixed(2)} color="text-green-600" />
            <Stat label="成交量" value={`${(data.volume / 10000).toFixed(0)}万手`} />
          </div>
        </div>

        {/* Technical Indicators */}
        <TechnicalCard data={data.technicalIndicators} price={data.price} />

        {/* Fundamental + Money Flow */}
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg border bg-white p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-gray-700">基本面</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">市盈率 (PE)</span>
                <span className="font-medium">{data.peRatio?.toFixed(2) ?? "--"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">市净率 (PB)</span>
                <span className="font-medium">{data.pbRatio?.toFixed(2) ?? "--"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">总市值</span>
                <span className="font-medium">{data.marketCap ? `${data.marketCap.toFixed(2)}亿` : "--"}</span>
              </div>
            </div>
          </div>
          <MoneyFlowCard data={data.moneyFlow} />
        </div>

        {/* AI Summary */}
        <AiSummaryCard data={data.aiAnalysis} />
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="text-center">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`mt-1 font-mono text-sm font-semibold ${color ?? "text-gray-900"}`}>{value}</div>
    </div>
  );
}
