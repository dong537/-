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
