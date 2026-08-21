from fastapi import APIRouter, Request, HTTPException
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.disruption_sim import run_simulation
from src.models.spr_optimizer import load_reserves_data

api_router = APIRouter()

@api_router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "online"}

@api_router.get("/risk/live-corridor-status", tags=["Phase 1: Risk"])
async def get_live_corridor_status():
    """Returns live geopolitical threat level by maritime corridor."""
    live_risk = calculate_global_risk(master_routes)
    return {"corridors": live_risk}

@api_router.post("/simulation/run-scenario", tags=["Phase 2-3: Simulation"])
async def run_custom_scenario(override_days: int | None = None):
    """Triggers Phase 1-4 pipeline with custom disruption inputs."""
    live_risk = calculate_global_risk(master_routes)
    result = run_simulation(live_risk_report=live_risk, override_days=override_days)
    return result

@api_router.get("/digital-twin/network-state", tags=["Digital Twin Map"])
async def get_digital_twin_network(request: Request):
    """
    Provides GeoJSON-style network data for map visualization 
    (vessels en route, pipelines, SPR locations).
    """
    simulation_state = getattr(request.app.state, "latest_simulation", {})
    reserves_data = load_reserves_data()
    
    return {
        "type": "FeatureCollection",
        "monitored_corridors": master_routes,
        "active_disruptions": simulation_state.get("simulation_parameters", {}).get("triggered_corridors", []),
        "reallocation_routes": simulation_state.get("phase3_procurement_optimization", {}).get("reallocation_plan", []),
        "spr_caverns": reserves_data.get("strategic_petroleum_reserves_isprl", {}).get("caverns", [])
    }

@api_router.get("/simulation", tags=["Simulation State"])
async def get_latest_simulation(request: Request):
    """Returns the latest cached 4-phase digital twin state."""
    if not getattr(request.app.state, "is_ready", False):
        raise HTTPException(status_code=503, detail="Simulation initializing. Try again shortly.")
    return request.app.state.latest_simulation