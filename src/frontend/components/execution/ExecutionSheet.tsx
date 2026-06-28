"use client";

import { useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useExecutionStore } from "@/stores/execution-store";
import type { OrderType, TradeSide } from "@/types/execution";
import { cn } from "@/lib/utils";

const ORDER_TYPES: { value: OrderType; label: string }[] = [
  { value: "MARKET", label: "MARKET" },
  { value: "LIMIT", label: "LIMIT" },
  { value: "TWAP", label: "TWAP" },
  { value: "VWAP", label: "VWAP" },
];

const POSITION_PRESETS = [25, 50, 75, 100];

export default function ExecutionSheet() {
  const isOpen = useExecutionStore((s) => s.isSheetOpen);
  const ctx = useExecutionStore((s) => s.sheetContext);
  const orderType = useExecutionStore((s) => s.orderType);
  const size = useExecutionStore((s) => s.size);
  const algoParams = useExecutionStore((s) => s.algoParams);
  const preview = useExecutionStore((s) => s.preview);
  const previewLoading = useExecutionStore((s) => s.previewLoading);
  const submitting = useExecutionStore((s) => s.submitting);
  const submitResult = useExecutionStore((s) => s.submitResult);

  const closeSheet = useExecutionStore((s) => s.closeSheet);
  const setOrderType = useExecutionStore((s) => s.setOrderType);
  const setSize = useExecutionStore((s) => s.setSize);
  const setAlgoParams = useExecutionStore((s) => s.setAlgoParams);
  const fetchPreview = useExecutionStore((s) => s.fetchPreview);
  const submit = useExecutionStore((s) => s.submit);
  const reset = useExecutionStore((s) => s.reset);

  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const triggerPreview = useCallback(() => {
    if (!ctx) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchPreview(ctx.price);
    }, 350);
  }, [ctx, fetchPreview]);

  useEffect(() => {
    if (isOpen && ctx) triggerPreview();
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [isOpen, ctx, orderType, size, algoParams, triggerPreview]);

  useEffect(() => {
    if (submitResult && !submitting) {
      const timer = setTimeout(() => {
        reset();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [submitResult, submitting, reset]);

  if (!ctx) return null;

  const isBuy = ctx.side === "BUY";
  const sideColor = isBuy ? "text-[#00B8D9]" : "text-[#FF5630]";
  const sideBg = isBuy ? "bg-[#00B8D9]/10 border-[#00B8D9]/30" : "bg-[#FF5630]/10 border-[#FF5630]/30";
  const sideBadge = isBuy ? "BUY" : "SELL";
  const maxShares = 10000;

  const handlePresetClick = (pct: number) => {
    setSize(Math.round((maxShares * pct) / 100));
  };

  const handleSubmit = () => {
    if (ctx && !submitting) submit(ctx.price);
  };

  const showAlgoParams = orderType === "TWAP" || orderType === "VWAP";

  return (
    <Sheet open={isOpen} onOpenChange={(open) => { if (!open) reset(); }}>
      <SheetContent
        side="right"
        className="w-[440px] max-w-[440px] p-0 flex flex-col border-l border-[#2A2E39] bg-card backdrop-blur-md"
      >
        <SheetHeader className="px-5 pt-5 pb-0 text-left">
          <SheetTitle className="flex items-center gap-3">
            <span
              className={cn(
                "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-bold tracking-widest",
                sideBg, sideColor
              )}
            >
              {sideBadge}
            </span>
            <span className="font-mono text-base text-foreground">{ctx.symbol}</span>
            <span className="text-xs text-muted-foreground">{ctx.name}</span>
          </SheetTitle>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="font-mono text-2xl font-bold text-foreground">
              ¥{ctx.price.toFixed(2)}
            </span>
            <span className="font-mono text-xs text-muted-foreground animate-pulse">
              ▏ LIVE
            </span>
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {/* Algo Routing Selector */}
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Algo Routing
            </div>
            <Tabs
              value={orderType}
              onValueChange={(v) => setOrderType(v as OrderType)}
            >
              <TabsList className="w-full grid grid-cols-4 bg-secondary/50">
                {ORDER_TYPES.map((ot) => (
                  <TabsTrigger
                    key={ot.value}
                    value={ot.value}
                    className="text-[11px] font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                  >
                    {ot.label}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>

            <AnimatePresence>
              {showAlgoParams && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="mt-3 p-3 rounded-md bg-secondary/30 border border-border/50 space-y-3">
                    <div>
                      <label className="text-[11px] text-muted-foreground block mb-1">
                        Duration (minutes)
                      </label>
                      <input
                        type="number"
                        className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. 30"
                        value={algoParams.durationMinutes ?? ""}
                        onChange={(e) => {
                          setAlgoParams({
                            ...algoParams,
                            durationMinutes: e.target.value ? Number(e.target.value) : undefined,
                          });
                        }}
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-muted-foreground block mb-1">
                        Max Participation (%)
                      </label>
                      <input
                        type="number"
                        className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. 10"
                        value={algoParams.maxParticipationRate ?? ""}
                        onChange={(e) => {
                          setAlgoParams({
                            ...algoParams,
                            maxParticipationRate: e.target.value ? Number(e.target.value) : undefined,
                          });
                        }}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Position Sizing */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Position Sizing
              </span>
              <span className="font-mono text-xs text-muted-foreground">
                Max: {maxShares.toLocaleString()}
              </span>
            </div>
            <input
              type="number"
              className="w-full rounded-md border border-border bg-background px-3 py-2 font-mono text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              value={size}
              min={1}
              max={maxShares}
              onChange={(e) => setSize(Math.min(maxShares, Math.max(1, Number(e.target.value) || 1)))}
            />
            <div className="mt-2 flex items-center gap-2">
              <Slider
                value={[(size / maxShares) * 100]}
                onValueChange={([v]) => setSize(Math.round((v / 100) * maxShares))}
                min={0}
                max={100}
                step={1}
                className="flex-1"
              />
              <span className="font-mono text-xs text-primary w-10 text-right">
                {Math.round((size / maxShares) * 100)}%
              </span>
            </div>
            <div className="mt-2 flex gap-1.5">
              {POSITION_PRESETS.map((pct) => (
                <button
                  key={pct}
                  onClick={() => handlePresetClick(pct)}
                  className="flex-1 rounded-md border border-border/50 px-2 py-1 text-[11px] font-medium text-muted-foreground hover:border-primary/40 hover:text-foreground transition-colors"
                >
                  {pct}%
                </button>
              ))}
            </div>
            <div className="mt-1 text-right">
              <span className="text-[11px] text-muted-foreground">
                Est. Notional:{" "}
                <span className="font-mono text-foreground">
                  ¥{((size * ctx.price) / 10000).toFixed(1)}万
                </span>
              </span>
            </div>
          </div>

          {/* Pre-Trade Analytics */}
          <div className="rounded-md bg-[#151924] border-l-4 border-yellow-500/50 p-3.5 space-y-2.5">
            <div className="text-xs font-semibold uppercase tracking-wide text-yellow-500/80">
              Pre-Trade Analytics
            </div>
            {previewLoading ? (
              <div className="flex items-center gap-2 py-2">
                <div className="h-3 w-3 rounded-full border border-yellow-500/40 border-t-yellow-500 animate-spin" />
                <span className="text-[11px] text-[#8F9BBA]">Computing...</span>
              </div>
            ) : preview ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-[#8F9BBA]">Slippage</span>
                  <span className="font-mono text-xs text-yellow-400">
                    {preview.slippageBps.toFixed(1)} bps
                    <span className="text-[#8F9BBA] ml-1">
                      (¥{preview.slippageAmount.toFixed(2)})
                    </span>
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-[#8F9BBA]">Market Impact</span>
                  <span className="font-mono text-xs text-orange-400">
                    {preview.marketImpactBps.toFixed(1)} bps
                    <span className="text-[#8F9BBA] ml-1">
                      (¥{preview.marketImpactAmount.toFixed(2)})
                    </span>
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-[#8F9BBA]">Est. Avg Price</span>
                  <span className="font-mono text-xs text-foreground">
                    ¥{preview.estimatedAvgPrice.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-[#8F9BBA]">Participation</span>
                  <span className="font-mono text-xs text-[#8F9BBA]">
                    {preview.participationRate.toFixed(2)}%
                  </span>
                </div>
                <div className="border-t border-[#2A2E39] pt-2 flex items-center justify-between">
                  <span className="text-[11px] text-[#8F9BBA]">
                    Stress Test {preview.stressTestScenario}
                  </span>
                  <span className="font-mono text-xs text-[#FF5630]">
                    -¥{preview.stressTestLoss.toFixed(2)}
                  </span>
                </div>
              </>
            ) : (
              <span className="text-[11px] text-[#8F9BBA]">No data available</span>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <div className="border-t border-border px-5 py-4">
          {submitResult ? (
            <div className="rounded-md bg-[#00B8D9]/10 border border-[#00B8D9]/30 px-4 py-3 text-center">
              <span className="text-xs text-[#00B8D9] font-semibold">
                Order Executed Successfully
              </span>
              <div className="mt-1 font-mono text-[11px] text-[#8F9BBA]">
                ID: {submitResult}
              </div>
            </div>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={submitting}
              className={cn(
                "w-full h-12 text-sm font-bold tracking-widest uppercase transition-all duration-300",
                isBuy
                  ? "bg-[#00B8D9] text-black hover:bg-[#00B8D9]/80 shadow-[0_0_30px_rgba(0,184,217,0.15)]"
                  : "bg-[#FF5630] text-black hover:bg-[#FF5630]/80 shadow-[0_0_30px_rgba(255,86,48,0.15)]"
              )}
            >
              {submitting ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin" />
                  SUBMITTING...
                </span>
              ) : (
                "SUBMIT TO PAPER TRADING"
              )}
            </Button>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
