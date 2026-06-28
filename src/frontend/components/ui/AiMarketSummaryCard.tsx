export function AiMarketSummaryCard({ summary }: { summary: string }) {
  return (
    <div className="panel border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10 p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-sm font-semibold text-primary">AI 市场摘要</span>
        <span className="rounded bg-primary/20 px-1.5 py-0.5 text-xs text-primary">Mock</span>
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">{summary}</p>
    </div>
  );
}
