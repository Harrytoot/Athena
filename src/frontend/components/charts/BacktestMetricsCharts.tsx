"use client";

import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { RadarChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  RadarComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { PeriodMetrics } from "@/types/backtest";

echarts.use([
  RadarChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  RadarComponent,
  LegendComponent,
  CanvasRenderer,
]);

interface Props {
  period5d: PeriodMetrics;
  period10d: PeriodMetrics;
  period20d: PeriodMetrics;
}

export default function BacktestMetricsCharts({ period5d, period10d, period20d }: Props) {
  const radarOption: echarts.EChartsCoreOption = {
    backgroundColor: "transparent",
    textStyle: { color: "#8B95A5" },
    legend: {
      data: ["5日", "10日", "20日"],
      bottom: 0,
      textStyle: { color: "#8B95A5", fontSize: 11 },
    },
    radar: {
      center: ["50%", "45%"],
      radius: "65%",
      indicator: [
        { name: "Sharpe", max: Math.max(period5d.sharpe, period10d.sharpe, period20d.sharpe, 1) * 1.3 },
        { name: "胜率", max: 1 },
        { name: "IC", max: Math.max(Math.abs(period5d.ic), Math.abs(period10d.ic), Math.abs(period20d.ic), 0.1) * 1.5 },
        { name: "Rank IC", max: Math.max(Math.abs(period5d.rankIc), Math.abs(period10d.rankIc), Math.abs(period20d.rankIc), 0.1) * 1.5 },
        { name: "样本量", max: Math.max(period5d.nObservations, period10d.nObservations, period20d.nObservations, 1) * 1.2 },
      ],
      axisName: { color: "#8B95A5", fontSize: 10 },
      splitArea: {
        areaStyle: { color: ["#2A2E3920", "#2A2E3910"] },
      },
      splitLine: { lineStyle: { color: "#2A2E39" } },
      axisLine: { lineStyle: { color: "#2A2E39" } },
    },
    series: [
      {
        type: "radar",
        name: "5日",
        data: [{ value: [period5d.sharpe, period5d.winRate, period5d.ic, period5d.rankIc, period5d.nObservations] }],
        symbol: "none",
        lineStyle: { color: "#00B8D9", width: 1.5 },
        areaStyle: { color: "#00B8D920" },
        itemStyle: { color: "#00B8D9" },
      },
      {
        type: "radar",
        name: "10日",
        data: [{ value: [period10d.sharpe, period10d.winRate, period10d.ic, period10d.rankIc, period10d.nObservations] }],
        symbol: "none",
        lineStyle: { color: "#FFD700", width: 1.5 },
        areaStyle: { color: "#FFD70020" },
        itemStyle: { color: "#FFD700" },
      },
      {
        type: "radar",
        name: "20日",
        data: [{ value: [period20d.sharpe, period20d.winRate, period20d.ic, period20d.rankIc, period20d.nObservations] }],
        symbol: "none",
        lineStyle: { color: "#FF6B6B", width: 1.5 },
        areaStyle: { color: "#FF6B6B20" },
        itemStyle: { color: "#FF6B6B" },
      },
    ],
  };

  return (
    <div className="panel p-3">
      <h3 className="mb-2 text-sm font-semibold text-muted-foreground">多周期指标雷达图</h3>
      <ReactEChartsCore
        echarts={echarts}
        option={radarOption}
        style={{ height: 220 }}
        opts={{ renderer: "canvas" }}
        notMerge
      />
    </div>
  );
}
