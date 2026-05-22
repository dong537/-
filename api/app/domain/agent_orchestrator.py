from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.core.config import settings
from app.domain.media_service import extract_frames, select_best_frames
from app.domain.providers import get_ai_provider
from app.domain.store import get_trip_events, new_id, now_iso, record_event, store


def analyze_companion(trip_id: str, frame_id: str | None, route_node_id: str | None, user_status: str) -> dict:
    frames = [frame for frame in store.frames.values() if frame["trip_id"] == trip_id]
    if not frames:
        media_items = [media for media in store.media.values() if media["trip_id"] == trip_id]
        if media_items:
            _, frames = extract_frames(media_items[-1]["media_id"])

    frame = store.frames.get(frame_id) if frame_id else (frames[0] if frames else None)
    route = store.routes.get(trip_id)
    route_node = None
    if route:
        route_node = next((node for node in route["nodes"] if node["id"] == route_node_id), None) or route["nodes"][0]

    ai_provider = get_ai_provider()
    status_hint = ai_provider.companion_status_hint(user_status)

    node_name = route_node["name"] if route_node else "当前地点"
    caption = frame["ai_caption"] if frame else "当前画面适合做一次轻量讲解。"
    message = f"{node_name}这一段可以慢一点。{caption}{status_hint}"
    record_event(
        trip_id,
        "companion_generated",
        "AI 生成伴游讲解",
        message,
        {"frame_id": frame["frame_id"] if frame else None, "route_node_id": route_node["id"] if route_node else None},
    )
    return {
        "message": message,
        "shooting_tips": ["相机略微抬高", "保持慢速移动", "让天空和地面各留出一点空间"],
        "scene_tags": ["City Walk", "湖边", "全景素材"],
        "safety_tips": [] if user_status != "short_time" else ["不要为了赶时间边走边盯屏幕。"],
        "share_value": 8,
        "frame": frame,
    }


def _build_video_draft(selected_frames: list[dict], route: dict | None) -> list[dict]:
    route_nodes = route["nodes"] if route else []
    shot_types = ["开场环境", "行走过渡", "细节观察", "休息节奏", "收尾封面"]
    transitions = ["淡入开场", "慢速推进", "交叉溶解", "节奏放缓", "淡出收尾"]
    durations = [5, 6, 6, 6, 7]

    draft = []
    for index, frame in enumerate(selected_frames[:5]):
        node = route_nodes[min(index, len(route_nodes) - 1)] if route_nodes else None
        marked_note = "用户手动标记过，建议保留在主时间线。" if frame.get("marked") else "可作为路线叙事中的稳定镜头。"
        node_note = f"关联路线节点：{node['name']}。" if node else "关联当前旅行素材。"
        draft.append(
            {
                "order": index + 1,
                "frame_id": frame["frame_id"],
                "duration_seconds": durations[index % len(durations)],
                "caption": frame["ai_caption"],
                "shot_type": shot_types[index % len(shot_types)],
                "route_node_name": node["name"] if node else None,
                "transition": transitions[index % len(transitions)],
                "edit_note": f"{node_note}{marked_note}",
            }
        )
    return draft


def generate_export(trip_id: str) -> dict:
    media_items = [media for media in store.media.values() if media["trip_id"] == trip_id]
    if media_items and not [frame for frame in store.frames.values() if frame["trip_id"] == trip_id]:
        extract_frames(media_items[-1]["media_id"])

    selected = select_best_frames(trip_id, limit=5)
    route = store.routes.get(trip_id)
    trip = store.trips[trip_id]
    route_names = " -> ".join(node["name"] for node in route["nodes"]) if route else trip["destination"]
    social_copy = get_ai_provider().generate_social_copy(trip["destination"])
    video_draft = _build_video_draft(selected, route)
    export_id = new_id("export")
    export = {
        "export_id": export_id,
        "trip_id": trip_id,
        "status": "succeeded",
        "selected_frames": selected,
        "route_recap": f"今日路线：{route_names}",
        "social_copy": social_copy,
        "video_draft": video_draft,
        "story_events": get_trip_events(trip_id),
        "created_at": now_iso(),
    }
    store.exports[export_id] = export
    record_event(
        trip_id,
        "export_generated",
        "自动出片结果已生成",
        f"精选 {len(selected)} 张图片，并生成路线回顾、发布文案和视频草稿。",
        {"export_id": export_id, "selected_frame_ids": [frame["frame_id"] for frame in selected]},
    )
    export["story_events"] = get_trip_events(trip_id)
    return export


def build_export_manifest(export_id: str) -> dict:
    export = store.exports[export_id]
    trip = store.trips[export["trip_id"]]
    route = store.routes.get(export["trip_id"])
    media_items = [media for media in store.media.values() if media["trip_id"] == export["trip_id"]]
    return {
        "schema": "panorama-companion.export-manifest.v1",
        "generated_at": now_iso(),
        "trip": {
            "trip_id": trip["id"],
            "destination": trip["destination"],
            "duration_minutes": trip["duration_minutes"],
            "preferences": trip["preferences"],
        },
        "route": {
            "route_id": route["route_id"] if route else None,
            "route_name": route["route_name"] if route else None,
            "nodes": route["nodes"] if route else [],
        },
        "media_assets": [
            {
                "media_id": media["media_id"],
                "kind": media["kind"],
                "filename": media["filename"],
                "url": media.get("url"),
            }
            for media in media_items
        ],
        "selected_frames": [
            {
                "frame_id": frame["frame_id"],
                "timestamp_ms": frame["timestamp_ms"],
                "image_url": frame["image_url"],
                "caption": frame.get("ai_caption"),
                "score": frame.get("ai_score"),
                "selected_reason": frame.get("selected_reason"),
                "marked": frame.get("marked", False),
                "marked_reason": frame.get("marked_reason"),
            }
            for frame in export["selected_frames"]
        ],
        "video_draft": export["video_draft"],
        "story_events": get_trip_events(export["trip_id"]),
        "copy": {
            "route_recap": export["route_recap"],
            "social_copy": export["social_copy"],
        },
        "handoff": {
            "suggested_workflow": "Import selected frame URLs and video draft timeline into Insta360 Studio or another editor.",
            "status": "MVP manifest, not a rendered final video.",
        },
    }


def build_export_bundle(export_id: str) -> Path:
    export = store.exports[export_id]
    manifest = build_export_manifest(export_id)
    export_dir = settings.exports_dir / export_id
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"{export_id}-bundle.zip"

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for index, frame in enumerate(export["selected_frames"], start=1):
            frame_path = Path(frame.get("path") or "")
            if not frame_path.is_file():
                continue
            suffix = frame_path.suffix or ".jpg"
            bundle.write(frame_path, f"selected_frames/{index:02d}-{frame['frame_id']}{suffix}")

    record_event(
        export["trip_id"],
        "export_bundle_created",
        "素材包已导出",
        "已生成包含 manifest 和精选帧的 ZIP 素材包。",
        {"export_id": export_id, "bundle_path": str(zip_path)},
    )
    return zip_path
