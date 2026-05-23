import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.domain.health_service import (
    DEFAULT_USER_ID,
    bind_device,
    create_capture,
    delete_user_data,
    generate_daily_log,
    generate_weekly_report,
    get_dashboard,
    get_trends,
    get_weekly_report,
    list_daily_logs,
    list_weekly_reports,
    review_capture,
    run_demo_flow,
    sync_offline_captures,
    update_device,
    upsert_health_profile,
)
from app.domain.insta360_sdk_bridge import get_command_plan, get_sdk_status
from app.domain.store import store
from app.schemas.health import (
    CaptureCreateRequest,
    CaptureResponse,
    CaptureReviewRequest,
    DailyLogResponse,
    DeleteUserDataResponse,
    DemoFlowResponse,
    DeviceBindRequest,
    DeviceResponse,
    DeviceSettingsRequest,
    HealthDashboardResponse,
    HealthProfileRequest,
    HealthProfileResponse,
    Insta360CommandPlanResponse,
    Insta360SdkStatusResponse,
    OfflineSyncResponse,
    TrendResponse,
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


@router.post("/devices/{device_id}/sync", response_model=OfflineSyncResponse)
def sync_camera_cache(device_id: str) -> dict:
    result = sync_offline_captures(device_id)
    if not result:
        raise HTTPException(status_code=404, detail="Device not found")
    return result


@router.get("/insta360/sdk/status", response_model=Insta360SdkStatusResponse)
def insta360_sdk_status() -> dict:
    return get_sdk_status()


@router.get("/insta360/sdk/command-plan", response_model=Insta360CommandPlanResponse)
def insta360_sdk_command_plan(operation: str = "capture") -> dict:
    plan = get_command_plan(operation)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Unsupported Insta360 SDK operation: {operation}")
    return plan


@router.post("/captures", response_model=CaptureResponse)
def create_capture_endpoint(payload: CaptureCreateRequest) -> dict:
    device_id = payload.device_id
    if device_id and device_id not in store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    return create_capture(payload.model_dump())


@router.post("/captures/{capture_id}/review", response_model=CaptureResponse)
def review_capture_endpoint(capture_id: str, payload: CaptureReviewRequest) -> dict:
    capture = review_capture(capture_id, payload.model_dump())
    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")
    return capture


@router.post("/daily/{user_id}", response_model=DailyLogResponse)
def generate_daily(user_id: str, date: str | None = None) -> dict:
    return generate_daily_log(user_id, date)


@router.get("/daily/{user_id}", response_model=list[DailyLogResponse])
def daily_history(user_id: str, limit: int = 30) -> list[dict]:
    return list_daily_logs(user_id, max(1, min(limit, 90)))


@router.get("/trends/{user_id}", response_model=TrendResponse)
def trends(user_id: str, range_days: int = 30) -> dict:
    return get_trends(user_id, range_days)


@router.post("/weekly/{user_id}", response_model=WeeklyReportResponse)
def generate_weekly(user_id: str, date: str | None = None) -> dict:
    return generate_weekly_report(user_id, date)


@router.get("/weekly/{user_id}", response_model=list[WeeklyReportResponse])
def weekly_history(user_id: str, limit: int = 12) -> list[dict]:
    return list_weekly_reports(user_id, max(1, min(limit, 52)))


@router.get("/weekly/reports/{report_id}/pdf")
def export_weekly_pdf(report_id: str) -> Response:
    report = get_weekly_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    # Minimal PDF-like handoff for MVP demos. Replace with a renderer such as WeasyPrint in production.
    content = f"%PDF-1.4\n% Health weekly report\n{payload}\n%%EOF\n".encode()
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report_id}.pdf"'},
    )


@router.post("/demo", response_model=DemoFlowResponse)
def demo_flow(user_id: str = DEFAULT_USER_ID) -> dict:
    return run_demo_flow(user_id)


@router.delete("/users/{user_id}", response_model=DeleteUserDataResponse)
def delete_user(user_id: str, scope: str = "all") -> dict:
    return delete_user_data(user_id, scope)
