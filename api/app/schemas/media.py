from pydantic import BaseModel


class MediaAsset(BaseModel):
    media_id: str
    trip_id: str
    kind: str
    filename: str
    url: str | None = None
    status: str


class FrameAsset(BaseModel):
    frame_id: str
    media_id: str
    trip_id: str
    timestamp_ms: int
    image_url: str
    thumbnail_url: str
    ai_caption: str | None = None
    ai_score: dict | None = None
    selected: bool = False
    selected_reason: str | None = None
    marked: bool = False
    marked_reason: str | None = None


class ExtractFramesResponse(BaseModel):
    job_id: str
    status: str
    frames: list[FrameAsset]


class AnalyzeFrameRequest(BaseModel):
    frame_id: str | None = None
    route_node_id: str | None = None
    user_status: str = "normal"


class CompanionResponse(BaseModel):
    message: str
    shooting_tips: list[str]
    scene_tags: list[str]
    safety_tips: list[str]
    share_value: int
    frame: FrameAsset | None = None


class MarkFrameRequest(BaseModel):
    marked: bool = True
    reason: str | None = None


class ExportResponse(BaseModel):
    export_id: str
    status: str
    selected_frames: list[FrameAsset]
    route_recap: str
    social_copy: str
    video_draft: list[dict]
    story_events: list[dict]


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str | None = None
    result: dict | None = None
