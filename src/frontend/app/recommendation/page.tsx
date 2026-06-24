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

  if (loading) return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" /></div>;

  if (!data || data.items.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center text-lg font-medium text-gray-400">暂无建议</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">投资建议</h1>

        {/* Summary */}
        <SummaryCard
          regime={data.marketRegime}
          temperature={data.marketTemperature}
          summary={data.summary}
        />

        {/* Action Items grouped by priority */}
        {data.items.length > 0 && (
          <div className="space-y-3">
            {data.items.map((item, i) => (
              <RecommendationCard key={`${item.symbol}-${i}`} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({ regime, temperature, summary }: { regime: string; temperature: number; summary: string }) {
  const getRegimeColor = () => {
    switch (regime) {
      case "Bull": return "text-green-600 bg-green-50 border-green-200";
      case "Bear": return "text-red-600 bg-red-50 border-red-200";
      case "Volatile": return "text-yellow-600 bg-yellow-50 border-yellow-200";
      default: return "text-blue-600 bg-blue-50 border-blue-200";
    }
  };

  const getTempColor = () => {
    if (temperature >= 70) return "text-red-600";
    if (temperature >= 40) return "text-yellow-600";
    return "text-green-600";
  };

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex items-center gap-4">
        <div className={cn("rounded-lg border px-3 py-1 text-sm font-medium", getRegimeColor())}>
          {regime === "Bull" ? "牛市" : regime === "Bear" ? "熊市" : regime === "Volatile" ? "震荡" : "盘整"}
        </div>
        <div className={cn("text-sm font-medium", getTempColor())}>
          市场情绪: {temperature}/100
        </div>
      </div>
      <div className="mt-3 text-sm text-gray-600 leading-relaxed">{summary}</div>
    </div>
  );
}

function RecommendationCard({ item }: { item: RecommendationItemDTO }) {
  const actionConfig = {
    buy: { label: "买入", className: "bg-green-100 text-green-800 border-green-300" },
    sell: { label: "卖出", className: "bg-red-100 text-red-800 border-red-300" },
    hold: { label: "持有", className: "bg-yellow-100 text-yellow-800 border-yellow-300" },
    watch: { label: "观望", className: "bg-blue-100 text-blue-800 border-blue-300" },
  };

  const config = actionConfig[item.action];

  const priorityLabel = item.priority === 1 ? "高" : item.priority === 2 ? "中" : "低";
  const priorityColor = item.priority === 1 ? "text-red-600" : item.priority === 2 ? "text-yellow-600" : "text-gray-500";

  const sourceLabels: Record<string, string> = {
    technical: "技术面", fundamental: "基本面", portfolio: "组合管理", market: "市场面", diversification: "风险分散",
  };

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={cn("rounded border px-2.5 py-0.5 text-xs font-semibold", config.className)}>
            {config.label}
          </div>
          <div>
            <span className="font-mono font-medium text-gray-900">{item.symbol}</span>
            {item.name && <span className="ml-2 text-sm text-gray-500">{item.name}</span>}
          </div>
          <div className={cn("text-xs font-medium", priorityColor)}>优先级: {priorityLabel}</div>
        </div>
        <div className="text-xs text-gray-400">{sourceLabels[item.source] || item.source}</div>
      </div>

      <div className="mt-2 text-sm text-gray-700">{item.reason}</div>

      {item.detail && (
        <div className="mt-1 text-xs text-gray-400">{item.detail}</div>
      )}

      <div className="mt-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">信心指数:</span>
          <div className="h-2 flex-1 rounded-full bg-gray-200">
            <div
              className={cn(
                "h-2 rounded-full",
                item.confidence >= 80 ? "bg-green-500" : item.confidence >= 60 ? "bg-yellow-500" : "bg-gray-400",
              )}
              style={{ width: `${item.confidence}%` }}
            />
          </div>
          <span className="text-xs font-medium text-gray-600">{item.confidence}%</span>
        </div>
      </div>
    </div>
  );
}
