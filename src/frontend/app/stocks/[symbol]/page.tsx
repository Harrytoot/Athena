import Link from "next/link";
import { getStockDetail } from "@/lib/api";
import StockChartPanel from "./StockChartPanel";
import DecisionCenter from "@/components/decision/DecisionCenter";
import DetailDataPanel from "./DetailDataPanel";
import { cn } from "@/lib/utils";

export default async function StockDetailPage({ params }: { params: { symbol: string } }) {
  const { symbol } = params;
  let data;
  try {
    data = await getStockDetail(symbol);
  } catch {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p className="text-sm font-medium">股票数据加载失败</p>
          <Link href="/watchlist" className="mt-2 inline-block text-[11px] text-primary hover:underline">
            返回自选股
          </Link>
        </div>
      </div>
    );
  }

  const isUp = data.changePct >= 0;
  const changeColor = isUp ? "text-up" : "text-down";
  const changeBg = isUp ? "bg-up/15 text-up" : "bg-down/15 text-down";

  return (
    <div className="flex h-full flex-col gap-2 p-2">
      {/* Header Bar */}
      <div className="flex items-center gap-6 px-3 py-2 rounded-lg border border-divider bg-card/50 shrink-0">
        <div>
          <div className="flex items-baseline gap-2">
            <h1 className="text-sm font-bold text-foreground">{data.name}</h1>
            <span className="text-[11px] font-mono text-muted-foreground">{data.symbol}</span>
          </div>
          <div className="mt-0.5 flex items-baseline gap-3">
            <span className={`font-mono text-xl font-bold ${changeColor}`}>
              {data.price.toFixed(2)}
            </span>
            <span className={cn("rounded px-2 py-0.5 font-mono text-[11px] font-semibold", changeBg)}>
              {isUp ? "+" : ""}{data.changePct.toFixed(2)}%
            </span>
          </div>
        </div>
        <div className="ml-auto grid grid-cols-4 gap-6">
          <Stat label="开盘" value={data.open.toFixed(2)} />
          <Stat label="最高" value={data.high.toFixed(2)} />
          <Stat label="最低" value={data.low.toFixed(2)} />
          <Stat label="成交量" value={`${(data.volume / 10000).toFixed(0)}万`} />
        </div>
      </div>

      {/* Main: 70% Chart + 30% DecisionCenter */}
      <div className="flex flex-1 gap-2 min-h-0">
        <div className="rounded-lg border border-divider bg-card/50 overflow-hidden" style={{ flex: "0 0 70%" }}>
          <StockChartPanel symbol={symbol} />
        </div>

        <div className="flex flex-col gap-2" style={{ flex: "0 0 30%" }}>
          <div className="flex-1 min-h-0">
            <DecisionCenter symbol={symbol} name={data.name} price={data.price} />
          </div>
          <DetailDataPanel data={data} />
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-[9px] text-muted-foreground uppercase tracking-wide">{label}</div>
      <div className="mt-0.5 font-mono text-[11px] font-semibold text-foreground tabular-nums">{value}</div>
    </div>
  );
}
