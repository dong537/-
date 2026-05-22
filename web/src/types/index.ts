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

export type TripEvent = {
  event_id: string;
  trip_id: string;
  event_type: string;
  title: string;
  detail: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type TripDetail = {
  trip: Record<string, unknown>;
  route?: RoutePlan | null;
  media: MediaAsset[];
  frames: FrameAsset[];
  exports: ExportResponse[];
  events: TripEvent[];
};

export type UserStatus = "normal" | "tired" | "photo" | "food" | "short_time" | "quiet";
