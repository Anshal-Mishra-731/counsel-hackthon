"""
FINAL RUNNER: Phase 1 -> Phase 2, single command.

This file assumes your existing Phase-1 code (the Google News + Gemini
script you already have working) lives in a file called `phase1.py`
in the SAME folder as this script, and exposes a function:

    calculate_global_risk(corridors: list[str]) -> dict

...which is exactly what your code already does. We import it,
run it, and feed the output straight into Phase 2's auto pipeline.

HOW TO RUN (on your machine, where Gemini API + internet both work):

    1. Put your existing Phase-1 script in this same folder, named phase1.py
    2. Make sure step1_baseline.py, step2_corridor_mapping.py,
       step3_scenario_engine.py, step5_auto_pipeline.py and the 3 CSVs
       are all in this same folder
    3. Run:
           python final_pipeline.py
"""
import json

# --- PHASE 1 (your existing Gemini + Google News script) ---
from src.phase1 import calculate_global_risk

# --- PHASE 2 (the scenario engine we built) ---
from src.step5_auto_pipeline import run_full_pipeline, CORRIDOR_KEY_TO_NAME


# These MUST be the same corridor names your Phase-1 script scores,
# spelled exactly as Phase-1 expects them (matches your test_routes list).
CORRIDORS_TO_EVALUATE = [
    "Strait of Hormuz",
    "Red Sea",
    "Cape of Good Hope",
]


def run_end_to_end():
    print("=== PHASE 1: Fetching live news + scoring geopolitical risk ===")
    phase1_raw = calculate_global_risk(CORRIDORS_TO_EVALUATE)

    # Phase-1's raw output keys look like "strait_of_hormuz", "red_sea", etc.
    # Phase-1's per-corridor dict currently has: risk_score, traffic_halted,
    # raw_headlines (no "threat_level" key - it's folded into risk_score).
    # We normalise it here into the shape Phase-2 expects.
    phase1_normalised = {}
    for key, val in phase1_raw.items():
        # your evaluate_single_corridor() encodes threat_level implicitly via
        # risk_score = threat_level * 10 (+30 if traffic_halted). Reverse it:
        score = val["risk_score"]
        halted = val["traffic_halted"]
        implied_threat_level = round((score - (30 if halted else 0)) / 10)
        implied_threat_level = max(1, min(5, implied_threat_level))

        phase1_normalised[key] = {
            "name": key.replace("_", " ").title(),
            "risk_score": score,
            "threat_level": implied_threat_level,
            "traffic_halted": halted,
        }

    print("\n=== PHASE 1 OUTPUT ===")
    print(json.dumps(phase1_normalised, indent=2))

    print("\n=== PHASE 2: Running disruption scenarios (auto-derived from Phase 1) ===")
    final_result = run_full_pipeline(phase1_normalised)

    print("\n=== FINAL COMBINED RESULT (Phase 1 + Phase 2) ===")
    print(json.dumps(final_result, indent=2))

    with open("final_result.json", "w") as f:
        json.dump(final_result, f, indent=2)
    print("\nSaved to final_result.json")

    return final_result


if __name__ == "__main__":
    run_end_to_end()