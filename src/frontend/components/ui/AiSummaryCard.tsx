import { cn } from "@/lib/utils";
import type { AiAnalysis } from "@/types/stock";

export function AiSummaryCard({ data }: { data: AiAnalysis }) {
  const riskColors: Record<string, string> = {
    low: "bg-green-100 text-green-700",
    medium: "bg-amber-100 text-amber-700",
    high: "bg-red-100 text-red-700",
  };

  const sentimentLabels: Record<string, string> = {
    bullish: "看多",
    neutral: "中性",
    bearish: "看空",
  };

  return (
    <div className="rounded-lg border border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm font-semibold text-blue-700">AI 分析</span>
        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-600">Mock</span>
        <div className="ml-auto flex items-center gap-2">
          <span className={cn("rounded px-2 py-0.5 text-xs font-medium", riskColors[data.riskLevel] ?? "bg-gray-100")}>
            风险：{data.riskLevel === "low" ? "低" : data.riskLevel === "medium" ? "中" : "高"}
          </span>
          <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
            {sentimentLabels[data.sentiment] ?? data.sentiment}
          </span>
        </div>
      </div>
      <p className="text-sm leading-relaxed text-gray-700">{data.summary}</p>
    </div>
  );
}
