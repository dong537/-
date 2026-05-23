from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.config import settings


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


STORE_SCHEMA = "panorama-companion.memory-store.v2"
STORE_COLLECTIONS = (
    "trips",
    "routes",
    "media",
    "frames",
    "jobs",
    "exports",
    "events",
    "health_profiles",
    "health_metrics",
    "devices",
    "captures",
    "behavior_records",
    "daily_logs",
    "weekly_reports",
)


@dataclass
class MemoryStore:
    trips: dict[str, dict[str, Any]] = field(default_factory=dict)
    routes: dict[str, dict[str, Any]] = field(default_factory=dict)
    media: dict[str, dict[str, Any]] = field(default_factory=dict)
    frames: dict[str, dict[str, Any]] = field(default_factory=dict)
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    exports: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: dict[str, dict[str, Any]] = field(default_factory=dict)
    health_profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    health_metrics: dict[str, dict[str, Any]] = field(default_factory=dict)
    devices: dict[str, dict[str, Any]] = field(default_factory=dict)
    captures: dict[str, dict[str, Any]] = field(default_factory=dict)
    behavior_records: dict[str, dict[str, Any]] = field(default_factory=dict)
    daily_logs: dict[str, dict[str, Any]] = field(default_factory=dict)
    weekly_reports: dict[str, dict[str, Any]] = field(default_factory=dict)
    loaded_at: str | None = None
    saved_at: str | None = None
    persistence_error: str | None = None


store = MemoryStore()


def _collection_snapshot() -> dict[str, dict[str, dict[str, Any]]]:
    return {name: getattr(store, name) for name in STORE_COLLECTIONS}


def persist_store() -> bool:
    if not settings.store_persistence_enabled:
        return False

    saved_at = now_iso()
    payload = {
        "schema": STORE_SCHEMA,
        "saved_at": saved_at,
        "collections": _collection_snapshot(),
    }
    try:
        settings.state_file.parent.mkdir(parents=True, exist_ok=True)
        temp_path = settings.state_file.with_name(f"{settings.state_file.name}.tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(settings.state_file)
    except (OSError, TypeError, ValueError) as exc:
        store.persistence_error = str(exc)
        return False

    store.saved_at = saved_at
    store.persistence_error = None
    return True


def load_store() -> bool:
    if not settings.store_persistence_enabled or not settings.state_file.exists():
        return False

    try:
        payload = json.loads(settings.state_file.read_text(encoding="utf-8"))
        collections = payload.get("collections", {})
        for name in STORE_COLLECTIONS:
            target = getattr(store, name)
            target.clear()
            target.update(collections.get(name, {}))
    except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
        store.persistence_error = str(exc)
        return False

    store.loaded_at = now_iso()
    store.saved_at = payload.get("saved_at")
    store.persistence_error = None
    return True


def reset_store(clear_files: bool = False) -> None:
    store.trips.clear()
    store.routes.clear()
    store.media.clear()
    store.frames.clear()
    store.jobs.clear()
    store.exports.clear()
    store.events.clear()
    store.health_profiles.clear()
    store.health_metrics.clear()
    store.devices.clear()
    store.captures.clear()
    store.behavior_records.clear()
    store.daily_logs.clear()
    store.weekly_reports.clear()

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
    persist_store()


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
    persist_store()
    return event


def get_trip_events(trip_id: str) -> list[dict[str, Any]]:
    events = [event for event in store.events.values() if event["trip_id"] == trip_id]
    return sorted(events, key=lambda event: event["created_at"])


load_store()
