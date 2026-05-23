import type {
  CaptureCreatePayload,
  CaptureResponse,
  DailyLogResponse,
  DemoFlowResponse,
  DeviceBindPayload,
  DeviceResponse,
  HealthDashboard,
  HealthProfilePayload,
  HealthProfileResponse,
  WeeklyReportResponse
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers
    }
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export type RuntimeConfig = {
  ai_provider: string;
  ai_mode: string;
  map_provider: string;
  map_mode: string;
  app_base_url: string;
  frame_extract_interval_seconds: number;
  max_frame_analysis_count: number;
  max_upload_bytes: number;
  request_log_enabled: boolean;
  store_persistence_enabled: boolean;
  state_file: string;
  store_loaded_at: string | null;
  store_saved_at: string | null;
  store_persistence_error: string | null;
  counts?: Record<string, number>;
  text_model: string;
  vision_model: string;
};

export type HealthStatus = {
  status: string;
  app_env: string;
  ai_provider: string;
  ai_mode: string;
  map_provider: string;
  map_mode: string;
};

export type ReadyStatus = {
  status: "ready" | "degraded";
  checks: Record<string, boolean>;
};

export async function getHealth() {
  return request<HealthStatus>("/health");
}

export async function getReady() {
  const response = await fetch(`${API_BASE_URL}/ready`);
  if (response.status !== 200 && response.status !== 503) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<ReadyStatus>;
}

export async function getRuntimeConfig() {
  return request<RuntimeConfig>("/api/dev/config");
}

export async function resetDemo() {
  return request<{ status: string }>("/api/dev/reset", { method: "POST" });
}

export async function getHealthDashboard(userId = "demo_user") {
  return request<HealthDashboard>(`/api/health/dashboard?user_id=${encodeURIComponent(userId)}`);
}

export async function saveHealthProfile(payload: HealthProfilePayload) {
  return request<HealthProfileResponse>("/api/health/profiles", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function bindHealthDevice(payload: DeviceBindPayload) {
  return request<DeviceResponse>("/api/health/devices/bind", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createHealthCapture(payload: CaptureCreatePayload) {
  return request<CaptureResponse>("/api/health/captures", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function generateDailyLog(userId = "demo_user") {
  return request<DailyLogResponse>(`/api/health/daily/${encodeURIComponent(userId)}`, { method: "POST" });
}

export async function generateWeeklyReport(userId = "demo_user") {
  return request<WeeklyReportResponse>(`/api/health/weekly/${encodeURIComponent(userId)}`, { method: "POST" });
}

export async function runHealthDemo(userId = "demo_user") {
  return request<DemoFlowResponse>(`/api/health/demo?user_id=${encodeURIComponent(userId)}`, { method: "POST" });
}
