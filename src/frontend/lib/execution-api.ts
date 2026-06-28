import type { ExecutionPreviewRequest, ExecutionPreviewResponse, PaperTradeRequest, PaperTradeResponse } from "@/types/execution";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function postApi<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function previewExecution(req: ExecutionPreviewRequest): Promise<ExecutionPreviewResponse> {
  return postApi<ExecutionPreviewResponse>("/execution/preview", req);
}

export async function submitPaperTrade(req: PaperTradeRequest): Promise<PaperTradeResponse> {
  return postApi<PaperTradeResponse>("/execution/paper-trade", req);
}
