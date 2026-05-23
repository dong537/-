from fastapi import APIRouter

from app.core.config import settings
from app.domain.store import reset_store, store

router = APIRouter(prefix="/api/dev", tags=["dev"])


@router.get("/config")
def get_runtime_config() -> dict:
    return {
        "app_env": settings.app_env,
        "ai_provider": settings.ai_provider,
        "ai_mode": settings.ai_mode,
        "map_provider": settings.map_provider,
        "map_mode": settings.map_mode,
        "app_base_url": settings.app_base_url,
        "frame_extract_interval_seconds": settings.frame_interval_seconds,
        "max_frame_analysis_count": settings.max_frame_analysis_count,
        "max_upload_bytes": settings.max_upload_bytes,
        "request_log_enabled": settings.request_log_enabled,
        "store_persistence_enabled": settings.store_persistence_enabled,
        "state_file": str(settings.state_file),
        "store_loaded_at": store.loaded_at,
        "store_saved_at": store.saved_at,
        "store_persistence_error": store.persistence_error,
        "text_model": settings.openai_text_model or "mock",
        "vision_model": settings.openai_vision_model or "mock",
        "insta360_sdk_demo_path": settings.insta360_sdk_demo_path,
        "insta360_native_bridge_enabled": settings.insta360_native_bridge_enabled,
        "counts": {
            "trips": len(store.trips),
            "media": len(store.media),
            "frames": len(store.frames),
            "exports": len(store.exports),
            "events": len(store.events),
            "health_profiles": len(store.health_profiles),
            "health_metrics": len(store.health_metrics),
            "devices": len(store.devices),
            "captures": len(store.captures),
            "behavior_records": len(store.behavior_records),
            "daily_logs": len(store.daily_logs),
            "weekly_reports": len(store.weekly_reports),
        },
    }


@router.post("/reset")
def reset_demo(clear_files: bool = True) -> dict[str, str]:
    reset_store(clear_files=clear_files)
    return {"status": "reset"}
