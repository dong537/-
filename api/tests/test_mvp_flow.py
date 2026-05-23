from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.domain import store as store_module
from app.domain.store import reset_store
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    reset_store(clear_files=True)


def test_health_and_config() -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers["x-request-id"]

    ready = client.get("/ready")
    assert ready.status_code in {200, 503}
    checks = ready.json()["checks"]
    assert "data_dir_writable" in checks
    assert "state_file_writable" in checks
    assert "store_persistence_ok" in checks

    config = client.get("/api/dev/config")
    assert config.status_code == 200
    body = config.json()
    assert body["ai_mode"] == "mock"
    assert body["map_mode"] == "mock"
    assert body["max_upload_bytes"] > 0
    assert body["request_log_enabled"] is True
    assert body["store_persistence_enabled"] is True


def test_full_demo_flow() -> None:
    trip = client.post(
        "/api/trips",
        json={
            "destination": "Hangzhou West Lake",
            "duration_minutes": 120,
            "preferences": ["scenery", "video", "easy"],
            "use_panorama_camera": True,
        },
    )
    assert trip.status_code == 200
    trip_id = trip.json()["trip_id"]

    route = client.post(f"/api/trips/{trip_id}/route")
    assert route.status_code == 200
    route_body = route.json()
    assert len(route_body["nodes"]) == 5

    reroute = client.post(
        f"/api/trips/{trip_id}/reroute",
        json={"status_action": "tired", "remaining_minutes": 80},
    )
    assert reroute.status_code == 200
    assert reroute.json()["change_summary"]

    media = client.post(f"/api/trips/{trip_id}/media/demo")
    assert media.status_code == 200
    media_id = media.json()["media_id"]

    frames = client.post(f"/api/media/{media_id}/extract-frames")
    assert frames.status_code == 200
    frame_body = frames.json()
    assert len(frame_body["frames"]) >= 3
    marked_frame_id = frame_body["frames"][-1]["frame_id"]

    mark = client.post(f"/api/frames/{marked_frame_id}/mark", json={"marked": True, "reason": "favorite moment"})
    assert mark.status_code == 200
    assert mark.json()["marked"] is True

    companion = client.post(
        f"/api/trips/{trip_id}/companion/analyze",
        json={
            "frame_id": frame_body["frames"][0]["frame_id"],
            "route_node_id": route_body["nodes"][0]["id"],
            "user_status": "normal",
        },
    )
    assert companion.status_code == 200
    assert companion.json()["message"]

    export = client.post(f"/api/trips/{trip_id}/exports")
    assert export.status_code == 200
    export_body = export.json()
    assert len(export_body["selected_frames"]) >= 3
    assert export_body["social_copy"]
    assert any(frame["frame_id"] == marked_frame_id for frame in export_body["selected_frames"])
    assert export_body["video_draft"][0]["shot_type"]
    assert export_body["video_draft"][0]["transition"]
    assert export_body["video_draft"][0]["edit_note"]
    assert len(export_body["story_events"]) >= 6
    assert export_body["story_events"][-1]["event_type"] == "export_generated"

    manifest = client.get(f"/api/exports/{export_body['export_id']}/manifest")
    assert manifest.status_code == 200
    manifest_body = manifest.json()
    assert manifest_body["schema"] == "panorama-companion.export-manifest.v1"
    assert manifest_body["trip"]["trip_id"] == trip_id
    assert len(manifest_body["selected_frames"]) >= 3
    assert any(frame["marked"] for frame in manifest_body["selected_frames"])
    assert len(manifest_body["video_draft"]) >= 3
    assert manifest_body["video_draft"][0]["route_node_name"]
    assert len(manifest_body["story_events"]) >= 6
    assert manifest.headers["content-disposition"].endswith("-manifest.json\"")

    bundle = client.get(f"/api/exports/{export_body['export_id']}/bundle")
    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(bundle.content)) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert len([name for name in names if name.startswith("selected_frames/")]) >= 3

    trips = client.get("/api/trips")
    assert trips.status_code == 200
    summary = trips.json()[0]
    assert summary["trip_id"] == trip_id
    assert summary["route_ready"] is True
    assert summary["media_count"] == 1
    assert summary["frame_count"] >= 3
    assert summary["export_count"] == 1
    assert summary["event_count"] >= 6


def test_reset_demo_state() -> None:
    trip = client.post(
        "/api/trips",
        json={
            "destination": "Hangzhou West Lake",
            "duration_minutes": 120,
            "preferences": ["scenery"],
            "use_panorama_camera": True,
        },
    )
    assert trip.status_code == 200

    before = client.get("/api/dev/config").json()
    assert before["counts"]["trips"] == 1

    reset = client.post("/api/dev/reset?clear_files=false")
    assert reset.status_code == 200
    assert reset.json()["status"] == "reset"

    after = client.get("/api/dev/config").json()
    assert after["counts"]["trips"] == 0


def test_upload_size_limit(monkeypatch) -> None:
    monkeypatch.setattr("app.domain.media_service.settings.max_upload_bytes", 4)
    trip = client.post(
        "/api/trips",
        json={
            "destination": "Hangzhou West Lake",
            "duration_minutes": 120,
            "preferences": ["scenery"],
            "use_panorama_camera": True,
        },
    )
    assert trip.status_code == 200

    upload = client.post(
        f"/api/trips/{trip.json()['trip_id']}/media",
        files={"file": ("clip.mp4", b"too-large", "video/mp4")},
    )
    assert upload.status_code == 413


def test_store_persistence_round_trip(tmp_path, monkeypatch) -> None:
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(store_module.settings, "state_file", state_file)
    monkeypatch.setattr(store_module.settings, "store_persistence_enabled", True)

    reset_store(clear_files=False)
    trip = client.post(
        "/api/trips",
        json={
            "destination": "Hangzhou West Lake",
            "duration_minutes": 120,
            "preferences": ["scenery"],
            "use_panorama_camera": True,
        },
    )
    assert trip.status_code == 200
    trip_id = trip.json()["trip_id"]
    assert state_file.exists()

    for name in store_module.STORE_COLLECTIONS:
        getattr(store_module.store, name).clear()
    assert trip_id not in store_module.store.trips

    assert store_module.load_store() is True
    assert trip_id in store_module.store.trips
    assert any(event["trip_id"] == trip_id for event in store_module.store.events.values())
