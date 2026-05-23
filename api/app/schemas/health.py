from pydantic import BaseModel, Field


class VitalSignsInput(BaseModel):
    height_cm: float = Field(..., ge=80, le=230)
    weight_kg: float = Field(..., ge=20, le=250)
    bmi: float | None = Field(default=None, ge=10, le=80)
    systolic_bp: int = Field(..., ge=60, le=260)
    diastolic_bp: int = Field(..., ge=30, le=180)
    heart_rate: int = Field(..., ge=30, le=220)
    blood_oxygen: int = Field(..., ge=50, le=100)
    blood_glucose: float | None = Field(default=None, ge=1.0, le=40.0)
    blood_lipid: float | None = Field(default=None, ge=0.1, le=20.0)
    uric_acid: float | None = Field(default=None, ge=50, le=1200)
    notes: str | None = Field(default=None, max_length=500)


class HealthProfileRequest(BaseModel):
    user_id: str = Field(default="demo_user", min_length=1)
    name: str = Field(default="Demo User", min_length=1, max_length=80)
    age: int = Field(default=32, ge=1, le=120)
    gender: str = Field(default="unspecified", max_length=30)
    vital_signs: VitalSignsInput


class HealthMetricResponse(BaseModel):
    metric_id: str
    profile_id: str
    user_id: str
    recorded_at: str
    vital_signs: dict
    warnings: list[str]


class HealthProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    name: str
    age: int
    gender: str
    created_at: str
    updated_at: str
    latest_metric: HealthMetricResponse | None = None
    metric_history: list[HealthMetricResponse] = Field(default_factory=list)


class DeviceBindRequest(BaseModel):
    user_id: str = Field(default="demo_user", min_length=1)
    device_name: str = Field(default="Insta360 X4", min_length=1, max_length=80)
    device_model: str = Field(default="Insta360 X4", min_length=1, max_length=80)
    connection_type: str = Field(default="wifi", pattern="^(wifi|bluetooth|usb|mock)$")
    auto_capture_enabled: bool = True
    capture_interval_minutes: int = Field(default=10, ge=5, le=30)
    capture_window: str = Field(default="08:00-22:00", max_length=30)


class DeviceSettingsRequest(BaseModel):
    auto_capture_enabled: bool | None = None
    capture_interval_minutes: int | None = Field(default=None, ge=5, le=30)
    capture_window: str | None = Field(default=None, max_length=30)


class DeviceResponse(BaseModel):
    device_id: str
    user_id: str
    device_name: str
    device_model: str
    provider: str
    connection_type: str
    status: str
    battery_percent: int
    storage_free_gb: float
    auto_capture_enabled: bool
    capture_interval_minutes: int
    capture_window: str
    last_seen_at: str
    created_at: str
    updated_at: str


class CaptureCreateRequest(BaseModel):
    user_id: str = Field(default="demo_user", min_length=1)
    device_id: str | None = None
    capture_mode: str = Field(default="manual", pattern="^(manual|auto|offline_cache)$")
    scene_hint: str | None = Field(default=None, max_length=80)
    image_url: str | None = Field(default=None, max_length=300)
    captured_at: str | None = None


class BehaviorRecordResponse(BaseModel):
    behavior_id: str
    capture_id: str
    user_id: str
    category: str
    label: str
    confidence: float
    body_score: int
    mental_score: int
    impact: str
    risk_flags: list[str]
    recommendations: list[str]
    created_at: str


class CaptureResponse(BaseModel):
    capture_id: str
    user_id: str
    device_id: str | None = None
    capture_mode: str
    scene_hint: str | None = None
    image_url: str | None = None
    status: str
    special_tag: str | None = None
    captured_at: str
    synced_at: str
    analysis: BehaviorRecordResponse | None = None


class DailyLogResponse(BaseModel):
    daily_log_id: str
    user_id: str
    date: str
    overall_score: int
    body_score: int
    mental_score: int
    behavior_summary: dict
    abnormal_behaviors: list[str]
    risk_tips: list[str]
    generated_at: str


class WeeklyReportResponse(BaseModel):
    report_id: str
    user_id: str
    week_start: str
    week_end: str
    average_overall_score: int
    average_body_score: int
    average_mental_score: int
    trend: list[dict]
    behavior_analysis: dict
    body_assessment: str
    mental_assessment: str
    suggestions: dict[str, list[str]]
    next_week_goals: list[str]
    comparison: str
    generated_at: str


class HealthDashboardResponse(BaseModel):
    profile: HealthProfileResponse | None
    device: DeviceResponse | None
    today_log: DailyLogResponse | None
    weekly_report: WeeklyReportResponse | None
    recent_captures: list[CaptureResponse]
    recent_behaviors: list[BehaviorRecordResponse]
    metric_trend: list[HealthMetricResponse]
    status: dict


class DemoFlowResponse(BaseModel):
    profile: HealthProfileResponse
    device: DeviceResponse
    captures: list[CaptureResponse]
    today_log: DailyLogResponse
    weekly_report: WeeklyReportResponse
