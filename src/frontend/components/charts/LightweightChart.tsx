"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  createSeriesMarkers,
  type IChartApi,
  type Time,
  type LineData,
} from "lightweight-charts";
import type { KlineData } from "@/lib/mock-kline";
import { computeMAs, computeMACD } from "@/lib/mock-kline";

interface LightweightChartProps {
  data: KlineData;
  className?: string;
}

export default function LightweightChart({ data, className }: LightweightChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const subChartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || data.candles.length === 0) return;
    container.innerHTML = "";

    const totalWidth = container.clientWidth || 800;
    const totalHeight = container.clientHeight || 600;
    const mainHeight = Math.floor(totalHeight * 0.65);
    const subHeight = totalHeight - mainHeight;

    const mainDiv = document.createElement("div");
    mainDiv.style.width = "100%";
    mainDiv.style.height = `${mainHeight}px`;
    container.appendChild(mainDiv);

    const subDiv = document.createElement("div");
    subDiv.style.width = "100%";
    subDiv.style.height = `${subHeight}px`;
    container.appendChild(subDiv);

    const baseLayout = {
      background: { type: ColorType.Solid, color: "#151924" },
      textColor: "#8B95A5",
    };
    const baseGrid = {
      vertLines: { color: "#2A2E39" },
      horzLines: { color: "#2A2E39" },
    };
    const baseScale = { borderColor: "#2A2E39" };

    const mainChart = createChart(mainDiv, {
      width: totalWidth,
      height: mainHeight,
      layout: baseLayout,
      grid: baseGrid,
      rightPriceScale: baseScale,
      timeScale: { ...baseScale, timeVisible: true, secondsVisible: false },
      crosshair: { mode: 0 },
    });

    const subChart = createChart(subDiv, {
      width: totalWidth,
      height: subHeight,
      layout: baseLayout,
      grid: baseGrid,
      rightPriceScale: baseScale,
      timeScale: { ...baseScale, visible: false },
      crosshair: { mode: 0 },
    });

    // --- Candlestick ---
    const candleSeries = mainChart.addSeries(CandlestickSeries, {
      upColor: "#00B8D9",
      downColor: "#FF5630",
      borderUpColor: "#00B8D9",
      borderDownColor: "#FF5630",
      wickUpColor: "#00B8D9",
      wickDownColor: "#FF5630",
    });
    candleSeries.setData(
      data.candles.map((c) => ({
        time: c.time as Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );

    // --- Trade markers ---
    const markersPlugin = createSeriesMarkers(candleSeries, []);
    markersPlugin.setMarkers(
      data.trades.map((t) => ({
        time: t.time as Time,
        position: t.type === "BUY" ? ("belowBar" as const) : ("aboveBar" as const),
        color: t.type === "BUY" ? "#00B8D9" : "#FF5630",
        shape: t.type === "BUY" ? ("arrowUp" as const) : ("arrowDown" as const),
        text: t.type === "BUY" ? "买" : "卖",
        size: 2.5,
      }))
    );

    // --- MAs ---
    const closes = data.candles.map((c) => c.close);
    const mas = computeMAs(closes);
    const maColors: Record<string, string> = { ma5: "#FFD700", ma10: "#FF6B6B", ma20: "#4ECDC4" };

    for (const key of Object.keys(mas) as Array<keyof typeof mas>) {
      const values = mas[key];
      const series = mainChart.addSeries(LineSeries, {
        color: maColors[key],
        lineWidth: 1,
        priceLineVisible: false,
      });
      series.setData(
        values
          .map((v, i) =>
            v !== null ? { time: data.candles[i].time as Time, value: v } : null
          )
          .filter((x): x is LineData => x !== null)
      );
    }

    // --- Volume ---
    const volSeries = subChart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    volSeries.setData(
      data.candles.map((c) => ({
        time: c.time as Time,
        value: c.volume,
        color: c.close >= c.open ? "#00B8D940" : "#FF563040",
      }))
    );

    // --- MACD ---
    const macd = computeMACD(closes);

    const macdHist = subChart.addSeries(HistogramSeries, {
      priceScaleId: "macd",
    });
    macdHist.setData(
      data.candles
        .map((c, i) => {
          const v = macd.histogram[i];
          if (v === null) return null;
          return {
            time: c.time as Time,
            value: v,
            color: v >= 0 ? "#00B8D960" : "#FF563060",
          };
        })
        .filter((x): x is NonNullable<typeof x> => x !== null) as never
    );

    const difSeries = subChart.addSeries(LineSeries, {
      color: "#FFD700",
      lineWidth: 1,
      priceLineVisible: false,
      priceScaleId: "macd",
    });
    difSeries.setData(
      data.candles
        .map((c, i) => {
          const v = macd.dif[i];
          if (v === null) return null;
          return { time: c.time as Time, value: v };
        })
        .filter((x): x is NonNullable<typeof x> => x !== null)
    );

    const deaSeries = subChart.addSeries(LineSeries, {
      color: "#FF6B6B",
      lineWidth: 1,
      priceLineVisible: false,
      priceScaleId: "macd",
    });
    deaSeries.setData(
      data.candles
        .map((c, i) => {
          const v = macd.dea[i];
          if (v === null) return null;
          return { time: c.time as Time, value: v };
        })
        .filter((x): x is NonNullable<typeof x> => x !== null)
    );

    // --- Time scale sync ---
    const syncSub = (range: { from: number; to: number } | null) => {
      if (range) subChart.timeScale().setVisibleLogicalRange(range);
    };
    const syncMain = (range: { from: number; to: number } | null) => {
      if (range) mainChart.timeScale().setVisibleLogicalRange(range);
    };
    mainChart.timeScale().subscribeVisibleLogicalRangeChange(syncSub);
    subChart.timeScale().subscribeVisibleLogicalRangeChange(syncMain);

    chartRef.current = mainChart;
    subChartRef.current = subChart;

    return () => {
      mainChart.timeScale().unsubscribeVisibleLogicalRangeChange(syncSub);
      subChart.timeScale().unsubscribeVisibleLogicalRangeChange(syncMain);
      mainChart.remove();
      subChart.remove();
      chartRef.current = null;
      subChartRef.current = null;
    };
  }, [data]);

  // --- ResizeObserver ---
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          const mainH = Math.floor(height * 0.65);
          const subH = height - mainH;
          chartRef.current?.applyOptions({ width, height: mainH });
          subChartRef.current?.applyOptions({ width, height: subH });
        }
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  return <div ref={containerRef} className={className} />;
}
