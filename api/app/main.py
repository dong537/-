from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.companion import router as companion_router
from app.api.dev import router as dev_router
from app.api.exports import router as exports_router
from app.api.media import router as media_router
from app.api.trips import router as trips_router
from app.core.config import settings

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
app.include_router(dev_router)


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
