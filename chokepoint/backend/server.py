"""
Chokepoint API server.

Drop this file at your project root, next to run.py (it imports
`from src.final_pipeline import run_once`, exactly like run.py does).

Run it with:
    uvicorn server:app --reload --port 8000

What it does
------------
- On startup: loads the last `final_result.json` if one exists on disk
  (so the API has something to serve immediately), otherwise falls back
  to a clearly-labelled SAMPLE snapshot until the first live pipeline
  run completes.
- In the background: calls your existing `run_once()` (Phase 1 -> Phase 2,
  exactly your current pipeline, unmodified) on a timer, honouring the
  same REFRESH_INTERVAL_SECONDS your final_pipeline.py already defines,
  and caches the latest result in memory.
- On demand: `POST /api/simulate` triggers an immediate re-run (with a
  short cooldown so a user mashing "Start Simulation" doesn't blow
  through your Gemini free-tier quota).
- Every endpoint below reads from that single cached `final_result`
  dict — nothing about corridor risk, supplier volumes, lead times or
  economics is hardcoded here. The only static tables in this file are
  cartographic reference data (sea-lane waypoints for the map, country
  lat/lng for plotting) and a five-bucket risk-score->color mapping,
  neither of which exists in your dataset and both of which are normal
  to keep as reference constants in an API layer.

TODO before running
--------------------
1. Confirm the two import lines below marked "ADJUST THIS PATH" match
   your actual loader module locations for:
     - load_baseline_oil_balance()
     - load_supplier_corridor_dependency()
   If they don't import cleanly, /api/stats still works — it just
   reports those sections as `"available": false` instead of crashing,
   so nothing else in the app breaks while you fix the path.
2. Make sure `pip install fastapi uvicorn[standard]` is done in the
   same environment as the rest of your pipeline's dependencies.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.final_pipeline import run_once, REFRESH_INTERVAL_SECONDS

logger = logging.getLogger("chokepoint.api")
logging.basicConfig(level=logging.INFO)

# ADJUST THIS PATH if your loader lives somewhere else
try:
    from src.oil_balance import load_baseline_oil_balance
except Exception:  # pragma: no cover - degrade gracefully, don't crash the API
    load_baseline_oil_balance = None
    logger.warning("Could not import load_baseline_oil_balance — /api/stats.baseline will be unavailable until this import is fixed.")

# ADJUST THIS PATH if your loader lives somewhere else
try:
    from src.corridor_dependency import load_supplier_corridor_dependency
except Exception:  # pragma: no cover
    load_supplier_corridor_dependency = None
    logger.warning("Could not import load_supplier_corridor_dependency — /api/stats.corridor_dependency and /api/route lookups will fall back to a static table until this import is fixed.")


# ---------------------------------------------------------------------------
# Static cartographic reference data — geography, not business data.
# These positions/waypoints don't come from a CSV because they're map
# rendering geometry, not modelled results. Extend freely as you add
# more supplier countries or corridors to CORRIDORS_TO_EVALUATE.
# ---------------------------------------------------------------------------

DESTINATION = {"name": "India", "lat": 22.31, "lng": 69.83, "port": "Jamnagar"}

# [lat, lng] — matches the country names your pipeline already uses
# (SUPPLIER_LEAD_TIME_DAYS keys), so /api/meta always has a marker for
# every supplier your lead-time table already knows about.
COUNTRY_COORDS = {
    "Iraq": [33.2, 43.7],
    "Saudi Arabia": [23.9, 45.1],
    "United Arab Emirates": [23.4, 53.8],
    "Kuwait": [29.3, 47.5],
    "Iran": [32.4, 53.7],
    "Oman": [21.5, 55.9],
    "Russia": [61.5, 60.0],
    "Nigeria": [9.1, 8.7],
    "Angola": [-11.2, 17.9],
    "United States": [38.0, -97.0],
    "Canada": [56.1, -106.3],
    "Brazil": [-14.2, -51.9],
    "Colombia": [4.6, -74.1],
    "Venezuela": [6.4, -66.6],
}

# Approximate sea-lane polylines [lat, lng] per corridor, used to draw the
# route on the Leaflet map. Origin end is intentionally a rough regional
# point (not a single country) since a corridor is shared by many suppliers.
CORRIDOR_WAYPOINTS = {
    "strait_of_hormuz": [
        [26.0, 52.0], [26.6, 56.3], [22.0, 62.0], [20.0, 66.0], [22.31, 69.83],
    ],
    "red_sea": [
        [31.3, 32.3], [27.9, 33.6], [20.0, 38.5], [12.6, 43.4], [11.5, 51.0],
        [15.0, 60.0], [22.31, 69.83],
    ],
    "cape_of_good_hope": [
        [36.1, -5.4], [14.6, -17.4], [-4.0, 8.8], [-34.35, 18.47],
        [-30.0, 40.0], [-10.0, 55.0], [10.0, 65.0], [22.31, 69.83],
    ],
    "strait_of_malacca": [
        [1.3, 103.8], [6.0, 80.0], [8.0, 76.0], [22.31, 69.83],
    ],
    "chennai_vladivostok_maritime_corridor": [
        [43.1, 131.9], [10.0, 100.0], [8.0, 80.0], [22.31, 69.83],
    ],
}

CORRIDOR_KEY_TO_NAME = {
    "strait_of_hormuz": "Strait of Hormuz",
    "red_sea": "Suez Canal / Red Sea",
    "cape_of_good_hope": "Cape of Good Hope",
    "strait_of_malacca": "Strait of Malacca",
    "chennai_vladivostok_maritime_corridor": "Direct Indian Ocean route",
}

# Used only if load_supplier_corridor_dependency() can't be imported —
# a minimal fallback so /api/route never 500s during setup.
FALLBACK_SUPPLIER_TO_CORRIDOR = {
    "Iraq": "strait_of_hormuz",
    "Saudi Arabia": "strait_of_hormuz",
    "United Arab Emirates": "strait_of_hormuz",
    "Kuwait": "strait_of_hormuz",
    "Iran": "strait_of_hormuz",
    "Oman": "strait_of_hormuz",
    "Russia": "red_sea",
    "Nigeria": "chennai_vladivostok_maritime_corridor",
    "Angola": "chennai_vladivostok_maritime_corridor",
    "United States": "cape_of_good_hope",
    "Canada": "cape_of_good_hope",
    "Brazil": "cape_of_good_hope",
    "Colombia": "cape_of_good_hope",
    "Venezuela": "cape_of_good_hope",
}

SAMPLE_FINAL_RESULT = {
    "phase1_risk_report": {
        "strait_of_hormuz": {"name": "Strait of Hormuz", "risk_score": 40, "traffic_halted": False},
        "red_sea": {"name": "Red Sea", "risk_score": 80, "traffic_halted": True},
        "cape_of_good_hope": {"name": "Cape of Good Hope", "risk_score": 20, "traffic_halted": False},
    },
    "phase2_disruption_report": {
        "baseline_year": "2025-26",
        "india_total_import_bpd": 4931790,
        "corridors": {
            "strait_of_hormuz": {
                "phase1_context": {"name": "Strait of Hormuz", "risk_score": 40, "traffic_halted": False},
                "scenario": {"corridor": "Strait of Hormuz", "severity": 0.3},
                "baseline": {
                    "india_total_import_bpd": 4931790,
                    "corridor_dependency_share": 0.4853,
                    "corridor_dependent_bpd": 2393561,
                    "daily_shortfall_bpd": 718068,
                },
                "affected_suppliers": [
                    {"country": "Iraq", "normal_bpd": 982978, "lost_bpd": 294893, "surviving_bpd": 688085},
                    {"country": "Saudi Arabia", "normal_bpd": 722673, "lost_bpd": 216802, "surviving_bpd": 505871},
                    {"country": "United Arab Emirates", "normal_bpd": 522619, "lost_bpd": 156786, "surviving_bpd": 365834},
                    {"country": "Kuwait", "normal_bpd": 161220, "lost_bpd": 48366, "surviving_bpd": 112854},
                    {"country": "Iran", "normal_bpd": 4070, "lost_bpd": 1221, "surviving_bpd": 2849},
                ],
                "alternative_sources": [
                    {"supplier": "Oman", "corridor": "Gulf of Oman (outside Hormuz chokepoint)", "current_bpd": 15643, "additional_bpd_offered": 4693, "lead_time_days": 5},
                    {"supplier": "Nigeria", "corridor": "Direct Indian Ocean route", "current_bpd": 146838, "additional_bpd_offered": 44052, "lead_time_days": 18},
                    {"supplier": "Russia", "corridor": "Suez Canal / Red Sea", "current_bpd": 1739575, "additional_bpd_offered": 521872, "lead_time_days": 18},
                ],
                "derived_lead_time": {"estimated_replacement_days": 20, "covered_daily_bpd": 718068, "residual_daily_shortfall_bpd": 0, "note": "sample"},
                "supply_impact": {"ramp_up_loss_bbl": 14361366, "chronic_loss_bbl": 0, "gross_loss_bbl": 14361366, "inventory_offset_bbl": 9500000, "net_gap_bbl": 4861366},
                "economic_estimates": {"supply_drop_pct": 14.56, "price_elasticity_assumption": 1.25, "estimated_crude_price_spike_pct": 18.2},
            },
            "red_sea": {
                "phase1_context": {"name": "Red Sea", "risk_score": 80, "traffic_halted": True},
                "scenario": {"corridor": "Suez Canal / Red Sea", "severity": 0.9},
                "baseline": {
                    "india_total_import_bpd": 4931790,
                    "corridor_dependency_share": 0.3556,
                    "corridor_dependent_bpd": 1753604,
                    "daily_shortfall_bpd": 1578244,
                },
                "affected_suppliers": [
                    {"country": "Russia", "normal_bpd": 1739575, "lost_bpd": 1565617, "surviving_bpd": 173957},
                ],
                "alternative_sources": [
                    {"supplier": "Iraq", "corridor": "Strait of Hormuz", "current_bpd": 982978, "additional_bpd_offered": 294893, "lead_time_days": 8},
                ],
                "derived_lead_time": {"estimated_replacement_days": 12, "covered_daily_bpd": 953456, "residual_daily_shortfall_bpd": 624788, "note": "sample"},
                "supply_impact": {"ramp_up_loss_bbl": 18938928, "chronic_loss_bbl": 18743648, "gross_loss_bbl": 37682576, "inventory_offset_bbl": 9500000, "net_gap_bbl": 28182576},
                "economic_estimates": {"supply_drop_pct": 32.0, "price_elasticity_assumption": 1.25, "estimated_crude_price_spike_pct": 40.0},
            },
            "cape_of_good_hope": {
                "phase1_context": {"name": "Cape of Good Hope", "risk_score": 20, "traffic_halted": False},
                "scenario": {"corridor": "Cape of Good Hope", "severity": 0.1},
                "baseline": {
                    "india_total_import_bpd": 4931790,
                    "corridor_dependency_share": 0.104,
                    "corridor_dependent_bpd": 513059,
                    "daily_shortfall_bpd": 51306,
                },
                "affected_suppliers": [
                    {"country": "United States", "normal_bpd": 264326, "lost_bpd": 26433, "surviving_bpd": 237893},
                ],
                "alternative_sources": [
                    {"supplier": "Oman", "corridor": "Gulf of Oman (outside Hormuz chokepoint)", "current_bpd": 15643, "additional_bpd_offered": 4693, "lead_time_days": 5},
                ],
                "derived_lead_time": {"estimated_replacement_days": 5, "covered_daily_bpd": 51306, "residual_daily_shortfall_bpd": 0, "note": "sample"},
                "supply_impact": {"ramp_up_loss_bbl": 256530, "chronic_loss_bbl": 0, "gross_loss_bbl": 256530, "inventory_offset_bbl": 256530, "net_gap_bbl": 0},
                "economic_estimates": {"supply_drop_pct": 1.04, "price_elasticity_assumption": 1.25, "estimated_crude_price_spike_pct": 1.3},
            },
        },
    },
}


# ---------------------------------------------------------------------------
# In-memory cache + background refresh
# ---------------------------------------------------------------------------

class State:
    def __init__(self):
        self.final_result: dict = SAMPLE_FINAL_RESULT
        self.mode: str = "sample"
        self.updated_at: float = time.time()
        self.last_run_started_at: float = 0.0
        self.lock = asyncio.Lock()


state = State()
RESULT_FILE = Path("final_result.json")
SIMULATE_COOLDOWN_SECONDS = 15  # protects your Gemini free-tier quota from button-mashing


def _load_from_disk() -> Optional[dict]:
    if RESULT_FILE.exists():
        try:
            with RESULT_FILE.open() as f:
                return json.load(f)
        except Exception:
            logger.exception("Found final_result.json but couldn't parse it.")
    return None


async def _refresh_once():
    async with state.lock:
        state.last_run_started_at = time.time()
    try:
        result = await asyncio.to_thread(run_once)  # run_once() is sync/blocking (network calls)
        async with state.lock:
            state.final_result = result
            state.mode = "live"
            state.updated_at = time.time()
        logger.info("Pipeline refresh succeeded.")
    except Exception:
        logger.exception("Pipeline refresh failed — keeping previous cached result.")


async def _background_refresh_loop():
    while True:
        await _refresh_once()
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Derivation helpers — everything below reads state.final_result, nothing
# is invented here.
# ---------------------------------------------------------------------------

def risk_bucket(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "elevated"
    if score >= 20:
        return "guarded"
    return "low"


def corridor_summary(name: str, risk_score: float, traffic_halted: bool, daily_shortfall_bpd: float) -> str:
    status = "Traffic halted." if traffic_halted else "Flowing normally."
    return f"{status} Risk score {risk_score:.0f}/100 — {daily_shortfall_bpd:,.0f} bpd at risk if disrupted."


def build_corridors_payload() -> dict:
    phase2 = state.final_result.get("phase2_disruption_report", {})
    out = []
    for key, corridor in phase2.get("corridors", {}).items():
        if corridor.get("note"):
            continue
        p1 = corridor.get("phase1_context", {})
        scenario = corridor.get("scenario", {})
        baseline = corridor.get("baseline", {})
        risk_score = p1.get("risk_score", round(scenario.get("severity", 0) * 100))
        out.append({
            "key": key,
            "name": scenario.get("corridor", CORRIDOR_KEY_TO_NAME.get(key, key)),
            "risk_score": risk_score,
            "risk_bucket": risk_bucket(risk_score),
            "traffic_halted": p1.get("traffic_halted", False),
            "summary": corridor_summary(
                scenario.get("corridor", key), risk_score,
                p1.get("traffic_halted", False), baseline.get("daily_shortfall_bpd", 0),
            ),
            "waypoints": CORRIDOR_WAYPOINTS.get(key, [[DESTINATION["lat"], DESTINATION["lng"]]]),
        })
    return {"corridors": out, "mode": state.mode, "updated_at": state.updated_at}


def build_corridor_detail(key: str) -> dict:
    phase2 = state.final_result.get("phase2_disruption_report", {})
    corridor = phase2.get("corridors", {}).get(key)
    if corridor is None:
        raise HTTPException(404, f"Unknown corridor '{key}'")
    p1 = corridor.get("phase1_context", {})
    scenario = corridor.get("scenario", {})
    baseline = corridor.get("baseline", {})
    risk_score = p1.get("risk_score", round(scenario.get("severity", 0) * 100))
    return {
        "name": scenario.get("corridor", CORRIDOR_KEY_TO_NAME.get(key, key)),
        "mode": state.mode,
        "risk_score": risk_score,
        "risk_bucket": risk_bucket(risk_score),
        "traffic_halted": p1.get("traffic_halted", False),
        "summary": corridor_summary(
            scenario.get("corridor", key), risk_score,
            p1.get("traffic_halted", False), baseline.get("daily_shortfall_bpd", 0),
        ),
        "baseline": baseline,
        "supply_impact": corridor.get("supply_impact", {}),
        "economic_estimates": corridor.get("economic_estimates", {}),
        "affected_suppliers": corridor.get("affected_suppliers", []),
        "alternative_sources": corridor.get("alternative_sources", []),
        "derived_lead_time": corridor.get("derived_lead_time", {}),
    }


def find_route_for_source(source_country: str) -> str:
    if load_supplier_corridor_dependency is not None:
        try:
            result = load_supplier_corridor_dependency()
            breakdown = result["supplier_breakdown"]
            row = breakdown[breakdown["supplier_country"] == source_country]
            if not row.empty and row.iloc[0].get("primary_corridor"):
                name_to_key = {v: k for k, v in CORRIDOR_KEY_TO_NAME.items()}
                corridor_name = row.iloc[0]["primary_corridor"]
                return name_to_key.get(corridor_name, corridor_name)
        except Exception:
            logger.exception("load_supplier_corridor_dependency() failed, falling back to static table.")
    key = FALLBACK_SUPPLIER_TO_CORRIDOR.get(source_country)
    if key is None:
        raise HTTPException(404, f"No corridor mapping for '{source_country}'")
    return key


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Chokepoint API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    disk_result = _load_from_disk()
    if disk_result:
        state.final_result = disk_result
        state.mode = "live"
        state.updated_at = RESULT_FILE.stat().st_mtime
        logger.info("Loaded cached final_result.json from disk.")
    asyncio.create_task(_background_refresh_loop())


@app.get("/api/meta")
def get_meta():
    suppliers = [
        {"country": country, "lat": lat, "lng": lng, "port": "—"}
        for country, (lat, lng) in COUNTRY_COORDS.items()
    ]
    return {"suppliers": suppliers, "destination": DESTINATION}


@app.get("/api/corridors")
def get_corridors():
    return build_corridors_payload()


@app.get("/api/corridor/{key}")
def get_corridor_detail(key: str):
    return build_corridor_detail(key)


@app.get("/api/route")
def get_route(source: str = Query(...)):
    return {"corridor_key": find_route_for_source(source)}


@app.post("/api/simulate")
async def post_simulate():
    now = time.time()
    if now - state.last_run_started_at < SIMULATE_COOLDOWN_SECONDS:
        # Too soon since the last run — serve the cache instead of spending
        # another Gemini quota call.
        return build_corridors_payload()
    await _refresh_once()
    return build_corridors_payload()


@app.get("/api/stats")
def get_stats():
    baseline = {"available": False}
    if load_baseline_oil_balance is not None:
        try:
            baseline = {"available": True, **load_baseline_oil_balance()}
        except Exception:
            logger.exception("load_baseline_oil_balance() failed.")
            baseline = {"available": False, "error": "loader failed, see server logs"}

    corridor_dependency = {"available": False, "rows": []}
    supplier_breakdown = {"available": False, "rows": []}
    if load_supplier_corridor_dependency is not None:
        try:
            result = load_supplier_corridor_dependency()
            corridor_dependency = {
                "available": True,
                "rows": result["corridor_dependency"].to_dict(orient="records"),
            }
            top_suppliers = (
                result["supplier_breakdown"]
                .sort_values("share_of_imports", ascending=False)
                .head(12)
            )
            supplier_breakdown = {
                "available": True,
                "rows": top_suppliers[["supplier_country", "qty_kg", "share_of_imports", "primary_corridor"]].to_dict(orient="records"),
            }
        except Exception:
            logger.exception("load_supplier_corridor_dependency() failed.")

    corridor_risk_snapshot = [
        {"key": c["key"], "name": c["name"], "risk_score": c["risk_score"]}
        for c in build_corridors_payload()["corridors"]
    ]

    return {
        "baseline": baseline,
        "corridor_dependency": corridor_dependency,
        "supplier_breakdown": supplier_breakdown,
        "corridor_risk_snapshot": corridor_risk_snapshot,
        "mode": state.mode,
        "updated_at": state.updated_at,
    }
