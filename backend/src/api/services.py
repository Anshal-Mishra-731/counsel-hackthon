import time
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.disruption_sim import run_simulation
from src.models.spr_optimizer import load_reserves_data

# --- SMART CACHE ---
_CACHED_RISK = None
_CACHED_SIMULATION = None
_LAST_CACHE_TIME = 0
CACHE_TTL_SECONDS = 300

def force_refresh_cache():
    """Wipes memory so simulation forces a fresh calculation."""
    global _CACHED_RISK, _CACHED_SIMULATION, _LAST_CACHE_TIME
    _CACHED_RISK = None
    _CACHED_SIMULATION = None
    _LAST_CACHE_TIME = 0

def to_slug(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")

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
        
    return {
        to_slug(k): {
            "name": k.replace("_", " ").title(),
            "risk_score": 15,
            "traffic_halted": False,
            "reason": "Corridor operational under regular maritime security patrols."
        }
        for k in master_routes
    }

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


# --- DENSE NAUTICAL SEA LANES (No Land Collisions) ---
CORRIDOR_WAYPOINTS = {
    "strait_of_hormuz": [
        [30.02, 48.55],  # Al Basra Offshore Terminal (ABOT)
        [29.35, 49.30],  # Kuwait Outflow Channel
        [28.45, 50.15],  # Ras Tanura Anchorage
        [27.10, 51.60],  # Central Gulf TSS
        [26.40, 53.60],  # South of Lavan Island
        [26.15, 55.40],  # Tunb Island Passage
        [26.35, 56.40],  # Strait of Hormuz Chokepoint
        [25.75, 56.95],  # Outflow into Gulf of Oman
        [24.50, 58.50],  # Gulf of Oman TSS
        [23.50, 60.50],  # Ras al Hadd Turn
        [22.80, 63.50],  # Central Arabian Sea Corridor
        [22.00, 66.50],  # Gujarat Approach
        [22.47, 69.84]   # Vadinar / Jamnagar / Mundra Hub
    ],
    "red_sea": [
        [31.30, 32.35],  # Port Said North Gate
        [30.50, 32.40],  # Great Bitter Lake
        [29.90, 32.55],  # Suez South Anchorage
        [27.80, 33.70],  # Strait of Gubal
        [26.50, 35.00],  # Northern Red Sea Central Trench
        [23.50, 37.20],  # Yanbu Offshore
        [20.50, 38.80],  # Central Red Sea
        [16.50, 41.20],  # Farasan Islands Outer Deep
        [13.80, 42.60],  # Hanish Islands Channel
        [12.60, 43.35],  # Bab-el-Mandeb Chokepoint
        [11.90, 44.50],  # Gulf of Aden Inbound
        [12.20, 48.00],  # IRTC Patrol Channel
        [12.50, 51.50],  # Socotra Gap
        [14.50, 56.00],  # Arabian Sea Deep Water
        [17.50, 62.00],  # Trans-Arabian Tanker Lane
        [20.50, 67.00],  # Western India Inbound
        [22.47, 69.84]   # Vadinar / Mundra Refineries
    ],
    "suez_canal_red_sea": [
        [31.30, 32.35], [30.50, 32.40], [29.90, 32.55], [27.80, 33.70],
        [26.50, 35.00], [23.50, 37.20], [20.50, 38.80], [16.50, 41.20],
        [13.80, 42.60], [12.60, 43.35], [11.90, 44.50], [12.20, 48.00],
        [12.50, 51.50], [14.50, 56.00], [17.50, 62.00], [20.50, 67.00],
        [22.47, 69.84]
    ],
    "cape_of_good_hope": [
        # European / Baltic crude feeder
        [60.35, 28.63],  # Primorsk (Baltic)
        [57.50, 11.00],  # Kattegat Strait
        [57.70, 8.00],   # Skagerrak
        [53.00, 2.00],   # North Sea Southern Trench
        [50.50, -1.00],  # English Channel
        [48.50, -5.50],  # Ushant TSS
        [44.00, -9.50],  # Bay of Biscay Offshore
        [37.00, -10.00], # Cape St. Vincent
        [28.00, -16.00], # Canary Islands Channel
        [20.00, -18.50], # Cape Verde Passage
        [10.00, -16.00], # Guinea Abyssal Plain
        [4.44, 7.17],    # Bonny Offshore Terminal (Nigeria)
        [0.00, 5.00],    # Equator Crossing Atlantic
        [-8.80, 12.50],  # Luanda Offshore (Angola)
        [-20.00, 10.00], # Walvis Ridge
        [-30.00, 15.00], # Namaqua Deep
        [-34.80, 18.20], # Cape of Good Hope Rounding
        [-35.50, 22.00], # Agulhas Retroflection (Deep Ocean)
        [-34.00, 28.00], # South African East Coast Passage
        [-30.00, 35.00], # Natal Basin
        [-25.00, 40.00], # Mozambique Channel South
        [-18.00, 45.00], # Mozambique Channel Center
        [-10.00, 50.00], # North Madagascar Trench
        [0.00, 58.00],   # Equatorial Indian Ocean Trunk
        [10.00, 65.00],  # Lakshadweep Sea
        [16.00, 68.50],  # Konkan Deep Water
        [22.47, 69.84]   # Vadinar Terminal, India
    ],
    "strait_of_malacca": [
        [1.20, 103.90],  # Singapore TSS
        [2.10, 102.10],  # Malacca Strait Narrow
        [3.80, 100.20],  # One Fathom Bank
        [5.20, 97.80],   # Diamond Point
        [5.95, 95.20],   # Banda Aceh Northern Gate
        [6.50, 93.40],   # Great Channel (Nicobar)
        [8.50, 87.00],   # Bay of Bengal Crossing
        [11.00, 82.50],  # Coromandel Approach
        [13.08, 80.27],  # Chennai Port & Refinery Hub
        [17.68, 83.21],  # Visakhapatnam HPCL Hub
        [20.25, 86.65]   # Paradip IOCL Mega-Refinery
    ],
    "chennai_vladivostok_maritime_corridor": [
        [43.11, 131.88], # Vladivostok Commercial Port
        [39.00, 133.00], # Sea of Japan Central
        [34.80, 129.50], # Tsushima Strait
        [30.50, 125.00], # East China Sea
        [25.00, 122.50], # East of Taiwan
        [20.50, 120.50], # Luzon Strait (Bashi Channel)
        [15.00, 115.00], # South China Sea Deep Trunk
        [8.00, 109.50],  # Spratly Deep Water
        [3.00, 106.00],  # Natuna Sea Basin
        [1.25, 103.85],  # Singapore Strait Entry
        [5.95, 95.20],   # Outflow via Banda Aceh
        [10.00, 86.00],  # Andaman Sea Traverse
        [13.08, 80.27]   # Chennai Port Terminal
    ],
    "instc": [
        [27.14, 56.28],  # Bandar Abbas Port, Iran
        [25.29, 60.64],  # Chabahar Port, Iran
        [24.80, 62.50],  # Gwadar Deep-Sea Approach
        [23.50, 65.50],  # North Arabian Sea Maritime Transit
        [22.47, 69.84]   # Vadinar / Mundra Port
    ],
    "international_north_south_transport_corridor": [
        [27.14, 56.28],  # Bandar Abbas Port
        [25.29, 60.64],  # Chabahar Port
        [24.80, 62.50],
        [23.50, 65.50],
        [22.47, 69.84]
    ]
}

# --- REAL-WORLD EXPORT PORTS & DOMESTIC REFINERIES ---
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
    # Persian Gulf (Hormuz)
    "Iraq": {"corridor": "strait_of_hormuz", "port": "Basra Oil Terminal", "lat": 29.98, "lng": 48.60, "normal_bpd": 982978},
    "Saudi Arabia": {"corridor": "strait_of_hormuz", "port": "Ras Tanura Terminal", "lat": 26.65, "lng": 50.15, "normal_bpd": 722673},
    "United Arab Emirates": {"corridor": "strait_of_hormuz", "port": "Fujairah SPM / Jebel Dhanna", "lat": 25.12, "lng": 56.33, "normal_bpd": 522619},
    "Kuwait": {"corridor": "strait_of_hormuz", "port": "Mina Al-Ahmadi Sea Island", "lat": 29.08, "lng": 48.14, "normal_bpd": 161220},
    "Qatar": {"corridor": "strait_of_hormuz", "port": "Ras Laffan / Halul Island", "lat": 25.90, "lng": 51.55, "normal_bpd": 75000},
    "Oman": {"corridor": "strait_of_hormuz", "port": "Mina Al Fahal", "lat": 23.63, "lng": 58.52, "normal_bpd": 115000},

    # Red Sea / Black Sea & Mediterranean Feeders
    "Russia": {"corridor": "red_sea", "port": "Novorossiysk / Primorsk SPM", "lat": 44.72, "lng": 37.78, "normal_bpd": 1785713},
    "Algeria": {"corridor": "red_sea", "port": "Arzew Marine Terminal", "lat": 35.85, "lng": -0.31, "normal_bpd": 65000},
    "Egypt": {"corridor": "red_sea", "port": "Sidi Kerir (SUMED Terminal)", "lat": 31.10, "lng": 29.62, "normal_bpd": 45000},

    # Cape of Good Hope Long-Haul
    "Nigeria": {"corridor": "cape_of_good_hope", "port": "Bonny Offshore Terminal", "lat": 4.44, "lng": 7.17, "normal_bpd": 146838},
    "Angola": {"corridor": "cape_of_good_hope", "port": "Malongo / Cabinda Terminal", "lat": -5.55, "lng": 12.19, "normal_bpd": 109084},
    "United States": {"corridor": "cape_of_good_hope", "port": "LOOP / Houston Ship Channel", "lat": 28.88, "lng": -90.02, "normal_bpd": 264326},
    "Brazil": {"corridor": "cape_of_good_hope", "port": "Angra dos Reis / Santos", "lat": -23.01, "lng": -44.31, "normal_bpd": 85000},
    "Gabon": {"corridor": "cape_of_good_hope", "port": "Cap Lopez Terminal", "lat": -0.63, "lng": 8.70, "normal_bpd": 35000},
    "Norway": {"corridor": "cape_of_good_hope", "port": "Mongstad Crude Base", "lat": 60.81, "lng": 5.03, "normal_bpd": 40000},

    # Far East & Malacca
    "Malaysia": {"corridor": "strait_of_malacca", "port": "Bintulu / Malacca STS", "lat": 3.20, "lng": 113.05, "normal_bpd": 55000},
    "Indonesia": {"corridor": "strait_of_malacca", "port": "Dumai Crude Terminal", "lat": 1.68, "lng": 101.45, "normal_bpd": 40000},
    "Australia": {"corridor": "strait_of_malacca", "port": "North West Shelf (Dampier)", "lat": -20.65, "lng": 116.71, "normal_bpd": 30000},

    # INSTC / Caspian
    "Iran": {"corridor": "instc", "port": "Chabahar / Bandar Abbas", "lat": 25.29, "lng": 60.64, "normal_bpd": 90000},
    "Kazakhstan": {"corridor": "instc", "port": "Aktau Port (Caspian)", "lat": 43.65, "lng": 51.15, "normal_bpd": 45000}
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

        for key, data in live_risk.items():
            norm_key = to_slug(key)
            score = data.get("risk_score", 15)
            waypoints = CORRIDOR_WAYPOINTS.get(norm_key) or CORRIDOR_WAYPOINTS.get(key) or [[20.0, 50.0], [22.47, 69.84]]

            corridors_list.append({
                "key": norm_key,
                "name": data.get("name", norm_key.replace("_", " ").title()),
                "risk_score": score,
                "risk_bucket": bucket_for_score(score),
                "summary": data.get("reason") or data.get("summary", "Corridor operational under regular maritime security patrols."),
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
        norm_key = to_slug(key)
        live_risk = get_cached_risk_data()
        corridor_info = live_risk.get(norm_key) or live_risk.get(key, {
            "name": norm_key.replace("_", " ").title(),
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
            for k, v in SUPPLIER_PROFILES.items() 
            if to_slug(v["corridor"]) == norm_key 
            or (norm_key in ["red_sea", "suez_canal_red_sea"] and v["corridor"] in ["red_sea", "suez_canal_red_sea"])
        ]
        corridor_dependent_bpd = sum(s["normal_bpd"] for s in corridor_suppliers)

        if is_disrupted:
            sim_result = get_cached_simulation_data()
            realloc = sim_result.get("phase3_procurement_optimization", {}).get("reallocation_plan", [])
            econ = sim_result.get("economic_estimates", {})
            impact = sim_result.get("impact_metrics", {})
            spr = sim_result.get("phase4_spr_drawdown_optimization", {})
            
            return {
                "key": norm_key,
                "name": corridor_info.get("name"),
                "mode": "Disruption Scenario Active",
                "risk_score": score,
                "risk_bucket": bucket_for_score(score),
                "traffic_halted": corridor_info.get("traffic_halted", True),
                "summary": f"INTEL RADAR: {corridor_info.get('reason') or corridor_info.get('summary', 'Active kinetic threat in corridor.')}",
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
                    "supply_drop_pct": round((corridor_dependent_bpd / 4931790) * 100, 1) if corridor_dependent_bpd > 0 else 0,
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
                "key": norm_key,
                "name": corridor_info.get("name"),
                "mode": "Normal Operation",
                "risk_score": score,
                "risk_bucket": bucket_for_score(score),
                "traffic_halted": False,
                "summary": f"INTEL RADAR: {corridor_info.get('reason') or corridor_info.get('summary', 'Commercial maritime lanes safe and open.')}",
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
        corridor_key = to_slug(profile["corridor"])

        live_risk = get_cached_risk_data()
        corridor_risk = live_risk.get(corridor_key) or live_risk.get(profile["corridor"], {"risk_score": 15, "traffic_halted": False})
        score = corridor_risk.get("risk_score", 15)

        # Dynamic bypass for disrupted Russian supply via Pacific route
        if source == "Russia" and corridor_risk.get("traffic_halted", False):
            waypoints = CORRIDOR_WAYPOINTS["chennai_vladivostok_maritime_corridor"]
            corridor_key = "chennai_vladivostok_maritime_corridor"
            score = 10
        else:
            trunk = CORRIDOR_WAYPOINTS.get(corridor_key, [[profile["lat"], profile["lng"]], [22.47, 69.84]])
            # Connect the individual supplier port cleanly to the oceanic trunk
            waypoints = [[profile["lat"], profile["lng"]]] + trunk[1:]

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
            {"key": to_slug(k), "name": v.get("name", k.replace("_", " ").title()), "risk_score": v.get("risk_score", 15)}
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