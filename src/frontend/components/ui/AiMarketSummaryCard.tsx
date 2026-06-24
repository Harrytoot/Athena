export function AiMarketSummaryCard({ summary }: { summary: string }) {
  return (
    <div className="rounded-lg border border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-4 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-sm font-semibold text-blue-700">AI 市场摘要</span>
        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-600">Mock</span>
      </div>
      <p className="text-sm leading-relaxed text-gray-700">{summary}</p>
    </div>
  );
}
