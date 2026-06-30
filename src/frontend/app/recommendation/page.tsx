"use client";

import { useCallback, useEffect, useState } from "react";
import type { RecommendationDTO, RecommendationItemDTO } from "@/types/recommendation";
import { getRecommendations } from "@/lib/recommendation-api";
import { cn } from "@/lib/utils";

export default function RecommendationPage() {
  const [data, setData] = useState<RecommendationDTO | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const result = await getRecommendations();
      setData(result);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  if (loading) return (
    <div className="flex h-full items-center justify-center">
      <div className="font-mono text-xs text-muted-foreground animate-pulse">加载建议...</div>
    </div>
  );

  if (!data || data.items.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <span className="text-xs text-muted-foreground">暂无建议</span>
      </div>
    );
  }

  return (
    <div className="h-full p-4 overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-4">
        <h1 className="text-sm font-bold text-foreground">投资建议</h1>

        <div className="panel p-4">
          <div className="flex items-center gap-3">
            <span className={cn(
              "rounded border px-2.5 py-0.5 text-[11px] font-semibold",
              data.marketRegime === "Bull" ? "text-up bg-up/10 border-up/30" :
              data.marketRegime === "Bear" ? "text-down bg-down/10 border-down/30" :
              "text-amber-400 bg-amber-400/10 border-amber-400/30"
            )}>
              {data.marketRegime === "Bull" ? "牛市" : data.marketRegime === "Bear" ? "熊市" : "震荡"}
            </span>
            <span className="text-[11px] text-muted-foreground">
              情绪: <span className="font-mono font-semibold text-foreground">{data.marketTemperature}/100</span>
            </span>
          </div>
          <div className="mt-2 text-[11px] text-muted-foreground leading-relaxed">{data.summary}</div>
        </div>

        {data.items.map((item, i) => (
          <RecommendationCard key={`${item.symbol}-${i}`} item={item} />
        ))}
      </div>
    </div>
  );
}

function RecommendationCard({ item }: { item: RecommendationItemDTO }) {
  const actionConfig = {
    buy: { label: "买入", cls: "bg-up/10 text-up border-up/30" },
    sell: { label: "卖出", cls: "bg-down/10 text-down border-down/30" },
    hold: { label: "持有", cls: "bg-amber-400/10 text-amber-400 border-amber-400/30" },
    watch: { label: "观望", cls: "bg-muted/30 text-muted-foreground border-border" },
  };
  const config = actionConfig[item.action] ?? actionConfig.watch;
  const priorityLabel = item.priority === 1 ? "高" : item.priority === 2 ? "中" : "低";
  const priorityColor = item.priority === 1 ? "text-down" : item.priority === 2 ? "text-amber-400" : "text-muted-foreground";

  return (
    <div className="panel p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className={cn("rounded border px-2.5 py-0.5 text-[10px] font-semibold", config.cls)}>
            {config.label}
          </span>
          <span className="font-mono text-[11px] font-medium text-foreground">{item.symbol}</span>
          {item.name && <span className="text-[11px] text-muted-foreground">{item.name}</span>}
          <span className={cn("text-[10px] font-medium", priorityColor)}>P{priorityLabel}</span>
        </div>
        <span className="text-[10px] text-muted-foreground">{item.source}</span>
      </div>
      <div className="mt-2 text-[11px] text-foreground/80">{item.reason}</div>
      {item.detail && <div className="mt-0.5 text-[10px] text-muted-foreground">{item.detail}</div>}
      <div className="mt-2 flex items-center gap-2">
        <span className="text-[10px] text-muted-foreground">Confidence:</span>
        <div className="h-1.5 flex-1 rounded-full bg-secondary">
          <div className={cn("h-1.5 rounded-full", item.confidence >= 80 ? "bg-up" : item.confidence >= 60 ? "bg-amber-400" : "bg-muted-foreground")}
            style={{ width: `${item.confidence}%` }} />
        </div>
        <span className="font-mono text-[10px] font-semibold text-foreground tabular-nums">{item.confidence}%</span>
      </div>
    </div>
  );
}
