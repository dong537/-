from __future__ import annotations

from app.core.config import settings


class MapProvider:
    name = "mock"

    def enrich_route_context(self, destination: str, preferences: list[str]) -> dict:
        return {
            "provider": self.name,
            "destination": destination,
            "preferences": preferences,
            "note": "Using built-in West Lake demo route.",
        }


class AmapProvider(MapProvider):
    name = "amap"

    def enrich_route_context(self, destination: str, preferences: list[str]) -> dict:
        # Real Web Service calls can be added here. MVP keeps deterministic fallback.
        return {
            "provider": self.name,
            "destination": destination,
            "preferences": preferences,
            "note": "AMap provider configured; MVP route still uses deterministic fallback.",
            "has_service_key": bool(settings.amap_web_service_key),
        }


class AIProvider:
    name = "mock"

    def companion_status_hint(self, user_status: str) -> str:
        return {
            "tired": "你现在有点累，可以把拍摄动作做得更轻，不需要追求太多角度。",
            "photo": "既然你想拍照，可以多留意前景和画面边缘。",
            "food": "可以顺路找个地方坐下，别让行程只剩赶路。",
            "short_time": "时间不多，先保留最有代表性的画面。",
            "quiet": "这段适合安静一点的观察，不用急着说太多。",
            "normal": "保持现在的节奏就很好。",
        }.get(user_status, "保持现在的节奏就很好。")

    def generate_social_copy(self, destination: str) -> str:
        return (
            f"今天的{destination}不是攻略里的打卡路线，而是一路慢慢走出来的湖风、树影和片刻停留。"
            "把相机交给全景视角，把节奏交给自己，原来两小时也可以很完整。"
        )


class OpenAIProvider(AIProvider):
    name = "openai"

    def companion_status_hint(self, user_status: str) -> str:
        # Real model calls can be added here. Keep mock-compatible behavior for stable demos.
        return super().companion_status_hint(user_status)


def get_map_provider() -> MapProvider:
    if settings.map_provider == "amap" and (settings.amap_web_key or settings.amap_web_service_key):
        return AmapProvider()
    return MapProvider()


def get_ai_provider() -> AIProvider:
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return OpenAIProvider()
    return AIProvider()
