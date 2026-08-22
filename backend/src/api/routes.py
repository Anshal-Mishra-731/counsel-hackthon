from fastapi import APIRouter, Request, HTTPException
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.disruption_sim import run_simulation
from src.models.spr_optimizer import load_reserves_data

# You must initialize the router BEFORE defining endpoints!
api_router = APIRouter()

@api_router.get("/latest", tags=["Frontend Bridge"])
@api_router.get("/v1/latest", tags=["Frontend Bridge"])
async def get_frontend_latest_pipeline(request: Request):
    """
    Translates our global backend state into the exact corridor-by-corridor 
    JSON shape expected by the frontend's usePipelineData.js.
    """
    simulation_state = getattr(request.app.state, "latest_simulation", {})
    
    if not getattr(request.app.state, "is_ready", False):
        live_risk = calculate_global_risk(master_routes)
        simulation_state = run_simulation(live_risk_report=live_risk)
        
    impact_metrics = simulation_state.get("impact_metrics", {})
    reallocation_plan = simulation_state.get("phase3_procurement_optimization", {}).get("reallocation_plan", [])
    economic_data = simulation_state.get("economic_estimates", {})

    phase1_risk = {}
    for corridor_key in master_routes:
        is_triggered = any(tc["corridor"] == corridor_key for tc in simulation_state.get("simulation_parameters", {}).get("triggered_corridors", []))
        phase1_risk[corridor_key] = {
            "name": corridor_key.replace("_", " ").title(),
            "risk_score": 80 if is_triggered else 20,
            "traffic_halted": is_triggered
        }

    corridors_payload = {}
    
    for tc in simulation_state.get("simulation_parameters", {}).get("triggered_corridors", []):
        c_key = tc["corridor"]
        
        affected = impact_metrics.get("affected_suppliers", [])
        mapped_affected = []
        for supp in affected:
            mapped_affected.append({
                "country": supp.get("country", "Unknown"),
                "normal_bpd": supp.get("normal_bpd", 0),
                "lost_bpd": supp.get("lost_bpd", 0),
                "surviving_bpd": supp.get("normal_bpd", 0) - supp.get("lost_bpd", 0)
            })
            
        alt_sources = []
        for realloc in reallocation_plan:
            alt_sources.append({
                "supplier": realloc.get("supplier", "").split(" (")[0], 
                "corridor": realloc.get("corridor_used", "").replace("_", " ").title(),
                "current_bpd": 0, 
                "additional_bpd_offered": realloc.get("allocated_bpd", 0),
                "lead_time_days": realloc.get("transit_lead_time_days", 0)
            })

        corridors_payload[c_key] = {
            "phase1_context": phase1_risk.get(c_key, {}),
            "scenario": {
                "corridor": phase1_risk.get(c_key, {}).get("name", c_key),
                "severity": tc.get("severity_pct", 100) / 100.0
            },
            "baseline": {
                "india_total_import_bpd": impact_metrics.get("total_baseline_demand_bpd", 4931790),
                "corridor_dependency_share": round(impact_metrics.get("initial_daily_shortfall_bpd", 0) / max(1, impact_metrics.get("total_baseline_demand_bpd", 1)), 4),
                "corridor_dependent_bpd": impact_metrics.get("initial_daily_shortfall_bpd", 0),
                "daily_shortfall_bpd": impact_metrics.get("initial_daily_shortfall_bpd", 0)
            },
            "affected_suppliers": mapped_affected,
            "alternative_sources": alt_sources,
            "derived_lead_time": {
                "estimated_replacement_days": simulation_state.get("simulation_parameters", {}).get("duration_days", 30),
                "covered_daily_bpd": sum(a["additional_bpd_offered"] for a in alt_sources),
                "residual_daily_shortfall_bpd": 0,
                "note": "Mapped dynamically from Phase 3 Reallocation."
            },
            "supply_impact": {
                "ramp_up_loss_bbl": 0,
                "chronic_loss_bbl": 0,
                "gross_loss_bbl": impact_metrics.get("cumulative_barrels_lost_staggered", 0),
                "inventory_offset_bbl": 0,
                "net_gap_bbl": impact_metrics.get("cumulative_barrels_lost_staggered", 0)
            },
            "economic_estimates": {
                "supply_drop_pct": round((impact_metrics.get("initial_daily_shortfall_bpd", 0) / max(1, impact_metrics.get("total_baseline_demand_bpd", 1))) * 100, 2),
                "price_elasticity_assumption": 1.25,
                "estimated_crude_price_spike_pct": economic_data.get("estimated_crude_price_spike_pct", 0)
            }
        }

    return {
        "phase1_risk_report": phase1_risk,
        "phase2_disruption_report": {
            "baseline_year": "2025-26",
            "india_total_import_bpd": impact_metrics.get("total_baseline_demand_bpd", 4931790),
            "corridors": corridors_payload
        }
    }