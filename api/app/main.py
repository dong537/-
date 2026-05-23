import logging
import shutil
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.companion import router as companion_router
from app.api.dev import router as dev_router
from app.api.exports import router as exports_router
from app.api.health import router as health_router
from app.api.media import router as media_router
from app.api.trips import router as trips_router
from app.core.config import settings
from app.domain.store import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("panorama-companion")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory=settings.data_dir), name="files")

app.include_router(trips_router)
app.include_router(media_router)
app.include_router(companion_router)
app.include_router(exports_router)
app.include_router(health_router)
app.include_router(dev_router)


@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    request_id = uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    if settings.request_log_enabled:
        logger.info(
            "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
    return response


def _directory_writable() -> bool:
    probe = settings.data_dir / ".write-check"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _state_file_writable() -> bool:
    if not settings.store_persistence_enabled:
        return True
    probe = settings.state_file.with_name(f"{settings.state_file.name}.write-check")
    try:
        settings.state_file.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "ai_provider": settings.ai_provider,
        "ai_mode": settings.ai_mode,
        "map_provider": settings.map_provider,
        "map_mode": settings.map_mode,
    }


@app.get("/ready")
def ready() -> JSONResponse:
    checks = {
        "data_dir_writable": _directory_writable(),
        "uploads_dir_exists": settings.uploads_dir.exists(),
        "frames_dir_exists": settings.frames_dir.exists(),
        "exports_dir_exists": settings.exports_dir.exists(),
        "state_file_writable": _state_file_writable(),
        "store_persistence_ok": store.persistence_error is None,
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
    }
    status = "ready" if all(checks.values()) else "degraded"
    return JSONResponse(
        status_code=200 if status == "ready" else 503,
        content={
            "status": status,
            "checks": checks,
        },
    )
