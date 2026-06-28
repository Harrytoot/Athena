import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const httpClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

httpClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("athena_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("athena_token");
        window.location.href = "/login";
      }
    }
    const message = error.response?.data?.detail || error.message || "请求失败";
    return Promise.reject(new Error(message));
  },
);
