from fastapi.testclient import TestClient

from app.domain.store import reset_store
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_store(clear_files=True)


def test_health_monitoring_prd_flow() -> None:
    profile = client.post(
        "/api/health/profiles",
        json={
            "user_id": "demo_user",
            "name": "Alex",
            "age": 32,
            "gender": "unspecified",
            "vital_signs": {
                "height_cm": 172,
                "weight_kg": 78,
                "systolic_bp": 142,
                "diastolic_bp": 92,
                "heart_rate": 88,
                "blood_oxygen": 98,
                "blood_glucose": 7.4,
                "blood_lipid": 5.8,
                "uric_acid": 410,
            },
        },
    )
    assert profile.status_code == 200
    profile_body = profile.json()
    assert profile_body["latest_metric"]["vital_signs"]["bmi"] > 0
    assert profile_body["latest_metric"]["warnings"]

    device = client.post(
        "/api/health/devices/bind",
        json={
            "user_id": "demo_user",
            "device_name": "Insta360 X4",
            "device_model": "Insta360 X4",
            "connection_type": "mock",
            "auto_capture_enabled": True,
            "capture_interval_minutes": 10,
            "capture_window": "08:00-22:00",
        },
    )
    assert device.status_code == 200
    device_body = device.json()
    assert device_body["status"] == "online"

    capture = client.post(
        "/api/health/captures",
        json={
            "user_id": "demo_user",
            "device_id": device_body["device_id"],
            "capture_mode": "manual",
            "scene_hint": "late snack",
        },
    )
    assert capture.status_code == 200
    capture_body = capture.json()
    assert capture_body["status"] == "analyzed"
    assert capture_body["analysis"]["category"] == "diet"
    assert "high_sugar" in capture_body["analysis"]["risk_flags"]
    assert capture_body["analysis"]["body_score"] < 70

    daily = client.post("/api/health/daily/demo_user")
    assert daily.status_code == 200
    daily_body = daily.json()
    assert daily_body["overall_score"] > 0
    assert "高糖饮食" in daily_body["abnormal_behaviors"]

    weekly = client.post("/api/health/weekly/demo_user")
    assert weekly.status_code == 200
    weekly_body = weekly.json()
    assert weekly_body["average_body_score"] > 0
    assert weekly_body["suggestions"]["diet"]
    assert weekly_body["next_week_goals"]

    dashboard = client.get("/api/health/dashboard")
    assert dashboard.status_code == 200
    dashboard_body = dashboard.json()
    assert dashboard_body["status"]["profile_ready"] is True
    assert dashboard_body["status"]["device_ready"] is True
    assert dashboard_body["status"]["capture_count"] == 1
    assert dashboard_body["weekly_report"]["report_id"] == weekly_body["report_id"]


def test_health_demo_flow() -> None:
    demo = client.post("/api/health/demo")
    assert demo.status_code == 200
    body = demo.json()
    assert body["profile"]["profile_id"]
    assert body["device"]["device_model"].startswith("Insta360")
    assert len(body["captures"]) == 6
    assert body["today_log"]["behavior_summary"]["total_records"] == 6
    assert body["weekly_report"]["average_overall_score"] > 0


def test_device_offline_cache_history_and_weekly_pdf() -> None:
    demo = client.post("/api/health/demo")
    assert demo.status_code == 200
    device_id = demo.json()["device"]["device_id"]

    offline = client.patch(
        f"/api/health/devices/{device_id}",
        json={"status": "offline", "battery_percent": 12, "status_detail": "network lost"},
    )
    assert offline.status_code == 200
    assert offline.json()["status"] == "offline"

    cached = client.post(
        "/api/health/captures",
        json={
            "user_id": "demo_user",
            "device_id": device_id,
            "capture_mode": "auto",
            "scene_hint": "sitting",
        },
    )
    assert cached.status_code == 200
    cached_body = cached.json()
    assert cached_body["status"] == "cached"
    assert cached_body["analysis"] is None

    synced = client.post(f"/api/health/devices/{device_id}/sync")
    assert synced.status_code == 200
    synced_body = synced.json()
    assert synced_body["device"]["status"] == "online"
    assert synced_body["device"]["offline_cache_count"] == 0
    assert len(synced_body["synced_captures"]) == 1
    assert synced_body["synced_captures"][0]["status"] == "analyzed"

    daily_history = client.get("/api/health/daily/demo_user")
    assert daily_history.status_code == 200
    assert len(daily_history.json()) >= 1

    weekly_history = client.get("/api/health/weekly/demo_user")
    assert weekly_history.status_code == 200
    report_id = weekly_history.json()[0]["report_id"]

    pdf = client.get(f"/api/health/weekly/reports/{report_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
