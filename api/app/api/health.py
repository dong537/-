from fastapi import APIRouter, HTTPException

from app.domain.health_service import (
    DEFAULT_USER_ID,
    bind_device,
    create_capture,
    generate_daily_log,
    generate_weekly_report,
    get_dashboard,
    run_demo_flow,
    update_device,
    upsert_health_profile,
)
from app.domain.store import store
from app.schemas.health import (
    CaptureCreateRequest,
    CaptureResponse,
    DailyLogResponse,
    DemoFlowResponse,
    DeviceBindRequest,
    DeviceResponse,
    DeviceSettingsRequest,
    HealthDashboardResponse,
    HealthProfileRequest,
    HealthProfileResponse,
    WeeklyReportResponse,
)

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/dashboard", response_model=HealthDashboardResponse)
def dashboard(user_id: str = DEFAULT_USER_ID) -> dict:
    return get_dashboard(user_id)


@router.post("/profiles", response_model=HealthProfileResponse)
def save_profile(payload: HealthProfileRequest) -> dict:
    return upsert_health_profile(payload.model_dump())


@router.get("/profiles/{user_id}", response_model=HealthProfileResponse)
def get_profile(user_id: str) -> dict:
    profiles = [profile for profile in store.health_profiles.values() if profile["user_id"] == user_id]
    if not profiles:
        raise HTTPException(status_code=404, detail="Health profile not found")
    dashboard_data = get_dashboard(user_id)
    if not dashboard_data["profile"]:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return dashboard_data["profile"]


@router.post("/devices/bind", response_model=DeviceResponse)
def bind_camera(payload: DeviceBindRequest) -> dict:
    return bind_device(payload.model_dump())


@router.patch("/devices/{device_id}", response_model=DeviceResponse)
def update_camera(device_id: str, payload: DeviceSettingsRequest) -> dict:
    device = update_device(device_id, payload.model_dump())
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/captures", response_model=CaptureResponse)
def create_capture_endpoint(payload: CaptureCreateRequest) -> dict:
    device_id = payload.device_id
    if device_id and device_id not in store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    return create_capture(payload.model_dump())


@router.post("/daily/{user_id}", response_model=DailyLogResponse)
def generate_daily(user_id: str, date: str | None = None) -> dict:
    return generate_daily_log(user_id, date)


@router.post("/weekly/{user_id}", response_model=WeeklyReportResponse)
def generate_weekly(user_id: str, date: str | None = None) -> dict:
    return generate_weekly_report(user_id, date)


@router.post("/demo", response_model=DemoFlowResponse)
def demo_flow(user_id: str = DEFAULT_USER_ID) -> dict:
    return run_demo_flow(user_id)
