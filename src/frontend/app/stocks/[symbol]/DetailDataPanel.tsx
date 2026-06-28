"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StockDetail } from "@/types/stock";

export default function DetailDataPanel({ data }: { data: StockDetail }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="shrink-0 overflow-hidden rounded-lg border border-border bg-card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        <span>详细数据面板</span>
        {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>

      {open && (
        <div className="divide-y divide-border border-t border-border px-3 pb-3 space-y-2">
          {/* Technical */}
          <div className="pt-2">
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              技术指标
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
              <TinyStat label="MA5" value={data.technicalIndicators.ma5.toFixed(2)} compare={data.price} />
              <TinyStat label="MA20" value={data.technicalIndicators.ma20.toFixed(2)} compare={data.price} />
              <TinyStat label="RSI" value={data.technicalIndicators.rsi.toFixed(1)} />
              <TinyStat label="MACD" value={data.technicalIndicators.macd.diff.toFixed(2)} />
            </div>
          </div>

          {/* Fundamentals */}
          <div className="pt-2">
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              基本面
            </div>
            {[["PE", data.peRatio], ["PB", data.pbRatio], ["市值", data.marketCap ? `${data.marketCap.toFixed(2)}亿` : null]].map(([l, v]) => (
              <div key={l} className="flex justify-between py-0.5 text-xs">
                <span className="text-muted-foreground">{l}</span>
                <span className="font-mono text-foreground">{v ?? "--"}</span>
              </div>
            ))}
          </div>

          {/* Flow */}
          <div className="pt-2">
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              资金流向
            </div>
            <FlowBar label="主力" value={data.moneyFlow.mainForceInflow} />
            <FlowBar label="散户" value={data.moneyFlow.retailInflow} />
            <FlowBar label="北向" value={data.moneyFlow.northboundInflow} />
          </div>

          {/* AI */}
          <div className="pt-2">
            <div className="mb-1.5 flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">AI 分析</span>
              <span className={cn(
                "rounded px-1 py-0 text-xs font-medium",
                data.aiAnalysis.riskLevel === "low" ? "bg-up/15 text-up" : data.aiAnalysis.riskLevel === "medium" ? "bg-amber-500/15 text-amber-400" : "bg-down/15 text-down"
              )}>
                {data.aiAnalysis.riskLevel === "low" ? "低" : data.aiAnalysis.riskLevel === "medium" ? "中" : "高"}风险
              </span>
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground line-clamp-3">{data.aiAnalysis.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function TinyStat({ label, value, compare }: { label: string; value: string; compare?: number }) {
  const isAbove = compare !== undefined && parseFloat(value) > compare;
  const isBelow = compare !== undefined && parseFloat(value) < compare;
  const color = isAbove ? "text-up" : isBelow ? "text-down" : "text-foreground";
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className={`font-mono font-medium ${color}`}>{value}</span>
    </div>
  );
}

function FlowBar({ label, value }: { label: string; value: number }) {
  const isPositive = value >= 0;
  const pct = Math.min(Math.abs(value) / 50, 100);
  return (
    <div className="mb-1.5 last:mb-0">
      <div className="mb-0.5 flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={cn("font-mono font-medium", isPositive ? "text-up" : "text-down")}>
          {isPositive ? "+" : ""}{value.toFixed(2)}万
        </span>
      </div>
      <div className="h-1 w-full rounded-full bg-secondary">
        <div className={cn("h-1 rounded-full", isPositive ? "bg-up" : "bg-down")} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
