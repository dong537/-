from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import shutil
from typing import Any
from uuid import uuid4

from app.core.config import settings


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryStore:
    trips: dict[str, dict[str, Any]] = field(default_factory=dict)
    routes: dict[str, dict[str, Any]] = field(default_factory=dict)
    media: dict[str, dict[str, Any]] = field(default_factory=dict)
    frames: dict[str, dict[str, Any]] = field(default_factory=dict)
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    exports: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: dict[str, dict[str, Any]] = field(default_factory=dict)


store = MemoryStore()


def reset_store(clear_files: bool = False) -> None:
    store.trips.clear()
    store.routes.clear()
    store.media.clear()
    store.frames.clear()
    store.jobs.clear()
    store.exports.clear()
    store.events.clear()

    if clear_files:
        for directory in (settings.uploads_dir, settings.frames_dir, settings.exports_dir):
            if directory.exists():
                for item in directory.iterdir():
                    if item.name == ".gitkeep":
                        continue
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()


def record_event(trip_id: str, event_type: str, title: str, detail: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    event_id = new_id("event")
    event = {
        "event_id": event_id,
        "trip_id": trip_id,
        "event_type": event_type,
        "title": title,
        "detail": detail,
        "payload": payload or {},
        "created_at": now_iso(),
    }
    store.events[event_id] = event
    return event


def get_trip_events(trip_id: str) -> list[dict[str, Any]]:
    events = [event for event in store.events.values() if event["trip_id"] == trip_id]
    return sorted(events, key=lambda event: event["created_at"])
