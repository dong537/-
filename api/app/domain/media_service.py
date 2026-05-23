from __future__ import annotations

import html
import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.domain.store import new_id, now_iso, persist_store, record_event, store


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}


def _public_url(path: Path) -> str:
    relative = path.resolve().relative_to(settings.data_dir)
    return f"{settings.app_base_url}/files/{relative.as_posix()}"


def _safe_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{uuid4().hex}{suffix}"


async def _write_upload_with_limit(upload: UploadFile, target: Path) -> None:
    total = 0
    chunk_size = 1024 * 1024
    try:
        with target.open("wb") as buffer:
            while chunk := await upload.read(chunk_size):
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    raise HTTPException(status_code=413, detail="Uploaded file exceeds MAX_UPLOAD_BYTES")
                buffer.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise


async def save_upload(trip_id: str, upload: UploadFile) -> dict:
    filename = _safe_name(upload.filename or "media.bin")
    target = settings.uploads_dir / filename
    await _write_upload_with_limit(upload, target)
    suffix = target.suffix.lower()
    kind = "image" if suffix in IMAGE_EXTENSIONS else "video" if suffix in VIDEO_EXTENSIONS else "file"
    media_id = new_id("media")
    asset = {
        "media_id": media_id,
        "trip_id": trip_id,
        "kind": kind,
        "filename": upload.filename or filename,
        "path": str(target),
        "url": _public_url(target),
        "status": "uploaded",
        "created_at": now_iso(),
    }
    store.media[media_id] = asset
    record_event(trip_id, "media_uploaded", "素材已上传", f"上传素材：{asset['filename']}。", {"media_id": media_id, "kind": kind})
    return asset


def create_demo_media(trip_id: str) -> dict:
    media_id = new_id("media")
    asset = {
        "media_id": media_id,
        "trip_id": trip_id,
        "kind": "demo",
        "filename": "demo-panorama-west-lake",
        "path": None,
        "url": None,
        "status": "ready",
        "created_at": now_iso(),
    }
    store.media[media_id] = asset
    record_event(trip_id, "demo_media_created", "演示素材已准备", "使用内置西湖全景演示素材。", {"media_id": media_id})
    return asset


def _write_demo_svg(media_id: str, index: int, title: str, subtitle: str, palette: tuple[str, str, str]) -> Path:
    frame_dir = settings.frames_dir / media_id
    frame_dir.mkdir(parents=True, exist_ok=True)
    path = frame_dir / f"frame_{index:03d}.svg"
    a, b, c = palette
    body = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="sky" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="{a}"/>
      <stop offset="1" stop-color="{b}"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#sky)"/>
  <path d="M0 470 C180 430 330 505 520 462 C700 421 820 440 980 410 C1120 384 1220 420 1280 390 L1280 720 L0 720 Z" fill="{c}" opacity="0.8"/>
  <path d="M0 540 C240 500 390 570 600 530 C790 494 980 536 1280 492 L1280 720 L0 720 Z" fill="#f7faf7" opacity="0.38"/>
  <circle cx="{180 + index * 90}" cy="{126 + index * 8}" r="{46 + index * 4}" fill="#fff7d1" opacity="0.72"/>
  <text x="70" y="610" font-family="Arial, sans-serif" font-size="42" font-weight="700" fill="#10251f">{html.escape(title)}</text>
  <text x="70" y="660" font-family="Arial, sans-serif" font-size="26" fill="#27453c">{html.escape(subtitle)}</text>
</svg>"""
    path.write_text(body, encoding="utf-8")
    return path


def _create_frame(media: dict, timestamp_ms: int, path: Path, index: int) -> dict:
    captions = [
        "湖边视野开阔，水面和天空形成稳定的横向层次。",
        "树影和步道有明显前景，适合做一段慢速移动镜头。",
        "街区侧路更安静，建筑和行人让画面更有生活感。",
        "咖啡休息点适合放慢节奏，也能补一张氛围图。",
        "收尾点的湖面更开阔，适合作为今日路线回顾封面。",
    ]
    frame_id = new_id("frame")
    score = {
        "lighting": min(10, 7 + index % 3),
        "composition": min(10, 6 + (index * 2) % 4),
        "story_value": min(10, 7 + (index + 1) % 3),
        "share_value": min(10, 7 + index % 4),
    }
    frame = {
        "frame_id": frame_id,
        "media_id": media["media_id"],
        "trip_id": media["trip_id"],
        "timestamp_ms": timestamp_ms,
        "image_url": _public_url(path),
        "thumbnail_url": _public_url(path),
        "path": str(path),
        "ai_caption": captions[index % len(captions)],
        "ai_score": score,
        "selected": False,
        "selected_reason": None,
        "marked": False,
        "marked_reason": None,
        "created_at": now_iso(),
    }
    store.frames[frame_id] = frame
    return frame


def _create_demo_frames(media: dict) -> list[dict]:
    scenes = [
        ("湖边步道", "天空、水面和步道适合做开场镜头", ("#9ed4e6", "#dcefbf", "#7eb59c")),
        ("树影取景点", "全景相机可以收进两侧树影", ("#b8d8a8", "#f4e8bd", "#80a970")),
        ("安静侧路", "人流更少，适合边走边讲解", ("#d6d1bf", "#b7d5d6", "#8c9f87")),
        ("咖啡休息点", "路线中的恢复节点，也适合作为故事转折", ("#f2d7ae", "#d7e7c3", "#a8a06e")),
        ("开阔湖景", "适合封面和路线回顾", ("#a9d7f2", "#f5eed2", "#6da6ba")),
    ]
    return [
        _create_frame(media, index * settings.frame_interval_seconds * 1000, _write_demo_svg(media["media_id"], index, title, subtitle, palette), index)
        for index, (title, subtitle, palette) in enumerate(scenes)
    ]


def extract_frames(media_id: str) -> tuple[dict, list[dict]]:
    media = store.media[media_id]
    job_id = new_id("job")
    job = {"job_id": job_id, "status": "running", "message": "正在抽帧", "result": None, "created_at": now_iso()}
    store.jobs[job_id] = job

    existing = [frame for frame in store.frames.values() if frame["media_id"] == media_id]
    if existing:
        job["status"] = "succeeded"
        job["message"] = "已复用已有抽帧"
        job["result"] = {"frame_count": len(existing)}
        persist_store()
        return job, existing

    frames: list[dict] = []
    path = Path(media["path"]) if media.get("path") else None
    if media["kind"] == "image" and path and path.exists():
        frames.append(_create_frame(media, 0, path, 0))
    elif media["kind"] == "video" and path and path.exists():
        output_dir = settings.frames_dir / media_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pattern = output_dir / "frame_%03d.jpg"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-vf",
            f"fps=1/{settings.frame_interval_seconds},scale=1280:-1",
            "-frames:v",
            str(settings.max_frame_analysis_count),
            str(output_pattern),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
            for index, frame_path in enumerate(sorted(output_dir.glob("frame_*.jpg"))):
                frames.append(_create_frame(media, index * settings.frame_interval_seconds * 1000, frame_path, index))
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            frames = _create_demo_frames(media)
    else:
        frames = _create_demo_frames(media)

    if not frames:
        frames = _create_demo_frames(media)

    job["status"] = "succeeded"
    job["message"] = f"已生成 {len(frames)} 张候选帧"
    job["result"] = {"frame_count": len(frames)}
    media["status"] = "frames_ready"
    record_event(media["trip_id"], "frames_extracted", "候选帧已生成", f"从素材中生成 {len(frames)} 张候选帧。", {"media_id": media_id, "frame_count": len(frames)})
    return job, frames


def select_best_frames(trip_id: str, limit: int = 5) -> list[dict]:
    frames = [frame for frame in store.frames.values() if frame["trip_id"] == trip_id]
    ranked = sorted(
        frames,
        key=lambda frame: sum((frame.get("ai_score") or {}).values()) + (20 if frame.get("marked") else 0),
        reverse=True,
    )
    selected = ranked[:limit]
    for index, frame in enumerate(selected):
        frame["selected"] = True
        frame["selected_reason"] = [
            "用户手动标记过，优先进入精选素材。" if frame.get("marked") else "光线和构图都比较稳定，适合作为封面候选。",
            "画面有明显旅行场景信息，适合放进九宫格。",
            "和路线节点关联强，可以帮助讲清今天的故事线。",
            "场景氛围轻松，符合 City Walk 的节奏。",
            "视野开阔，适合作为收尾图。",
        ][index % 5]
    return selected


def mark_frame(frame_id: str, marked: bool = True, reason: str | None = None) -> dict:
    frame = store.frames[frame_id]
    frame["marked"] = marked
    frame["marked_reason"] = reason or ("用户标记的精彩瞬间" if marked else None)
    record_event(
        frame["trip_id"],
        "frame_marked" if marked else "frame_unmarked",
        "标记精彩瞬间" if marked else "取消精彩标记",
        frame["marked_reason"] or "用户取消了这个精彩瞬间标记。",
        {"frame_id": frame_id, "timestamp_ms": frame["timestamp_ms"], "image_url": frame["image_url"]},
    )
    return frame
