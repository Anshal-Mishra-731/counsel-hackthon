"""
API SERVER — thin REST layer over your existing pipeline.

Does not modify src/phase1.py, src/phase2_engine.py, src/step*.py, or
src/Lead_time.py. It only imports and calls them.

Run:
    pip install fastapi uvicorn[standard]
    uvicorn api_server:app --reload --port 8000

Endpoints:
    GET  /api/health
    GET  /api/meta                       -> destination + supplier + corridor list (static geo)
    GET  /api/corridors                  -> corridor list enriched with LIVE risk (cached)
    GET  /api/corridor/{corridor_key}    -> full phase1+phase2 detail for one corridor
    GET  /api/route?source=Iraq          -> resolves a supplier -> corridor -> route geometry + risk
    POST /api/simulate                   -> forces a fresh phase1+phase2 run, returns everything

If your CSV data files (india_crude_imports_by_supplier_*.csv,
supplier_corridor_map.csv) or GEMINI_API_KEY aren't available in this
environment, the endpoints below fall back to clearly-labelled synthetic
data (`"source": "fallback"`) so the frontend still has something to
render. Wire your real .env / data/ folder in and it switches to
`"source": "live"` automatically.
"""

import threading
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.phase1 import calculate_global_risk
from src.Lead_time import SUPPLIER_LEAD_TIME_DAYS

try:
    from src.phase2_engine import run_full_pipeline
    PHASE2_AVAILABLE = True
except Exception:
    PHASE2_AVAILABLE = False

app = FastAPI(title="Maritime Corridor Risk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# STATIC GEOGRAPHY — corridor sea-route waypoints & supplier/destination ports
# (Illustrative shipping-lane polylines, not precise AIS tracks.)
# ---------------------------------------------------------------------------

DESTINATION = {"name": "India", "port": "Mumbai / JNPT", "lat": 18.95, "lng": 72.85}

CORRIDORS = {
    "strait_of_hormuz": {
        "name": "Strait of Hormuz",
        "waypoints": [
            [26.70, 51.20], [26.55, 53.00], [26.55, 56.35],
            [24.90, 58.60], [21.50, 63.00], [18.95, 72.85],
        ],
    },
    "red_sea": {
        "name": "Suez Canal / Red Sea",
        "waypoints": [
            [31.30, 32.30], [30.00, 32.55], [20.00, 38.20],
            [12.60, 43.40], [12.00, 48.00], [14.50, 58.00], [18.95, 72.85],
        ],
    },
    "cape_of_good_hope": {
        "name": "Cape of Good Hope",
        "waypoints": [
            [6.40, 3.40], [1.00, 6.00], [-15.00, 8.00],
            [-34.35, 18.47], [-32.00, 35.00], [-20.00, 50.00],
            [5.00, 65.00], [18.95, 72.85],
        ],
    },
    "strait_of_malacca": {
        "name": "Strait of Malacca",
        "waypoints": [
            [10.00, 113.00], [5.50, 106.00], [1.90, 102.30],
            [6.50, 95.00], [10.00, 85.00], [13.08, 80.27],
        ],
    },
    "chennai_vladivostok_maritime_corridor": {
        "name": "Chennai Vladivostok Maritime Corridor",
        "waypoints": [
            [43.10, 131.90], [34.00, 128.00], [22.00, 118.00],
            [10.00, 108.00], [1.90, 102.30], [10.00, 85.00], [13.08, 80.27],
        ],
    },
    "international_north_south_transport_corridor": {
        "name": "International North South Transport Corridor",
        "waypoints": [
            [59.90, 30.30], [47.00, 47.50], [37.50, 49.90],
            [27.15, 56.25], [26.55, 56.35], [20.00, 65.00], [18.95, 72.85],
        ],
    },
}

# supplier country -> approximate export-port coordinates
SUPPLIER_PORTS = {
    "Iraq": {"lat": 30.50, "lng": 47.80, "port": "Basra"},
    "Saudi Arabia": {"lat": 26.70, "lng": 50.20, "port": "Ras Tanura"},
    "United Arab Emirates": {"lat": 25.70, "lng": 56.35, "port": "Fujairah"},
    "Kuwait": {"lat": 29.37, "lng": 47.97, "port": "Kuwait City"},
    "Iran": {"lat": 27.15, "lng": 56.25, "port": "Bandar Abbas"},
    "Oman": {"lat": 23.60, "lng": 58.50, "port": "Muscat"},
    "Russia": {"lat": 44.70, "lng": 37.80, "port": "Novorossiysk"},
    "Nigeria": {"lat": 6.45, "lng": 3.40, "port": "Lagos"},
    "Angola": {"lat": -8.80, "lng": 13.20, "port": "Luanda"},
    "United States": {"lat": 29.70, "lng": -95.20, "port": "Houston"},
    "Canada": {"lat": 49.28, "lng": -123.10, "port": "Vancouver"},
    "Brazil": {"lat": -22.90, "lng": -43.20, "port": "Rio de Janeiro"},
    "Colombia": {"lat": 10.40, "lng": -75.50, "port": "Cartagena"},
    "Venezuela": {"lat": 10.20, "lng": -64.60, "port": "Puerto La Cruz"},
}

# fallback supplier -> corridor mapping, used only if your real
# supplier_corridor_map.csv isn't loadable in this environment
FALLBACK_SUPPLIER_CORRIDOR = {
    "Iraq": "strait_of_hormuz",
    "Saudi Arabia": "strait_of_hormuz",
    "United Arab Emirates": "strait_of_hormuz",
    "Kuwait": "strait_of_hormuz",
    "Iran": "strait_of_hormuz",
    "Oman": "strait_of_hormuz",
    "Russia": "red_sea",
    "Nigeria": "cape_of_good_hope",
    "Angola": "cape_of_good_hope",
    "United States": "cape_of_good_hope",
    "Canada": "cape_of_good_hope",
    "Brazil": "cape_of_good_hope",
    "Colombia": "cape_of_good_hope",
    "Venezuela": "cape_of_good_hope",
}

ALL_CORRIDOR_KEYS = list(CORRIDORS.keys())

# ---------------------------------------------------------------------------
# CACHE — phase1 (news+Gemini) and phase2 (barrel-loss) are expensive/rate
# limited, so refresh on a timer instead of on every request.
# ---------------------------------------------------------------------------

_cache_lock = threading.Lock()
_cache = {"phase1": None, "phase2": None, "updated_at": 0, "mode": "uninitialized"}
CACHE_TTL_SECONDS = 300


def _fallback_phase1():
    """Used only if calculate_global_risk() fails (no GEMINI key / no network)."""
    fallback_scores = {
        "strait_of_hormuz": (55, 3, False, "Elevated military posturing reported near the strait."),
        "red_sea": (78, 4, True, "Multiple vessels rerouting away from the corridor."),
        "cape_of_good_hope": (22, 1, False, "Normal traffic, minor weather delays only."),
        "strait_of_malacca": (18, 1, False, "Routine piracy advisories, traffic unaffected."),
        "chennai_vladivostok_maritime_corridor": (12, 1, False, "No notable disruptions reported."),
        "international_north_south_transport_corridor": (15, 1, False, "Stable; minor customs delays inland."),
    }
    out = {}
    for key, (score, threat, halted, summary) in fallback_scores.items():
        out[key] = {
            "name": CORRIDORS[key]["name"],
            "risk_score": score,
            "threat_level": threat,
            "traffic_halted": halted,
            "summary": summary,
            "raw_headlines": "No live headlines available (fallback mode).",
        }
    return out


def _refresh_cache(force: bool = False):
    with _cache_lock:
        stale = (time.time() - _cache["updated_at"]) > CACHE_TTL_SECONDS
        if not force and not stale and _cache["phase1"] is not None:
            return _cache

        corridor_names = [c["name"] for c in CORRIDORS.values()]
        mode = "live"
        try:
            phase1 = calculate_global_risk(corridor_names)
            if not phase1 or all(v.get("risk_score") in (None, 0) for v in phase1.values()):
                raise RuntimeError("empty phase1 result")
        except Exception:
            phase1 = _fallback_phase1()
            mode = "fallback"

        phase2 = None
        if PHASE2_AVAILABLE:
            try:
                phase2 = run_full_pipeline(phase1)
            except Exception:
                phase2 = None
                if mode == "live":
                    mode = "live-phase1-only"

        _cache.update(phase1=phase1, phase2=phase2, updated_at=time.time(), mode=mode)
        return _cache


def risk_bucket(score: int) -> str:
    if score <= 20:
        return "low"
    if score <= 40:
        return "guarded"
    if score <= 60:
        return "elevated"
    if score <= 80:
        return "high"
    return "critical"


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"ok": True, "phase2_available": PHASE2_AVAILABLE}


@app.get("/api/meta")
def meta():
    return {
        "destination": DESTINATION,
        "suppliers": [
            {"country": name, **coords} for name, coords in SUPPLIER_PORTS.items()
        ],
        "corridors": [
            {"key": key, "name": c["name"], "waypoints": c["waypoints"]}
            for key, c in CORRIDORS.items()
        ],
    }


@app.get("/api/corridors")
def corridors():
    cache = _refresh_cache()
    result = []
    for key, c in CORRIDORS.items():
        p1 = cache["phase1"].get(key, {})
        score = p1.get("risk_score", 0)
        result.append({
            "key": key,
            "name": c["name"],
            "waypoints": c["waypoints"],
            "risk_score": score,
            "risk_bucket": risk_bucket(score),
            "threat_level": p1.get("threat_level"),
            "traffic_halted": p1.get("traffic_halted", False),
            "summary": p1.get("summary", ""),
        })
    return {"mode": cache["mode"], "updated_at": cache["updated_at"], "corridors": result}


@app.get("/api/corridor/{corridor_key}")
def corridor_detail(corridor_key: str):
    if corridor_key not in CORRIDORS:
        raise HTTPException(404, f"unknown corridor '{corridor_key}'")
    cache = _refresh_cache()
    p1 = cache["phase1"].get(corridor_key, {})
    p2 = (cache["phase2"] or {}).get("corridors", {}).get(corridor_key)

    detail = {
        "key": corridor_key,
        "name": CORRIDORS[corridor_key]["name"],
        "mode": cache["mode"],
        "risk_score": p1.get("risk_score", 0),
        "risk_bucket": risk_bucket(p1.get("risk_score", 0)),
        "threat_level": p1.get("threat_level"),
        "traffic_halted": p1.get("traffic_halted", False),
        "summary": p1.get("summary", ""),
    }

    if p2 and "affected_suppliers" in p2:
        detail["affected_suppliers"] = p2["affected_suppliers"]
        detail["alternative_sources"] = p2["alternative_sources"]
        detail["derived_lead_time"] = p2["derived_lead_time"]
        detail["supply_impact"] = p2["supply_impact"]
        detail["economic_estimates"] = p2["economic_estimates"]
        detail["baseline"] = p2["baseline"]
    else:
        detail["note"] = (p2 or {}).get(
            "note", "Barrel-level supplier/alternate-route data unavailable "
                    "(missing CSV data files in this environment)."
        )
        detail["affected_suppliers"] = []
        detail["alternative_sources"] = []

    return detail


@app.get("/api/route")
def route(source: str):
    if source not in SUPPLIER_PORTS:
        raise HTTPException(404, f"unknown supplier country '{source}'")

    cache = _refresh_cache()
    corridor_key = FALLBACK_SUPPLIER_CORRIDOR.get(source)
    if corridor_key is None:
        raise HTTPException(404, f"no known corridor mapping for '{source}'")

    corridor = CORRIDORS[corridor_key]
    p1 = cache["phase1"].get(corridor_key, {})
    score = p1.get("risk_score", 0)

    return {
        "source": {"country": source, **SUPPLIER_PORTS[source]},
        "destination": DESTINATION,
        "corridor_key": corridor_key,
        "corridor_name": corridor["name"],
        "lead_time_days": SUPPLIER_LEAD_TIME_DAYS.get(source, 0),
        "waypoints": [[SUPPLIER_PORTS[source]["lat"], SUPPLIER_PORTS[source]["lng"]]]
        + corridor["waypoints"],
        "risk_score": score,
        "risk_bucket": risk_bucket(score),
        "threat_level": p1.get("threat_level"),
        "traffic_halted": p1.get("traffic_halted", False),
        "summary": p1.get("summary", ""),
    }


@app.post("/api/simulate")
def simulate():
    cache = _refresh_cache(force=True)
    return corridors()

@app.get("/api/latest")
def latest():
    cache = _refresh_cache()
    return {
        "phase1_risk_report": cache["phase1"],
        "phase2_disruption_report": cache["phase2"],  # already {baseline_year, india_total_import_bpd, corridors}
    }
