from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    lng: float
    lat: float


class CreateTripRequest(BaseModel):
    destination: str = Field(..., min_length=1)
    duration_minutes: int = Field(default=120, ge=15, le=720)
    preferences: list[str] = Field(default_factory=list)
    use_panorama_camera: bool = True
    current_location: GeoPoint | None = None


class TripResponse(BaseModel):
    trip_id: str
    status: str


class TripSummary(BaseModel):
    trip_id: str
    destination: str
    duration_minutes: int
    status: str
    created_at: str
    updated_at: str
    route_ready: bool
    media_count: int
    frame_count: int
    export_count: int
    event_count: int


class RouteNode(BaseModel):
    id: str
    name: str
    type: str
    lng: float
    lat: float
    order_index: int
    stay_minutes: int
    walking_minutes: int
    photo_value: int
    rest_value: int
    ai_reason: str


class RoutePlan(BaseModel):
    route_id: str
    route_name: str
    summary: str
    change_summary: str | None = None
    total_minutes: int
    nodes: list[RouteNode]
    tips: list[str]


class RerouteRequest(BaseModel):
    status_action: str
    remaining_minutes: int = Field(default=80, ge=5, le=720)
    current_location: GeoPoint | None = None


class TripDetail(BaseModel):
    trip: dict
    route: dict | None = None
    media: list[dict]
    frames: list[dict]
    exports: list[dict]
    events: list[dict]
