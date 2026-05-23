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
        "text_model": settings.openai_text_model or "mock",
        "vision_model": settings.openai_vision_model or "mock",
        "counts": {
            "trips": len(store.trips),
            "media": len(store.media),
            "frames": len(store.frames),
            "exports": len(store.exports),
            "events": len(store.events),
        },
    }


@router.post("/reset")
def reset_demo(clear_files: bool = True) -> dict[str, str]:
    reset_store(clear_files=clear_files)
    return {"status": "reset"}
