"""
FINAL ORCHESTRATOR

Flow (exactly as requested):
    1. Run Phase 1 (live news -> Gemini risk scoring)
    2. Feed that output into Phase 2 (new engine: alt suppliers -> lead
       time -> barrel loss -> economics -> affected suppliers)
    3. Print + save the combined result
    4. Wait REFRESH_INTERVAL_SECONDS, then repeat forever (Ctrl+C to stop)

IMPORTANT: Gemini's free tier has a request-per-minute quota. Running
every 20 seconds means ~3 calls/minute - check your quota before leaving
this running unattended for a long time, or you'll hit 429 errors.
"""
import json
import time
import traceback

from src.phase1 import calculate_global_risk
from src.phase2_engine import run_full_pipeline

REFRESH_INTERVAL_SECONDS = 120

CORRIDORS_TO_EVALUATE = [
    "Strait of Hormuz",
    "Red Sea",
    "Cape of Good Hope",
]


def run_once():
    print("\n" + "=" * 60)
    print("PHASE 1: Fetching live news + scoring geopolitical risk")
    print("=" * 60)
    phase1_output = calculate_global_risk(CORRIDORS_TO_EVALUATE)
    print(json.dumps(phase1_output, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("PHASE 2: Alt-supplier discovery -> lead time -> loss/economics")
    print("=" * 60)
    phase2_output = run_full_pipeline(phase1_output)

    final_result = {
        "phase1_risk_report": phase1_output,
        "phase2_disruption_report": phase2_output,
    }

    print("\n" + "=" * 60)
    print("FINAL COMBINED RESULT")
    print("=" * 60)
    print(json.dumps(final_result, indent=2, ensure_ascii=False))

    with open("final_result.json", "w") as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False)
    print("\nSaved to final_result.json")

    return final_result


def run_forever():
    print(f"Starting live pipeline - refreshing every {REFRESH_INTERVAL_SECONDS}s. Ctrl+C to stop.")
    while True:
        try:
            run_once()
        except Exception:
            print("Pipeline run failed, will retry next cycle:")
            traceback.print_exc()

        print(f"\nSleeping {REFRESH_INTERVAL_SECONDS}s before next refresh...")
        time.sleep(REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()