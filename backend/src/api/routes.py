from fastapi import APIRouter, Query, Request
from src.api.services import SupplyChainService
from src.api.schemas import MetaResponse, CorridorsResponse
from pydantic import BaseModel
from typing import Optional

class SimulationPayload(BaseModel):
    scenario: Optional[str] = None

api_router = APIRouter()

@api_router.get("/api/meta", tags=["Frontend Bridge"])
async def get_meta():
    """Returns suppliers, ports, and refinery destination metadata."""
    return SupplyChainService.get_meta_data()

@api_router.get("/api/corridors", tags=["Frontend Bridge"])
async def get_corridors(request: Request = None):
    """Returns high-level status and sea-lane waypoints for all 6 corridors."""
    return SupplyChainService.get_corridors_overview()

@api_router.get("/api/corridor/{key}", tags=["Frontend Bridge"])
async def get_corridor_detail(key: str):
    """Returns deep-dive intelligence and LP resolution for a specific corridor."""
    return SupplyChainService.get_corridor_intelligence(key)

@api_router.get("/api/route", tags=["Frontend Bridge"])
async def get_route(source: str = Query(...)):
    """Resolves active sea route waypoints from a supplier country to India."""
    return SupplyChainService.resolve_supplier_route(source)

@api_router.post("/api/simulate", tags=["Frontend Bridge"])
async def post_simulate(payload: Optional[SimulationPayload] = None):
    """Executes live simulation recalculation with optional custom scenario."""
    scenario_text = payload.scenario if payload and payload.scenario else None
    return SupplyChainService.run_custom_simulation(scenario=scenario_text)

@api_router.get("/api/stats", tags=["Frontend Bridge"])
async def get_stats():
    """Returns aggregate dependency metrics and risk score charts."""
    return SupplyChainService.get_analytics_overview()

@api_router.get("/api/analytics", tags=["Frontend Bridge"])
async def get_analytics():
    """Returns full per-corridor breakdown cards for the analytics grid."""
    overview = SupplyChainService.get_corridors_overview()
    detailed_corridors = [
        SupplyChainService.get_corridor_intelligence(c["key"])
        for c in overview["corridors"]
    ]
    return {"corridors": detailed_corridors}