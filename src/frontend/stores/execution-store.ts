import { create } from "zustand";
import type { ExecutionSheetContext, ExecutionPreviewResponse, OrderType, TradeSide, AlgoParams } from "@/types/execution";
import { previewExecution, submitPaperTrade } from "@/lib/execution-api";

interface ExecutionStore {
  isSheetOpen: boolean;
  sheetContext: ExecutionSheetContext | null;

  orderType: OrderType;
  size: number;
  algoParams: AlgoParams;

  preview: ExecutionPreviewResponse | null;
  previewLoading: boolean;

  submitting: boolean;
  submitResult: string | null;

  openSheet: (ctx: ExecutionSheetContext) => void;
  closeSheet: () => void;
  setOrderType: (t: OrderType) => void;
  setSize: (s: number) => void;
  setAlgoParams: (p: AlgoParams) => void;
  fetchPreview: (price: number) => Promise<void>;
  submit: (price: number) => Promise<void>;
  reset: () => void;
}

export const useExecutionStore = create<ExecutionStore>((set, get) => ({
  isSheetOpen: false,
  sheetContext: null,
  orderType: "MARKET",
  size: 100,
  algoParams: {},
  preview: null,
  previewLoading: false,
  submitting: false,
  submitResult: null,

  openSheet: (ctx) => set({
    isSheetOpen: true,
    sheetContext: ctx,
    orderType: "MARKET",
    size: ctx.defaultSize,
    algoParams: {},
    preview: null,
    previewLoading: false,
    submitting: false,
    submitResult: null,
  }),

  closeSheet: () => set({ isSheetOpen: false }),

  setOrderType: (t) => set({ orderType: t }),

  setSize: (s) => set({ size: s }),

  setAlgoParams: (p) => set({ algoParams: p }),

  fetchPreview: async (price) => {
    const { sheetContext, orderType, size, algoParams } = get();
    if (!sheetContext) return;
    set({ previewLoading: true });
    try {
      const result = await previewExecution({
        symbol: sheetContext.symbol,
        side: sheetContext.side,
        size,
        orderType,
        price,
        algoParams: orderType === "TWAP" || orderType === "VWAP" ? algoParams : undefined,
      });
      set({ preview: result, previewLoading: false });
    } catch {
      set({ previewLoading: false });
    }
  },

  submit: async (price) => {
    const { sheetContext, orderType, size, algoParams } = get();
    if (!sheetContext) return;
    set({ submitting: true });
    try {
      const result = await submitPaperTrade({
        symbol: sheetContext.symbol,
        side: sheetContext.side,
        size,
        orderType,
        price,
        algoParams: orderType === "TWAP" || orderType === "VWAP" ? algoParams : undefined,
      });
      set({ submitting: false, submitResult: result.orderId });
    } catch {
      set({ submitting: false, submitResult: "FAILED" });
    }
  },

  reset: () => set({
    isSheetOpen: false,
    sheetContext: null,
    orderType: "MARKET",
    size: 100,
    algoParams: {},
    preview: null,
    previewLoading: false,
    submitting: false,
    submitResult: null,
  }),
}));
