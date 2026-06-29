"use client";

import { useEffect, useState } from "react";
import { getMarketOverview, getMarketScore } from "@/lib/api";
import type { MarketOverview } from "@/types/market";
import { AiMarketSummaryCard } from "@/components/ui/AiMarketSummaryCard";
import { HotSectorList } from "@/components/ui/HotSectorList";
import { IndexCard } from "@/components/ui/IndexCard";
import { MarketRegimeBadge } from "@/components/ui/MarketRegimeBadge";
import { MarketStatsRow } from "@/components/ui/MarketStatsRow";
import { MarketTemperatureGauge } from "@/components/ui/MarketTemperatureGauge";
import { UpdateTimeLabel } from "@/components/ui/UpdateTimeLabel";

function isEmptyMarketData(data: MarketOverview): boolean {
  return (
    data.indices.shanghai.price === 0 &&
    data.temperature === 0 &&
    data.turnover === 0 &&
    data.upCount === 0 &&
    data.downCount === 0
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<MarketOverview | null>(null);
  const [scoreData, setScoreData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const overview = await getMarketOverview();
        if (cancelled) return;
        setData(overview);
        try {
          const score = await getMarketScore();
          if (!cancelled) setScoreData(score);
        } catch {
          // score is optional
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(true);
          setErrorMsg(e?.message || "");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchData();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="font-mono text-sm text-muted-foreground animate-pulse">正在连接数据源...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg font-medium">无法连接到后端服务</div>
          <div className="mt-2 text-sm">
            {errorMsg || "请确保 docker-compose up 已启动"}
          </div>
        </div>
      </div>
    );
  }

  if (isEmptyMarketData(data)) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center text-muted-foreground space-y-2">
          <div className="text-lg font-medium">市场数据暂未就绪</div>
          <div className="text-sm">
            等待数据同步完成，请稍后刷新页面
          </div>
          <div className="text-xs opacity-50">
            数据质量: {data.dataQuality || "unknown"}
          </div>
        </div>
      </div>
    );
  }

  const temperature = scoreData?.score ?? data.temperature;

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="mx-auto max-w-7xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground">市场概览</h1>
            <MarketRegimeBadge regime={data.marketRegime} />
            {data.dataQuality && data.dataQuality !== "unknown" && (
              <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">
                {data.dataQuality}
              </span>
            )}
          </div>
          <UpdateTimeLabel time={data.updatedAt} />
        </div>

        <div className="grid grid-cols-4 gap-3">
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

        <div className="grid grid-cols-2 gap-3">
          <HotSectorList title="热点行业 Top10" items={data.hotIndustries} />
          <HotSectorList title="热点概念 Top10" items={data.hotConcepts} />
        </div>

        <AiMarketSummaryCard summary={data.summary} />
      </div>
    </div>
  );
}
