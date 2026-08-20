"""
STEP 5: Actually USE Phase-1's risk output to drive Phase-2, automatically.

Instead of the user manually typing severity=0.8, we derive severity
FROM the Phase-1 risk_score + traffic_halted flag using a transparent
rule table. This is not a random hardcoded number - it's a documented
mapping you can tune, and it's the same idea the original spec suggested:

    "Risk score 40 -> possible scenarios -> 10%/30%/50%/80%/100% disruption"

We pick ONE scenario automatically based on how severe Phase-1 says
things currently are, instead of making the user choose.
"""
import json
from src.step3_scenario_engine import run_scenario

# ---------------------------------------------------------------------------
# RULE TABLE: risk_score (0-100) -> assumed severity (0-1) if this corridor
# were to actually get disrupted right now. This is the ONE place you'd
# tune this logic - everything else is calculated from your real CSV data.
# ---------------------------------------------------------------------------
def derive_severity_from_risk(risk_score: int, traffic_halted: bool) -> float:
    if risk_score <= 20:
        severity = 0.10      # diplomatic tension only
    elif risk_score <= 40:
        severity = 0.30      # military posturing
    elif risk_score <= 60:
        severity = 0.50      # active friction, some rerouting
    elif risk_score <= 80:
        severity = 0.70      # serious escalation
    else:
        severity = 0.90      # near-total breakdown

    # If news already confirms traffic is halted, bump severity up
    # (we know for a fact ships are being diverted/stopped)
    if traffic_halted:
        severity = min(1.0, severity + 0.20)

    return round(severity, 2)


def derive_duration_from_threat_level(threat_level: int) -> int:
    """
    Higher threat level -> we model a longer plausible disruption window.
    threat_level is 1-5 as defined in your Phase-1 prompt.
    """
    duration_map = {1: 3, 2: 7, 3: 10, 4: 15, 5: 30}
    return duration_map.get(threat_level, 10)


# Map your Phase-1 corridor keys -> exact corridor names in supplier_corridor_map.csv
# Corridors with no crude-oil supplier dependency in our dataset (e.g. INSTC,
# Chennai-Vladivostok) are marked None - we skip the barrel-loss calc for them
# and just say so, rather than faking a number.
CORRIDOR_KEY_TO_NAME = {
    "strait_of_hormuz": "Strait of Hormuz",
    "red_sea": "Suez Canal / Red Sea",
    "cape_of_good_hope": "Cape of Good Hope",
    "strait_of_malacca": None,   # no direct crude-import dependency in our data
    "chennai_vladivostok_maritime_corridor": None,
    "international_north_south_transport_corridor": None,
}


def run_full_pipeline(phase1_output: dict):
    """
    Takes RAW Phase-1 output (exactly what your Gemini step produces) and
    automatically runs Phase-2 for every corridor Phase-1 evaluated.
    No manual severity/duration input required.
    """
    report = {}

    for corridor_key, p1 in phase1_output.items():
        corridor_name = CORRIDOR_KEY_TO_NAME.get(corridor_key, "UNMAPPED")

        if corridor_name is None:
            report[corridor_key] = {
                "phase1_context": p1,
                "note": "No crude-oil import dependency data available for this "
                        "corridor in our dataset - cannot compute barrel-level impact.",
            }
            continue
        if corridor_name == "UNMAPPED":
            report[corridor_key] = {
                "phase1_context": p1,
                "note": f"corridor_key '{corridor_key}' not in CORRIDOR_KEY_TO_NAME - add it.",
            }
            continue

        risk_score = p1.get("risk_score", 0)
        threat_level = p1.get("threat_level", 1)
        traffic_halted = p1.get("traffic_halted", False)

        # <-- THIS is the actual Phase1 -> Phase2 connection -->
        auto_severity = derive_severity_from_risk(risk_score, traffic_halted)
        auto_duration = derive_duration_from_threat_level(threat_level)

        scenario_result = run_scenario(corridor_name, auto_duration, auto_severity)

        report[corridor_key] = {
            "phase1_context": p1,
            "auto_derived_inputs": {
                "severity": auto_severity,
                "duration_days": auto_duration,
                "derived_from": "risk_score + traffic_halted -> severity; "
                                 "threat_level -> duration",
            },
            **scenario_result,
        }

    return report


if __name__ == "__main__":
    # This is the REAL Phase-1 output you pasted earlier (Gemini result)
    PHASE1_OUTPUT = {
        "strait_of_hormuz": {"name": "Strait of Hormuz", "risk_score": 40, "threat_level": 4, "traffic_halted": False},
        "red_sea": {"name": "Red Sea", "risk_score": 70, "threat_level": 4, "traffic_halted": True},
        "cape_of_good_hope": {"name": "Cape of Good Hope", "risk_score": 30, "threat_level": 3, "traffic_halted": False},
        "strait_of_malacca": {"name": "Strait of Malacca", "risk_score": 30, "threat_level": 3, "traffic_halted": False},
        "chennai_vladivostok_maritime_corridor": {"name": "Chennai Vladivostok Maritime Corridor", "risk_score": 10, "threat_level": 1, "traffic_halted": False},
        "international_north_south_transport_corridor": {"name": "International North South Transport Corridor", "risk_score": 10, "threat_level": 1, "traffic_halted": False},
    }

    result = run_full_pipeline(PHASE1_OUTPUT)
    print(json.dumps(result, indent=2))