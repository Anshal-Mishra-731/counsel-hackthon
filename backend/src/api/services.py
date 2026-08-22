import time
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.disruption_sim import run_simulation
from src.models.spr_optimizer import load_reserves_data

# --- SMART IN-MEMORY CACHE (Prevents duplicate LLM calls and empty-cache bugs) ---
_CACHED_RISK = None
_CACHED_SIMULATION = None
_LAST_CACHE_TIME = 0
CACHE_TTL_SECONDS = 300  # Cache for 5 minutes

def get_cached_risk_data():
    global _CACHED_RISK, _LAST_CACHE_TIME
    now = time.time()
    
    # Return cache if valid and fresh
    if _CACHED_RISK and (now - _LAST_CACHE_TIME < CACHE_TTL_SECONDS):
        return _CACHED_RISK
        
    try:
        live_risk = calculate_global_risk(master_routes)
        # ONLY cache if it's a valid non-empty dictionary
        if live_risk and isinstance(live_risk, dict) and len(live_risk) > 0:
            _CACHED_RISK = live_risk
            _LAST_CACHE_TIME = now
            return _CACHED_RISK
    except Exception as e:
        print(f"Error fetching live risk: {e}")
        
    # If it failed/returned empty, and we have a stale cache, use the stale cache
    if _CACHED_RISK:
        return _CACHED_RISK
        
    # Absolute fallback if we've NEVER had a successful call
    return {k: {"name": k.replace("_", " ").title(), "risk_score": 15, "traffic_halted": False} for k in master_routes}

def get_cached_simulation_data():
    global _CACHED_SIMULATION
    if _CACHED_SIMULATION is not None:
        return _CACHED_SIMULATION
        
    live_risk = get_cached_risk_data()
    try:
        sim = run_simulation(live_risk_report=live_risk)
        # ONLY cache if simulation succeeded
        if sim and isinstance(sim, dict) and len(sim) > 0:
            _CACHED_SIMULATION = sim
            return sim
    except Exception as e:
        print(f"Error running simulation: {e}")
        
    return _CACHED_SIMULATION or {}


# --- HIGH-PRECISION MARITIME SEA LANES (Realistic Oceanic Curves) ---
CORRIDOR_WAYPOINTS = {
    "strait_of_hormuz": [
        [29.98, 48.45], [27.50, 50.80], [26.56, 56.25], [24.80, 58.20], [21.50, 63.50], [22.84, 69.70]
    ],
    "suez_canal_red_sea": [
        [31.25, 32.30], [29.97, 32.55], [27.50, 34.00], [20.00, 38.50], [14.50, 42.20], [12.58, 43.32], [11.90, 45.00], [12.50, 51.50], [16.00, 60.00], [22.84, 69.70]
    ],
    "red_sea": [
        [31.25, 32.30], [29.97, 32.55], [27.50, 34.00], [20.00, 38.50], [14.50, 42.20], [12.58, 43.32], [11.90, 45.00], [12.50, 51.50], [16.00, 60.00], [22.84, 69.70]
    ],
    "cape_of_good_hope": [
        [60.35, 28.63], [57.50, 8.00], [52.00, 2.50], [48.50, -5.50], [36.00, -10.50], [20.00, -18.50], [4.44, 7.17], [-8.83, 12.00], [-28.00, 14.50], [-34.85, 19.80], [-32.00, 33.00], [-20.00, 48.00], [-5.00, 60.00], [10.00, 66.00], [22.84, 69.70]
    ],
    "strait_of_malacca": [
        [1.25, 103.85], [2.50, 101.80], [4.50, 98.80], [5.80, 95.20], [6.50, 90.00], [8.50, 83.00], [13.08, 80.27], [5.80, 80.50], [8.50, 76.50], [15.50, 72.50], [22.84, 69.70]
    ],
    "chennai_vladivostok_maritime_corridor": [
        [43.13, 131.88], [38.50, 132.50], [34.20, 129.50], [29.50, 125.00], [22.00, 120.00], [14.00, 114.00], [4.00, 106.50], [1.25, 103.85], [3.00, 101.00], [5.80, 95.20], [9.00, 85.00], [13.08, 80.27], [17.50, 83.50], [20.25, 86.65]
    ],
    "instc": [
        [40.40, 49.86], [37.47, 49.46], [32.65, 51.66], [27.18, 56.27], [25.30, 60.60], [23.50, 64.00], [22.84, 69.70]
    ]
}

# Real-world baseline import distribution & ports
SUPPLIER_PROFILES = {
    "Iraq": {"corridor": "strait_of_hormuz", "port": "Basra Oil Terminal", "lat": 30.50, "lng": 47.78, "normal_bpd": 982978},
    "Saudi Arabia": {"corridor": "strait_of_hormuz", "port": "Ras Tanura", "lat": 26.65, "lng": 50.15, "normal_bpd": 722673},
    "United Arab Emirates": {"corridor": "strait_of_hormuz", "port": "Fujairah / Jebel Dhanna", "lat": 25.12, "lng": 56.33, "normal_bpd": 522619},
    "Kuwait": {"corridor": "strait_of_hormuz", "port": "Mina Al-Ahmadi", "lat": 29.08, "lng": 48.14, "normal_bpd": 161220},
    "Russia": {"corridor": "suez_canal_red_sea", "port": "Novorossiysk / Primorsk", "lat": 60.35, "lng": 28.63, "normal_bpd": 1785713},
    "Nigeria": {"corridor": "cape_of_good_hope", "port": "Bonny Terminal", "lat": 4.44, "lng": 7.17, "normal_bpd": 146838},
    "Angola": {"corridor": "cape_of_good_hope", "port": "Luanda", "lat": -8.83, "lng": 13.23, "normal_bpd": 109084},
    "United States": {"corridor": "cape_of_good_hope", "port": "Houston (USGC)", "lat": 29.76, "lng": -95.36, "normal_bpd": 264326}
}

def bucket_for_score(score: float) -> str:
    if score >= 80: return "critical"
    if score >= 60: return "high"
    if score >= 40: return "elevated"
    if score >= 20: return "guarded"
    return "low"

class SupplyChainService:

    @staticmethod
    def get_meta_data():
        return {
            "destination": {
                "name": "India Refineries Hub",
                "port": "Mundra / Sikka / Paradip / Chennai",
                "lat": 22.84,
                "lng": 69.70
            },
            "suppliers": [
                {"country": k, "port": v["port"], "lat": v["lat"], "lng": v["lng"]}
                for k, v in SUPPLIER_PROFILES.items()
            ]
        }

    @staticmethod
    def get_corridors_overview():
        live_risk = get_cached_risk_data()
        corridors_list = []

        for key, data in live_risk.items():
            score = data.get("risk_score", 15)
            # Fetch waypoints flexibly to handle any key naming
            waypoints = CORRIDOR_WAYPOINTS.get(key) or CORRIDOR_WAYPOINTS.get(key.replace("suez_canal_", "")) or [[20.0, 50.0], [22.84, 69.70]]
            
            corridors_list.append({
                "key": key,
                "name": data.get("name", key.replace("_", " ").title()),
                "risk_score": score,
                "risk_bucket": bucket_for_score(score),
                "summary": data.get("reason", "Corridor operational under regular maritime security patrols."),
                "traffic_halted": data.get("traffic_halted", False),
                "waypoints": waypoints
            })

        return {
            "mode": "live_monitoring",
            "updated_at": int(time.time()),
            "corridors": corridors_list
        }

    @staticmethod
    def get_corridor_intelligence(key: str):
        live_risk = get_cached_risk_data()
        corridor_info = live_risk.get(key, {
            "name": key.replace("_", " ").title(),
            "risk_score": 15,
            "traffic_halted": False,
            "reason": "Commercial shipping flows proceeding normally."
        })

        score = corridor_info.get("risk_score", 15)
        is_disrupted = corridor_info.get("traffic_halted", False) or score >= 60

        corridor_suppliers = [
            {
                "country": k,
                "normal_bpd": v["normal_bpd"],
                "lost_bpd": v["normal_bpd"] if is_disrupted else 0,
                "surviving_bpd": 0 if is_disrupted else v["normal_bpd"]
            }
            for k, v in SUPPLIER_PROFILES.items() if v["corridor"] == key
        ]
        corridor_dependent_bpd = sum(s["normal_bpd"] for s in corridor_suppliers)

        if is_disrupted:
            sim_result = get_cached_simulation_data()
            realloc = sim_result.get("phase3_procurement_optimization", {}).get("reallocation_plan", [])
            econ = sim_result.get("economic_estimates", {})
            impact = sim_result.get("impact_metrics", {})
            spr = sim_result.get("phase4_spr_drawdown_optimization", {})
            
            return {
                "key": key,
                "name": corridor_info.get("name"),
                "mode": "Disruption Scenario Active",
                "risk_score": score,
                "risk_bucket": bucket_for_score(score),
                "traffic_halted": corridor_info.get("traffic_halted", True),
                "summary": f"INTEL RADAR: {corridor_info.get('reason', 'Active kinetic threat in corridor.')}",
                "baseline": {
                    "india_total_import_bpd": impact.get("total_baseline_demand_bpd", 4931790),
                    "corridor_dependent_bpd": corridor_dependent_bpd,
                    "daily_shortfall_bpd": corridor_dependent_bpd
                },
                "affected_suppliers": corridor_suppliers,
                "alternative_sources": [
                    {
                        "supplier": r.get("supplier"),
                        "lead_time_days": r.get("transit_lead_time_days"),
                        "additional_bpd_offered": r.get("allocated_bpd")
                    }
                    for r in realloc
                ],
                "supply_impact": {
                    "net_gap_bbl": impact.get("cumulative_barrels_lost_staggered", corridor_dependent_bpd * 32)
                },
                "economic_estimates": {
                    "estimated_crude_price_spike_pct": econ.get("estimated_crude_price_spike_pct", 48.0),
                    "supply_drop_pct": round((corridor_dependent_bpd / 4931790) * 100, 1),
                    "price_elasticity_assumption": 1.25
                },
                "derived_lead_time": {
                    "estimated_replacement_days": sim_result.get("phase3_procurement_optimization", {}).get("critical_transit_lead_time_days", 32),
                    "residual_daily_shortfall_bpd": 0
                },
                "phase4_spr_summary": spr
            }
        else:
            return {
                "key": key,
                "name": corridor_info.get("name"),
                "mode": "Normal Operation",
                "risk_score": score,
                "risk_bucket": bucket_for_score(score),
                "traffic_halted": False,
                "summary": f"INTEL RADAR: {corridor_info.get('reason', 'Commercial maritime lanes safe and open.')}",
                "baseline": {
                    "india_total_import_bpd": 4931790,
                    "corridor_dependent_bpd": corridor_dependent_bpd,
                    "daily_shortfall_bpd": 0
                },
                "affected_suppliers": [],
                "alternative_sources": [],
                "supply_impact": {"net_gap_bbl": 0},
                "economic_estimates": {
                    "estimated_crude_price_spike_pct": 0.0,
                    "supply_drop_pct": 0.0,
                    "price_elasticity_assumption": 1.25
                },
                "derived_lead_time": {
                    "estimated_replacement_days": 0,
                    "residual_daily_shortfall_bpd": 0
                },
                "note": "Corridor is operating at 100% capacity with zero supply deficit."
            }

    @staticmethod
    def resolve_supplier_route(source: str):
        profile = SUPPLIER_PROFILES.get(source, {"corridor": "strait_of_hormuz", "lat": 25.0, "lng": 55.0})
        corridor_key = profile["corridor"]

        live_risk = get_cached_risk_data()
        corridor_risk = live_risk.get(corridor_key, {"risk_score": 15, "traffic_halted": False})
        score = corridor_risk.get("risk_score", 15)

        # Dynamic bypass for disrupted Russian supply
        if source == "Russia" and corridor_risk.get("traffic_halted", False):
            waypoints = CORRIDOR_WAYPOINTS["chennai_vladivostok_maritime_corridor"]
            corridor_key = "chennai_vladivostok_maritime_corridor"
            score = 10
        else:
            waypoints = CORRIDOR_WAYPOINTS.get(corridor_key) or CORRIDOR_WAYPOINTS.get(corridor_key.replace("suez_canal_", "")) or [[profile["lat"], profile["lng"]], [22.84, 69.70]]

        return {
            "source": source,
            "corridor_key": corridor_key,
            "risk_bucket": bucket_for_score(score),
            "traffic_halted": corridor_risk.get("traffic_halted", False),
            "waypoints": waypoints
        }

    @staticmethod
    def get_analytics_overview():
        live_risk = get_cached_risk_data()
        snapshot = [
            {"key": k, "name": v.get("name", k.replace("_", " ").title()), "risk_score": v.get("risk_score", 15)}
            for k, v in live_risk.items()
        ]
        return {
            "mode": "Live LP Pipeline",
            "updated_at": int(time.time()),
            "baseline": {
                "available": True,
                "avg_all_years_bpd": 4850000,
                "latest_year": "2025-26",
                "latest_year_bpd": 4931790
            },
            "corridor_dependency": {
                "available": True,
                "rows": [
                    {"primary_corridor": "Strait of Hormuz", "share_of_imports": 0.485},
                    {"primary_corridor": "Red Sea / Suez", "share_of_imports": 0.355},
                    {"primary_corridor": "Cape of Good Hope", "share_of_imports": 0.104},
                    {"primary_corridor": "Other Routes", "share_of_imports": 0.056}
                ]
            },
            "supplier_breakdown": {
                "available": True,
                "rows": [
                    {"supplier_country": "Russia", "share_of_imports": 0.362},
                    {"supplier_country": "Iraq", "share_of_imports": 0.200},
                    {"supplier_country": "Saudi Arabia", "share_of_imports": 0.147},
                    {"supplier_country": "UAE", "share_of_imports": 0.106},
                    {"supplier_country": "Others", "share_of_imports": 0.185}
                ]
            },
            "corridor_risk_snapshot": snapshot
        }