from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.domain.agent_orchestrator import build_export_bundle, build_export_manifest, generate_export
from app.domain.store import store
from app.schemas.media import ExportResponse, JobResponse

router = APIRouter(tags=["exports"])


@router.post("/api/trips/{trip_id}/exports", response_model=ExportResponse)
def create_export_endpoint(trip_id: str) -> dict:
    if trip_id not in store.trips:
        raise HTTPException(status_code=404, detail="Trip not found")
    return generate_export(trip_id)


@router.get("/api/exports/{export_id}/manifest")
def get_export_manifest_endpoint(export_id: str) -> JSONResponse:
    if export_id not in store.exports:
        raise HTTPException(status_code=404, detail="Export not found")
    manifest = build_export_manifest(export_id)
    filename = f"{export_id}-manifest.json"
    return JSONResponse(
        content=manifest,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/exports/{export_id}/bundle")
def get_export_bundle_endpoint(export_id: str) -> FileResponse:
    if export_id not in store.exports:
        raise HTTPException(status_code=404, detail="Export not found")
    bundle_path = build_export_bundle(export_id)
    return FileResponse(
        path=bundle_path,
        media_type="application/zip",
        filename=bundle_path.name,
    )


@router.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job_endpoint(job_id: str) -> dict:
    if job_id not in store.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return store.jobs[job_id]
