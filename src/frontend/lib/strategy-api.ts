const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface StrategyNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

interface StrategyEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface StrategyDTO {
  id: string;
  name: string;
  description: string;
  category: string;
  nodes: StrategyNode[];
  edges: StrategyEdge[];
  is_template: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StrategyCreateRequest {
  name: string;
  description?: string;
  category: string;
  nodes: StrategyNode[];
  edges: StrategyEdge[];
  is_template?: boolean;
}

export interface StrategyUpdateRequest {
  name?: string;
  description?: string;
  nodes?: StrategyNode[];
  edges?: StrategyEdge[];
  is_active?: boolean;
}

async function fetchApi<T>(path: string, options?: RequestInit, timeoutMs = 15000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }
    if (res.status === 204) return undefined as T;
    return res.json();
  } finally {
    clearTimeout(timer);
  }
}

export async function getStrategies(): Promise<StrategyDTO[]> {
  return fetchApi<StrategyDTO[]>("/strategies");
}

export async function getStrategyTemplates(): Promise<StrategyDTO[]> {
  return fetchApi<StrategyDTO[]>("/strategies/templates");
}

export async function getStrategy(id: string): Promise<StrategyDTO> {
  return fetchApi<StrategyDTO>(`/strategies/${id}`);
}

export async function createStrategy(data: StrategyCreateRequest): Promise<StrategyDTO> {
  return fetchApi<StrategyDTO>("/strategies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function updateStrategy(id: string, data: StrategyUpdateRequest): Promise<StrategyDTO> {
  return fetchApi<StrategyDTO>(`/strategies/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteStrategy(id: string): Promise<void> {
  return fetchApi<void>(`/strategies/${id}`, { method: "DELETE" });
}
