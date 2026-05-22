from fastapi import APIRouter, HTTPException

from app.domain.agent_orchestrator import analyze_companion
from app.domain.store import store
from app.schemas.media import AnalyzeFrameRequest, CompanionResponse

router = APIRouter(prefix="/api/trips/{trip_id}/companion", tags=["companion"])


@router.post("/analyze", response_model=CompanionResponse)
def analyze_endpoint(trip_id: str, payload: AnalyzeFrameRequest) -> dict:
    if trip_id not in store.trips:
        raise HTTPException(status_code=404, detail="Trip not found")
    return analyze_companion(trip_id, payload.frame_id, payload.route_node_id, payload.user_status)
