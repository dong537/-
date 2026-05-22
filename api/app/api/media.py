from fastapi import APIRouter, File, HTTPException, UploadFile

from app.domain.media_service import create_demo_media, extract_frames, mark_frame, save_upload
from app.domain.store import store
from app.schemas.media import ExtractFramesResponse, FrameAsset, MarkFrameRequest, MediaAsset

router = APIRouter(tags=["media"])


@router.post("/api/trips/{trip_id}/media", response_model=MediaAsset)
async def upload_media_endpoint(trip_id: str, file: UploadFile = File(...)) -> dict:
    if trip_id not in store.trips:
        raise HTTPException(status_code=404, detail="Trip not found")
    return await save_upload(trip_id, file)


@router.post("/api/trips/{trip_id}/media/demo", response_model=MediaAsset)
def create_demo_media_endpoint(trip_id: str) -> dict:
    if trip_id not in store.trips:
        raise HTTPException(status_code=404, detail="Trip not found")
    return create_demo_media(trip_id)


@router.post("/api/media/{media_id}/extract-frames", response_model=ExtractFramesResponse)
def extract_frames_endpoint(media_id: str) -> dict:
    if media_id not in store.media:
        raise HTTPException(status_code=404, detail="Media not found")
    job, frames = extract_frames(media_id)
    return {"job_id": job["job_id"], "status": job["status"], "frames": frames}


@router.post("/api/frames/{frame_id}/mark", response_model=FrameAsset)
def mark_frame_endpoint(frame_id: str, payload: MarkFrameRequest) -> dict:
    if frame_id not in store.frames:
        raise HTTPException(status_code=404, detail="Frame not found")
    return mark_frame(frame_id, payload.marked, payload.reason)
