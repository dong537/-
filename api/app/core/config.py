import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


class Settings:
    app_name = "Panorama Companion API"
    app_env = os.getenv("APP_ENV", "development")
    app_base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8010")
    web_origin = os.getenv("WEB_ORIGIN", "http://127.0.0.1:5173")
    data_dir = Path(os.getenv("DATA_DIR", "./data")).resolve()
    frame_interval_seconds = int(os.getenv("FRAME_EXTRACT_INTERVAL_SECONDS", "4"))
    max_frame_analysis_count = int(os.getenv("MAX_FRAME_ANALYSIS_COUNT", "12"))
    ai_provider = os.getenv("AI_PROVIDER", "mock")
    map_provider = os.getenv("MAP_PROVIDER", "mock")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_text_model = os.getenv("OPENAI_TEXT_MODEL", "")
    openai_vision_model = os.getenv("OPENAI_VISION_MODEL", "")
    amap_web_key = os.getenv("AMAP_WEB_KEY", "")
    amap_web_service_key = os.getenv("AMAP_WEB_SERVICE_KEY", "")

    @property
    def ai_mode(self) -> str:
        if self.ai_provider == "mock":
            return "mock"
        return "provider" if self.openai_api_key else "mock_missing_key"

    @property
    def map_mode(self) -> str:
        if self.map_provider == "mock":
            return "mock"
        return "provider" if self.amap_web_key or self.amap_web_service_key else "mock_missing_key"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def frames_dir(self) -> Path:
        return self.data_dir / "frames"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"


settings = Settings()

for directory in (settings.uploads_dir, settings.frames_dir, settings.exports_dir):
    directory.mkdir(parents=True, exist_ok=True)
