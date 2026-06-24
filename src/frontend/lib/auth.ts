import type { TokenResponse, UserResponse } from "@/types/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("athena_token") : null;
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Error ${res.status}`);
  }
  return res.json();
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  return request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
}

export async function register(
  username: string,
  email: string,
  password: string,
  displayName: string,
): Promise<TokenResponse> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password, displayName }),
  });
}

export async function getMe(): Promise<UserResponse> {
  return request("/auth/me");
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("athena_token");
}

export function setToken(token: string) {
  localStorage.setItem("athena_token", token);
}

export function clearToken() {
  localStorage.removeItem("athena_token");
}

export function isLoggedIn(): boolean {
  return getToken() !== null;
}
