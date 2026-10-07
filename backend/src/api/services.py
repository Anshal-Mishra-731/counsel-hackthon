import time
import math
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.disruption_sim import run_simulation
from src.models.spr_optimizer import load_reserves_data

# --- SMART CACHE ---
_CACHED_RISK = None
_CACHED_SIMULATION = None
_LAST_CACHE_TIME = 0
CACHE_TTL_SECONDS = 300

def force_refresh_cache():
    global _CACHED_RISK, _CACHED_SIMULATION, _LAST_CACHE_TIME
    _CACHED_RISK = None
    _CACHED_SIMULATION = None
    _LAST_CACHE_TIME = 0

def to_slug(name: str) -> str:
    slug = name.lower().replace(" ", "_").replace("-", "_")
    if slug in ["instc", "international_north_south_transport_corridor"]:
        return "international_north_south_transport_corridor"
    if slug in ["red_sea", "suez_canal_red_sea"]:
        return "red_sea"
    return slug

def get_cached_risk_data():
    global _CACHED_RISK, _LAST_CACHE_TIME
    now = time.time()
    
    if _CACHED_RISK and (now - _LAST_CACHE_TIME < CACHE_TTL_SECONDS):
        return _CACHED_RISK
        
    try:
        live_risk = calculate_global_risk(master_routes)
        if live_risk and isinstance(live_risk, dict) and len(live_risk) > 0:
            _CACHED_RISK = live_risk
            _LAST_CACHE_TIME = now
            return _CACHED_RISK
    except Exception as e:
        print(f"Error fetching live risk: {e}")
        
    if _CACHED_RISK:
        return _CACHED_RISK
        
    default_payload = {
        to_slug(k): {
            "name": k.replace("_", " ").title(),
            "risk_score": 15,
            "traffic_halted": False,
            "reason": "Corridor operational under regular maritime security patrols.",
            "raw_headlines": ""
        }
        for k in master_routes
    }
    default_payload["_disrupted_suppliers"] = []
    return default_payload

def get_cached_simulation_data():
    global _CACHED_SIMULATION
    if _CACHED_SIMULATION is not None:
        return _CACHED_SIMULATION
        
    live_risk = get_cached_risk_data()
    try:
        sim = run_simulation(live_risk_report=live_risk)
        if sim and isinstance(sim, dict) and len(sim) > 0:
            _CACHED_SIMULATION = sim
            return sim
    except Exception as e:
        print(f"Error running simulation: {e}")
    return _CACHED_SIMULATION or {}


# --- SPUR ROUTING LOGIC ---
def calculate_distance_sq(coord1, coord2):
    return (coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2

def connect_port_to_trunk(port_coord, trunk_coords):
    if not trunk_coords or len(trunk_coords) < 2:
        return [port_coord, trunk_coords[-1]] if trunk_coords else [port_coord]

    best_idx = 0
    min_dist = float("inf")
    for i, pt in enumerate(trunk_coords):
        dist = calculate_distance_sq(port_coord, pt)
        if dist < min_dist:
            min_dist = dist
            best_idx = i

    downstream_path = trunk_coords[best_idx:]
    return [port_coord] + downstream_path


# --- DENSE NAUTICAL SEA LANES ---
CORRIDOR_WAYPOINTS = {
    "strait_of_hormuz": [
        [30.02, 48.55], [29.35, 49.30], [28.45, 50.15], [27.10, 51.60],
        [26.40, 53.60], [26.15, 55.40], [26.35, 56.40], [25.75, 56.95],
        [24.50, 58.50], [23.50, 60.50], [22.80, 63.50], [22.00, 66.50], [22.47, 69.84]
    ],
    "red_sea": [
        [31.30, 32.35], [30.50, 32.40], [29.90, 32.55], [27.80, 33.70],
        [26.50, 35.00], [23.50, 37.20], [20.50, 38.80], [16.50, 41.20],
        [13.80, 42.60], [12.60, 43.35], [11.90, 44.50], [12.20, 48.00],
        [12.50, 51.50], [14.50, 56.00], [17.50, 62.00], [20.50, 67.00], [22.47, 69.84]
    ],
    "cape_of_good_hope": [
        [60.35, 28.63], [57.50, 11.00], [57.70, 8.00], [53.00, 2.00],
        [50.50, -1.00], [48.50, -5.50], [44.00, -9.50], [37.00, -10.00],
        [28.00, -16.00], [20.00, -18.50], [10.00, -16.00], [4.44, 7.17],
        [0.00, 5.00], [-8.80, 12.50], [-20.00, 10.00], [-30.00, 15.00],
        [-34.80, 18.20], [-35.50, 22.00], [-34.00, 28.00], [-30.00, 35.00],
        [-25.00, 40.00], [-18.00, 45.00], [-10.00, 50.00], [0.00, 58.00],
        [10.00, 65.00], [16.00, 68.50], [22.47, 69.84]
    ],
    "strait_of_malacca": [
        [1.20, 103.90], [2.10, 102.10], [3.80, 100.20], [5.20, 97.80],
        [5.95, 95.20], [6.50, 93.40], [8.50, 87.00], [11.00, 82.50],
        [13.08, 80.27], [17.68, 83.21], [20.25, 86.65]
    ],
    "chennai_vladivostok_maritime_corridor": [
        [43.11, 131.88], [39.00, 133.00], [34.80, 129.50], [30.50, 125.00],
        [25.00, 122.50], [20.50, 120.50], [15.00, 115.00], [8.00, 109.50],
        [3.00, 106.00], [1.25, 103.85], [5.95, 95.20], [10.00, 86.00], [13.08, 80.27]
    ],
    "international_north_south_transport_corridor": [
        [27.14, 56.28], [25.29, 60.64], [24.80, 62.50], [23.50, 65.50], [22.47, 69.84]
    ]
}

DOMESTIC_REFINERY_HUBS = [
    {"name": "Jamnagar / Vadinar Hub", "port": "Reliance / Nayara Marine Terminal", "lat": 22.47, "lng": 69.84, "capacity_bpd": 1360000},
    {"name": "Mundra Port", "port": "Adani Crude Terminal", "lat": 22.75, "lng": 69.70, "capacity_bpd": 400000},
    {"name": "Mumbai High / BPCL", "port": "Jawahar Dweep (Butcher Island)", "lat": 18.95, "lng": 72.88, "capacity_bpd": 240000},
    {"name": "Kochi Refinery (BPCL)", "port": "Cochin Single Point Mooring", "lat": 9.96, "lng": 76.22, "capacity_bpd": 310000},
    {"name": "Chennai Petroleum (CPCL)", "port": "Ennore / Chennai Marine Base", "lat": 13.08, "lng": 80.27, "capacity_bpd": 210000},
    {"name": "Visakhapatnam (HPCL)", "port": "Vizag Outer Harbour SPM", "lat": 17.68, "lng": 83.21, "capacity_bpd": 166000},
    {"name": "Paradip Mega-Refinery (IOCL)", "port": "Paradip Offshore SPM", "lat": 20.25, "lng": 86.65, "capacity_bpd": 300000}
]

SUPPLIER_PROFILES = {
    "Iraq": {"corridor": "strait_of_hormuz", "port": "Basra Oil Terminal", "lat": 29.98, "lng": 48.60, "normal_bpd": 982978},
    "Saudi Arabia": {"corridor": "strait_of_hormuz", "port": "Ras Tanura Terminal", "lat": 26.65, "lng": 50.15, "normal_bpd": 722673},
    "United Arab Emirates": {"corridor": "strait_of_hormuz", "port": "Fujairah SPM / Jebel Dhanna", "lat": 25.12, "lng": 56.33, "normal_bpd": 522619},
    "Kuwait": {"corridor": "strait_of_hormuz", "port": "Mina Al-Ahmadi Sea Island", "lat": 29.08, "lng": 48.14, "normal_bpd": 161220},
    "Qatar": {"corridor": "strait_of_hormuz", "port": "Ras Laffan / Halul Island", "lat": 25.90, "lng": 51.55, "normal_bpd": 75000},
    "Oman": {"corridor": "strait_of_hormuz", "port": "Mina Al Fahal", "lat": 23.63, "lng": 58.52, "normal_bpd": 115000},
    "Russia (Novorossiysk / Primorsk)": {"corridor": "red_sea", "port": "Novorossiysk / Primorsk SPM", "lat": 44.72, "lng": 37.78, "normal_bpd": 1400000},
    "Russia (Vladivostok)": {"corridor": "chennai_vladivostok_maritime_corridor", "port": "Port of Vladivostok / Kozmino", "lat": 43.11, "lng": 131.88, "normal_bpd": 385713},
    "Algeria": {"corridor": "red_sea", "port": "Arzew Marine Terminal", "lat": 35.85, "lng": -0.31, "normal_bpd": 65000},
    "Egypt": {"corridor": "red_sea", "port": "Sidi Kerir (SUMED Terminal)", "lat": 31.10, "lng": 29.62, "normal_bpd": 45000},
    "Nigeria": {"corridor": "cape_of_good_hope", "port": "Bonny Offshore Terminal", "lat": 4.44, "lng": 7.17, "normal_bpd": 146838},
    "Angola": {"corridor": "cape_of_good_hope", "port": "Malongo / Cabinda Terminal", "lat": -5.55, "lng": 12.19, "normal_bpd": 109084},
    "United States": {"corridor": "cape_of_good_hope", "port": "LOOP / Houston Ship Channel", "lat": 28.88, "lng": -90.02, "normal_bpd": 264326},
    "Brazil": {"corridor": "cape_of_good_hope", "port": "Angra dos Reis / Santos", "lat": -23.01, "lng": -44.31, "normal_bpd": 85000},
    "Gabon": {"corridor": "cape_of_good_hope", "port": "Cap Lopez Terminal", "lat": -0.63, "lng": 8.70, "normal_bpd": 35000},
    "Norway": {"corridor": "cape_of_good_hope", "port": "Mongstad Crude Base", "lat": 60.81, "lng": 5.03, "normal_bpd": 40000},
    "Malaysia": {"corridor": "strait_of_malacca", "port": "Bintulu / Malacca STS", "lat": 3.20, "lng": 113.05, "normal_bpd": 55000},
    "Indonesia": {"corridor": "strait_of_malacca", "port": "Dumai Crude Terminal", "lat": 1.68, "lng": 101.45, "normal_bpd": 40000},
    "Australia": {"corridor": "strait_of_malacca", "port": "North West Shelf (Dampier)", "lat": -20.65, "lng": 116.71, "normal_bpd": 30000},
    "Iran": {"corridor": "international_north_south_transport_corridor", "port": "Chabahar / Bandar Abbas", "lat": 25.29, "lng": 60.64, "normal_bpd": 90000},
    "Kazakhstan": {"corridor": "international_north_south_transport_corridor", "port": "Aktau Port (Caspian)", "lat": 43.65, "lng": 51.15, "normal_bpd": 45000}
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
                "name": "India Strategic Refining Cluster",
                "port": "Vadinar, Mundra, Mumbai, Kochi, Paradip, Vizag, Chennai",
                "lat": 22.47,
                "lng": 69.84,
                "hubs": DOMESTIC_REFINERY_HUBS
            },
            "suppliers": [
                {
                    "country": k,
                    "port": v["port"],
                    "lat": v["lat"],
                    "lng": v["lng"],
                    "corridor": v["corridor"],
                    "volume_bpd": v["normal_bpd"]
                }
                for k, v in SUPPLIER_PROFILES.items()
            ]
        }

    @staticmethod
    def get_corridors_overview():
        live_risk = get_cached_risk_data()
        corridors_list = []
        disrupted = live_risk.get("_disrupted_suppliers", [])

        seen_keys = set()
        for key, data in live_risk.items():
            if key == "_disrupted_suppliers":
                continue
            norm_key = to_slug(key)
            if norm_key in seen_keys:
                continue
            seen_keys.add(norm_key)

            score = data.get("risk_score", 15)
            waypoints = CORRIDOR_WAYPOINTS.get(norm_key) or CORRIDOR_WAYPOINTS.get(key) or [[20.0, 50.0], [22.47, 69.84]]

            corridors_list.append({
                "key": norm_key,
                "name": data.get("name", norm_key.replace("_", " ").title()),
                "risk_score": score,
                "risk_bucket": bucket_for_score(score),
                "summary": data.get("reason") or data.get("summary", "Corridor operational under regular maritime security patrols."),
                "traffic_halted": data.get("traffic_halted", False),
                "raw_headlines": data.get("raw_headlines", ""),
                "waypoints": waypoints
            })

        feeder_spurs = []
        for country, profile in SUPPLIER_PROFILES.items():
            c_key = to_slug(profile["corridor"])
            trunk = CORRIDOR_WAYPOINTS.get(c_key)
            if trunk:
                spur_path = connect_port_to_trunk([profile["lat"], profile["lng"]], trunk)
                feeder_spurs.append({
                    "country": country,
                    "corridor_key": c_key,
                    "waypoints": spur_path
                })

        return {
            "mode": "live_monitoring",
            "updated_at": int(time.time()),
            "corridors": corridors_list,
            "feeder_spurs": feeder_spurs,
            "disrupted_suppliers": disrupted
        }

    @staticmethod
    def get_corridor_intelligence(key: str):
        norm_key = to_slug(key)
        live_risk = get_cached_risk_data()
        disrupted_countries_list = live_risk.get("_disrupted_suppliers", [])

        corridor_info = live_risk.get(norm_key) or live_risk.get(key)
        if not corridor_info:
            for k, v in live_risk.items():
                if to_slug(k) == norm_key:
                    corridor_info = v
                    break

        if not corridor_info:
            corridor_info = {
                "name": norm_key.replace("_", " ").title(),
                "risk_score": 15,
                "traffic_halted": False,
                "summary": "Commercial shipping flows proceeding normally.",
                "reason": "Commercial shipping flows proceeding normally.",
                "raw_headlines": ""
            }

        score = corridor_info.get("risk_score", 15)
        is_corridor_disrupted = corridor_info.get("traffic_halted", False) or score >= 60

        corridor_suppliers = []
        for k, v in SUPPLIER_PROFILES.items():
            v_corridor = to_slug(v["corridor"])
            if v_corridor == norm_key:
                country_targeted = any(target.lower() in k.lower() for target in disrupted_countries_list)
                supplier_lost = is_corridor_disrupted or country_targeted
                
                corridor_suppliers.append({
                    "country": k,
                    "normal_bpd": v["normal_bpd"],
                    "lost_bpd": v["normal_bpd"] if supplier_lost else 0,
                    "surviving_bpd": 0 if supplier_lost else v["normal_bpd"],
                    "status": "DISRUPTED" if supplier_lost else "FLOWING"
                })

        corridor_dependent_bpd = sum(s["normal_bpd"] for s in corridor_suppliers)
        corridor_lost_bpd = sum(s["lost_bpd"] for s in corridor_suppliers)
        has_any_disruption = corridor_lost_bpd > 0

        sim_result = get_cached_simulation_data()
        realloc = sim_result.get("phase3_procurement_optimization", {}).get("reallocation_plan", [])
        econ = sim_result.get("economic_estimates", {})
        impact = sim_result.get("impact_metrics", {})
        spr = sim_result.get("phase4_spr_drawdown_optimization", {})

        if not spr or not isinstance(spr, dict):
            spr = {
                "crisis_duration_days": 32 if has_any_disruption else 0,
                "isprl_summary": {
                    "total_drawn_barrels": int(corridor_lost_bpd * 32) if has_any_disruption else 0,
                    "strategic_cover_used": 32 if has_any_disruption else 0
                }
            }

        price_spike = econ.get("estimated_crude_price_spike_pct")
        if price_spike is None:
            price_spike = round((corridor_lost_bpd / 4931790) * 100 * 1.25, 1) if has_any_disruption else 0.0

        supply_drop = round((corridor_lost_bpd / 4931790) * 100, 1) if corridor_lost_bpd > 0 else 0.0

        return {
            "key": norm_key,
            "name": corridor_info.get("name", norm_key.replace("_", " ").title()),
            "mode": "Disruption Scenario Active" if has_any_disruption else "Normal Operation",
            "risk_score": score if (is_corridor_disrupted or not has_any_disruption) else max(score, 50),
            "risk_bucket": bucket_for_score(score if (is_corridor_disrupted or not has_any_disruption) else max(score, 50)),
            "traffic_halted": corridor_info.get("traffic_halted", False),
            "summary": corridor_info.get("reason") or corridor_info.get("summary", "Commercial maritime lanes safe and open."),
            "raw_headlines": corridor_info.get("raw_headlines", ""),
            "baseline": {
                "india_total_import_bpd": impact.get("total_baseline_demand_bpd", 4931790),
                "corridor_dependent_bpd": corridor_dependent_bpd,
                "daily_shortfall_bpd": corridor_lost_bpd
            },
            "affected_suppliers": corridor_suppliers,
            "alternative_sources": [
                {
                    "supplier": r.get("supplier"),
                    "lead_time_days": r.get("transit_lead_time_days"),
                    "additional_bpd_offered": r.get("allocated_bpd")
                }
                for r in realloc
            ] if has_any_disruption else [],
            "supply_impact": {
                "net_gap_bbl": impact.get("cumulative_barrels_lost_staggered", corridor_lost_bpd * 32)
            },
            "economic_estimates": {
                "estimated_crude_price_spike_pct": price_spike,
                "supply_drop_pct": supply_drop,
                "price_elasticity_assumption": 1.25
            },
            "derived_lead_time": {
                "estimated_replacement_days": sim_result.get("phase3_procurement_optimization", {}).get("critical_transit_lead_time_days", 32) if has_any_disruption else 0,
                "residual_daily_shortfall_bpd": 0
            },
            "phase4_spr_summary": spr
        }

    @staticmethod
    def resolve_supplier_route(source: str):
        profile = SUPPLIER_PROFILES.get(source, {"corridor": "strait_of_hormuz", "lat": 25.0, "lng": 55.0})
        corridor_key = to_slug(profile["corridor"])

        live_risk = get_cached_risk_data()
        corridor_risk = live_risk.get(corridor_key) or live_risk.get(profile["corridor"], {"risk_score": 15, "traffic_halted": False})
        score = corridor_risk.get("risk_score", 15)
        is_halted = corridor_risk.get("traffic_halted", False)

        disrupted_countries_list = live_risk.get("_disrupted_suppliers", [])
        if any(target.lower() in source.lower() for target in disrupted_countries_list):
            is_halted = True
            score = max(score, 60)

        trunk = CORRIDOR_WAYPOINTS.get(corridor_key, [[profile["lat"], profile["lng"]], [22.47, 69.84]])
        waypoints = connect_port_to_trunk([profile["lat"], profile["lng"]], trunk)

        return {
            "source": source,
            "corridor_key": corridor_key,
            "risk_bucket": bucket_for_score(score),
            "traffic_halted": is_halted,
            "waypoints": waypoints
        }

    @staticmethod
    def get_analytics_overview():
        live_risk = get_cached_risk_data()
        snapshot = []
        seen_names = set()

        for k, v in live_risk.items():
            if k == "_disrupted_suppliers":
                continue
            
            name = v.get("name", k.replace("_", " ").title())
            if name in seen_names:
                continue
            seen_names.add(name)
            
            snapshot.append({"key": to_slug(k), "name": name, "risk_score": v.get("risk_score", 15)})

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

    @staticmethod
    def run_custom_simulation(scenario: str = None):
        global _CACHED_RISK, _CACHED_SIMULATION, _LAST_CACHE_TIME
        _CACHED_RISK = None
        _CACHED_SIMULATION = None
        _LAST_CACHE_TIME = 0
        
        try:
            live_risk = calculate_global_risk(master_routes, custom_scenario=scenario)
            if live_risk and isinstance(live_risk, dict) and len(live_risk) > 0:
                _CACHED_RISK = live_risk
                _LAST_CACHE_TIME = time.time()
                sim = run_simulation(live_risk_report=_CACHED_RISK)
                if sim:
                    _CACHED_SIMULATION = sim
        except Exception as e:
            print(f"Error running custom simulation: {e}")
            
        return SupplyChainService.get_corridors_overview()