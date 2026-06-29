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

export default function MarketPage() {
  const [data, setData] = useState<MarketOverview | null>(null);
  const [scoreData, setScoreData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

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
      } catch {
        if (!cancelled) setError(true);
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
        <div className="font-mono text-sm text-muted-foreground animate-pulse">加载市场数据...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-lg font-medium">无法连接到后端服务</div>
          <div className="mt-2 text-sm">请确保 docker-compose up 已启动</div>
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
            <h1 className="text-2xl font-bold text-foreground">市场</h1>
            <MarketRegimeBadge regime={data.marketRegime} />
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
