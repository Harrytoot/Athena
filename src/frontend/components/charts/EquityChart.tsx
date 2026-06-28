"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  LineSeries,
  HistogramSeries,
  createSeriesMarkers,
  type IChartApi,
  type Time,
} from "lightweight-charts";
import type { EquityPoint, TradeMark, DrawdownPeriod } from "@/types/backtest";

interface EquityChartProps {
  equityCurve: EquityPoint[];
  benchmarkCurve: EquityPoint[];
  trades: TradeMark[];
  drawdownPeriods: DrawdownPeriod[];
  className?: string;
}

export default function EquityChart({
  equityCurve,
  benchmarkCurve,
  trades,
  drawdownPeriods,
  className,
}: EquityChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || equityCurve.length === 0) return;
    container.innerHTML = "";

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 400;

    const chart = createChart(container, {
      width,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#151924" },
        textColor: "#8B95A5",
      },
      grid: {
        vertLines: { color: "#2A2E39" },
        horzLines: { color: "#2A2E39" },
      },
      rightPriceScale: { borderColor: "#2A2E39" },
      timeScale: {
        borderColor: "#2A2E39",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: { mode: 0 },
    });

    chartRef.current = chart;

    // Strategy equity line
    const strategySeries = chart.addSeries(LineSeries, {
      color: "#00B8D9",
      lineWidth: 2,
      priceLineVisible: false,
    });
    strategySeries.setData(
      equityCurve.map((p) => ({ time: p.time as Time, value: p.value }))
    );

    // Benchmark line
    const benchSeries = chart.addSeries(LineSeries, {
      color: "#8B95A5",
      lineWidth: 1,
      priceLineVisible: false,
      lineStyle: 2,
    });
    benchSeries.setData(
      benchmarkCurve.map((p) => ({ time: p.time as Time, value: p.value }))
    );

    // Drawdown highlighting using horizontal histogram
    if (drawdownPeriods.length > 0) {
      const ddMarkers = drawdownPeriods.flatMap((dd) => [
        { time: dd.start as Time, position: "inBar" as const, color: "#FF563033", shape: "square" as const, text: "", size: 3 },
        { time: dd.end as Time, position: "inBar" as const, color: "#FF563033", shape: "square" as const, text: "", size: 3 },
      ]);
      const ddMarkerPlugin = createSeriesMarkers(strategySeries, []);
      ddMarkerPlugin.setMarkers(drawdownPeriods.map((dd) => ({
        time: dd.start as Time,
        position: "aboveBar" as const,
        color: "#FF5630",
        shape: "circle" as const,
        text: `回撤 ${(dd.maxDrawdown * 100).toFixed(1)}%`,
        size: 2,
      })));
    }

    // Trade marks
    const tradeMarkerPlugin = createSeriesMarkers(strategySeries, []);
    tradeMarkerPlugin.setMarkers(
      trades.map((t) => ({
        time: t.time as Time,
        position: t.type === "BUY" ? ("belowBar" as const) : ("aboveBar" as const),
        color: t.type === "BUY" ? "#00B8D9" : "#FF5630",
        shape: t.type === "BUY" ? ("arrowUp" as const) : ("arrowDown" as const),
        text: t.type,
        size: 2,
      }))
    );

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [equityCurve, benchmarkCurve, trades, drawdownPeriods]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !chartRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          chartRef.current?.applyOptions({ width, height });
        }
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  return <div ref={containerRef} className={className} />;
}
