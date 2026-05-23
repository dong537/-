import type { CompanionResponse, ExportManifest, ExportResponse, FrameAsset, MediaAsset, RoutePlan, TripDetail, UserStatus } from "../types";

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
      reason: marked ? "用户标记的精彩瞬间" : null
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

export async function getRuntimeConfig() {
  return request<{
    ai_provider: string;
    ai_mode: string;
    map_provider: string;
    map_mode: string;
    app_base_url: string;
    frame_extract_interval_seconds: number;
    max_frame_analysis_count: number;
    max_upload_bytes: number;
    request_log_enabled: boolean;
    text_model: string;
    vision_model: string;
  }>("/api/dev/config");
}

export async function resetDemo() {
  return request<{ status: string }>("/api/dev/reset", { method: "POST" });
}
