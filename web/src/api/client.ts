import type {
  CompanionResponse,
  CaptureCreatePayload,
  CaptureResponse,
  DailyLogResponse,
  DeleteUserDataResponse,
  DemoFlowResponse,
  DeviceBindPayload,
  DeviceResponse,
  ExportManifest,
  ExportResponse,
  FrameAsset,
  HealthDashboard,
  HealthProfilePayload,
  HealthProfileResponse,
  MediaAsset,
  OfflineSyncResponse,
  RoutePlan,
  TripDetail,
  TripSummary,
  TrendResponse,
  UserStatus,
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

export async function updateHealthDevice(
  deviceId: string,
  payload: Partial<Pick<DeviceResponse, "auto_capture_enabled" | "capture_interval_minutes" | "capture_window" | "status" | "battery_percent" | "storage_free_gb" | "status_detail">>
) {
  return request<DeviceResponse>(`/api/health/devices/${encodeURIComponent(deviceId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export async function syncHealthDevice(deviceId: string) {
  return request<OfflineSyncResponse>(`/api/health/devices/${encodeURIComponent(deviceId)}/sync`, { method: "POST" });
}

export async function createHealthCapture(payload: CaptureCreatePayload) {
  return request<CaptureResponse>("/api/health/captures", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function reviewHealthCapture(captureId: string, payload: { scene_hint: string; manual_note?: string | null }) {
  return request<CaptureResponse>(`/api/health/captures/${encodeURIComponent(captureId)}/review`, {
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

export async function getHealthTrends(userId = "demo_user", rangeDays = 30) {
  return request<TrendResponse>(`/api/health/trends/${encodeURIComponent(userId)}?range_days=${rangeDays}`);
}

export async function deleteHealthUserData(userId = "demo_user", scope = "all") {
  return request<DeleteUserDataResponse>(`/api/health/users/${encodeURIComponent(userId)}?scope=${encodeURIComponent(scope)}`, {
    method: "DELETE"
  });
}

export async function downloadWeeklyReportPdf(reportId: string) {
  const response = await fetch(`${API_BASE_URL}/api/health/weekly/reports/${encodeURIComponent(reportId)}/pdf`);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.blob();
}

export async function runHealthDemo(userId = "demo_user") {
  return request<DemoFlowResponse>(`/api/health/demo?user_id=${encodeURIComponent(userId)}`, { method: "POST" });
}

export async function createTrip(payload: {
  destination: string;
  duration_minutes: number;
  preferences: string[];
  use_panorama_camera: boolean;
}) {
  return request<{ trip_id: string; status: string }>("/api/trips", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listTrips(limit = 5) {
  return request<TripSummary[]>(`/api/trips?limit=${limit}`);
}

export async function generateRoute(tripId: string) {
  return request<RoutePlan>(`/api/trips/${tripId}/route`, { method: "POST" });
}

export async function getTripDetail(tripId: string) {
  return request<TripDetail>(`/api/trips/${tripId}`);
}

export async function rerouteTrip(tripId: string, status: UserStatus) {
  return request<RoutePlan>(`/api/trips/${tripId}/reroute`, {
    method: "POST",
    body: JSON.stringify({ status_action: status, remaining_minutes: 80 })
  });
}

export async function uploadMedia(tripId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<MediaAsset>(`/api/trips/${tripId}/media`, {
    method: "POST",
    body: form
  });
}

export async function createDemoMedia(tripId: string) {
  return request<MediaAsset>(`/api/trips/${tripId}/media/demo`, { method: "POST" });
}

export async function extractFrames(mediaId: string) {
  return request<{ job_id: string; status: string; frames: FrameAsset[] }>(`/api/media/${mediaId}/extract-frames`, {
    method: "POST"
  });
}

export async function markFrame(frameId: string, marked: boolean) {
  return request<FrameAsset>(`/api/frames/${frameId}/mark`, {
    method: "POST",
    body: JSON.stringify({
      marked,
      reason: marked ? "user marked favorite moment" : null
    })
  });
}

export async function analyzeCompanion(tripId: string, payload: { frame_id?: string; route_node_id?: string; user_status: UserStatus }) {
  return request<CompanionResponse>(`/api/trips/${tripId}/companion/analyze`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createExport(tripId: string) {
  return request<ExportResponse>(`/api/trips/${tripId}/exports`, { method: "POST" });
}

export async function getExportManifest(exportId: string) {
  return request<ExportManifest>(`/api/exports/${exportId}/manifest`);
}

export async function getExportBundle(exportId: string) {
  const response = await fetch(`${API_BASE_URL}/api/exports/${exportId}/bundle`);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.blob();
}
