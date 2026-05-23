from fastapi import APIRouter, HTTPException

from app.domain.route_service import create_trip, generate_initial_route, get_trip_detail, list_trip_summaries, reroute
from app.domain.store import store
from app.schemas.trip import CreateTripRequest, RerouteRequest, RoutePlan, TripDetail, TripResponse, TripSummary

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.get("", response_model=list[TripSummary])
def list_trips_endpoint(limit: int = 10) -> list[dict]:
    return list_trip_summaries(limit=max(1, min(limit, 50)))


@router.post("", response_model=TripResponse)
def create_trip_endpoint(payload: CreateTripRequest) -> TripResponse:
    trip = create_trip(payload.model_dump())
    return TripResponse(trip_id=trip["id"], status=trip["status"])


@router.get("/{trip_id}", response_model=TripDetail)
def get_trip_endpoint(trip_id: str) -> dict:
    if trip_id not in store.trips:
        raise HTTPException(status_code=404, detail="Trip not found")
    return get_trip_detail(trip_id)


@router.post("/{trip_id}/route", response_model=RoutePlan)
def generate_route_endpoint(trip_id: str) -> dict:
    if trip_id not in store.trips:
        raise HTTPException(status_code=404, detail="Trip not found")
    return generate_initial_route(trip_id)


@router.post("/{trip_id}/reroute", response_model=RoutePlan)
def reroute_endpoint(trip_id: str, payload: RerouteRequest) -> dict:
    if trip_id not in store.trips:
        raise HTTPException(status_code=404, detail="Trip not found")
    return reroute(trip_id, payload.status_action, payload.remaining_minutes)
