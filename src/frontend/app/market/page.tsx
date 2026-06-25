import { getMarketOverview, getMarketScore } from "@/lib/api";
import { AiMarketSummaryCard } from "@/components/ui/AiMarketSummaryCard";
import { HotSectorList } from "@/components/ui/HotSectorList";
import { IndexCard } from "@/components/ui/IndexCard";
import { MarketRegimeBadge } from "@/components/ui/MarketRegimeBadge";
import { MarketStatsRow } from "@/components/ui/MarketStatsRow";
import { MarketTemperatureGauge } from "@/components/ui/MarketTemperatureGauge";
import { UpdateTimeLabel } from "@/components/ui/UpdateTimeLabel";

export default async function MarketPage() {
  let data;
  let scoreData;
  try {
    data = await getMarketOverview();
    try {
      scoreData = await getMarketScore();
    } catch {
      scoreData = null;
    }
  } catch {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-lg font-medium text-gray-700">无法连接到后端服务</div>
          <div className="mt-2 text-sm text-gray-500">请确保 docker-compose up 已启动</div>
        </div>
      </div>
    );
  }

  const temperature = scoreData?.score ?? data.temperature;
  const source = scoreData?.source ?? "";

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">市场</h1>
            <MarketRegimeBadge regime={data.marketRegime} />
          </div>
          <UpdateTimeLabel time={data.updatedAt} />
        </div>

        <div className="grid grid-cols-4 gap-4">
          <MarketTemperatureGauge temperature={temperature} />
          <IndexCard index={data.indices.shanghai} label="上证指数" />
          <IndexCard index={data.indices.shenzhen} label="深证成指" />
          <IndexCard index={data.indices.chi_next} label="创业板指" />
        </div>

        <MarketStatsRow
          turnover={data.turnover}
          upCount={data.upCount}
          downCount={data.downCount}
          northbound={data.northbound}
        />

        <div className="grid grid-cols-2 gap-4">
          <HotSectorList title="热点行业 Top10" items={data.hotIndustries} />
          <HotSectorList title="热点概念 Top10" items={data.hotConcepts} />
        </div>

        <AiMarketSummaryCard summary={data.summary} />

        {source && (
          <div className="text-center text-xs text-gray-400">
            Market Score: {source} | Score: {temperature}
          </div>
        )}
      </div>
    </div>
  );
}
