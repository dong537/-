export type VitalSigns = {
  height_cm: number;
  weight_kg: number;
  bmi?: number | null;
  systolic_bp: number;
  diastolic_bp: number;
  heart_rate: number;
  blood_oxygen: number;
  blood_glucose?: number | null;
  blood_lipid?: number | null;
  uric_acid?: number | null;
  notes?: string | null;
};

export type HealthProfilePayload = {
  user_id: string;
  name: string;
  age: number;
  gender: string;
  vital_signs: VitalSigns;
};

export type HealthMetric = {
  metric_id: string;
  profile_id: string;
  user_id: string;
  recorded_at: string;
  vital_signs: VitalSigns;
  warnings: string[];
};

export type HealthProfileResponse = {
  profile_id: string;
  user_id: string;
  name: string;
  age: number;
  gender: string;
  created_at: string;
  updated_at: string;
  latest_metric: HealthMetric | null;
  metric_history: HealthMetric[];
};

export type DeviceBindPayload = {
  user_id: string;
  device_name: string;
  device_model: string;
  connection_type: "wifi" | "bluetooth" | "usb" | "mock";
  auto_capture_enabled: boolean;
  capture_interval_minutes: number;
  capture_window: string;
};

export type DeviceResponse = DeviceBindPayload & {
  device_id: string;
  provider: string;
  status: string;
  battery_percent: number;
  storage_free_gb: number;
  offline_cache_count: number;
  status_detail?: string | null;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
};

export type CaptureCreatePayload = {
  user_id: string;
  device_id?: string | null;
  capture_mode: "manual" | "auto" | "offline_cache";
  scene_hint?: string | null;
  image_url?: string | null;
  captured_at?: string | null;
};

export type BehaviorRecord = {
  behavior_id: string;
  capture_id: string;
  user_id: string;
  category: "diet" | "exercise" | "sleep" | "daily" | string;
  label: string;
  confidence: number;
  body_score: number;
  mental_score: number;
  impact: string;
  risk_flags: string[];
  recommendations: string[];
  created_at: string;
};

export type CaptureResponse = {
  capture_id: string;
  user_id: string;
  device_id?: string | null;
  capture_mode: string;
  scene_hint?: string | null;
  image_url?: string | null;
  status: string;
  special_tag?: string | null;
  captured_at: string;
  synced_at: string;
  analysis: BehaviorRecord | null;
};

export type DailyLogResponse = {
  daily_log_id: string;
  user_id: string;
  date: string;
  overall_score: number;
  body_score: number;
  mental_score: number;
  behavior_summary: {
    diet_count?: number;
    exercise_count?: number;
    sleep_count?: number;
    daily_count?: number;
    total_records?: number;
    top_behaviors?: Array<[string, number]>;
  };
  abnormal_behaviors: string[];
  risk_tips: string[];
  generated_at: string;
};

export type WeeklyReportResponse = {
  report_id: string;
  user_id: string;
  week_start: string;
  week_end: string;
  average_overall_score: number;
  average_body_score: number;
  average_mental_score: number;
  trend: Array<{
    date: string;
    overall_score: number;
    body_score: number;
    mental_score: number;
  }>;
  behavior_analysis: Record<string, unknown>;
  body_assessment: string;
  mental_assessment: string;
  suggestions: Record<string, string[]>;
  next_week_goals: string[];
  comparison: string;
  generated_at: string;
};

export type HealthDashboard = {
  profile: HealthProfileResponse | null;
  device: DeviceResponse | null;
  today_log: DailyLogResponse | null;
  weekly_report: WeeklyReportResponse | null;
  recent_captures: CaptureResponse[];
  recent_behaviors: BehaviorRecord[];
  metric_trend: HealthMetric[];
  daily_history: DailyLogResponse[];
  weekly_history: WeeklyReportResponse[];
  status: {
    profile_ready: boolean;
    device_ready: boolean;
    capture_count: number;
    behavior_count: number;
    daily_log_ready: boolean;
    weekly_report_ready: boolean;
  };
};

export type OfflineSyncResponse = {
  device: DeviceResponse;
  synced_captures: CaptureResponse[];
};

export type TrendResponse = {
  user_id: string;
  range_days: number;
  score_series: Array<Record<string, number | string>>;
  vital_series: Array<Record<string, number | string | null>>;
  behavior_series: Array<Record<string, number | string>>;
  risk_flags: Record<string, number>;
  generated_at: string;
};

export type DeleteUserDataResponse = {
  user_id: string;
  scope: string;
  deleted_counts: Record<string, number>;
  status: string;
};

export type DemoFlowResponse = {
  profile: HealthProfileResponse;
  device: DeviceResponse;
  captures: CaptureResponse[];
  today_log: DailyLogResponse;
  weekly_report: WeeklyReportResponse;
};

export type GeoPoint = {
  lng: number;
  lat: number;
};

export type RouteNode = {
  id: string;
  name: string;
  type: string;
  lng: number;
  lat: number;
  order_index: number;
  stay_minutes: number;
  walking_minutes: number;
  photo_value: number;
  rest_value: number;
  ai_reason: string;
};

export type RoutePlan = {
  route_id: string;
  route_name: string;
  summary: string;
  change_summary?: string | null;
  total_minutes: number;
  nodes: RouteNode[];
  tips: string[];
};

export type MediaAsset = {
  media_id: string;
  trip_id: string;
  kind: string;
  filename: string;
  url?: string | null;
  status: string;
};

export type FrameAsset = {
  frame_id: string;
  media_id: string;
  trip_id: string;
  timestamp_ms: number;
  image_url: string;
  thumbnail_url: string;
  ai_caption?: string | null;
  ai_score?: Record<string, number> | null;
  selected: boolean;
  selected_reason?: string | null;
  marked: boolean;
  marked_reason?: string | null;
};

export type CompanionResponse = {
  message: string;
  shooting_tips: string[];
  scene_tags: string[];
  safety_tips: string[];
  share_value: number;
  frame?: FrameAsset | null;
};

export type TripEvent = {
  event_id: string;
  trip_id: string;
  event_type: string;
  title: string;
  detail: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type ExportResponse = {
  export_id: string;
  status: string;
  selected_frames: FrameAsset[];
  route_recap: string;
  social_copy: string;
  story_events: TripEvent[];
  video_draft: Array<{
    order: number;
    frame_id: string;
    duration_seconds: number;
    caption: string;
    shot_type: string;
    route_node_name?: string | null;
    transition: string;
    edit_note: string;
  }>;
};

export type ExportManifest = {
  schema: string;
  generated_at: string;
  trip: {
    trip_id: string;
    destination: string;
    duration_minutes: number;
    preferences: string[];
  };
  route: {
    route_id: string | null;
    route_name: string | null;
    nodes: RouteNode[];
  };
  media_assets: Array<{
    media_id: string;
    kind: string;
    filename: string;
    url?: string | null;
  }>;
  selected_frames: Array<{
    frame_id: string;
    timestamp_ms: number;
    image_url: string;
    caption?: string | null;
    score?: Record<string, number> | null;
    selected_reason?: string | null;
    marked?: boolean;
    marked_reason?: string | null;
  }>;
  video_draft: ExportResponse["video_draft"];
  story_events: TripEvent[];
  copy: {
    route_recap: string;
    social_copy: string;
  };
  handoff: {
    suggested_workflow: string;
    status: string;
  };
};

export type TripDetail = {
  trip: Record<string, unknown>;
  route?: RoutePlan | null;
  media: MediaAsset[];
  frames: FrameAsset[];
  exports: ExportResponse[];
  events: TripEvent[];
};

export type TripSummary = {
  trip_id: string;
  destination: string;
  duration_minutes: number;
  status: string;
  created_at: string;
  updated_at: string;
  route_ready: boolean;
  media_count: number;
  frame_count: number;
  export_count: number;
  event_count: number;
};

export type UserStatus = "normal" | "tired" | "photo" | "food" | "short_time" | "quiet";
