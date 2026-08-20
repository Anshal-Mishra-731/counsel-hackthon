import json

from src.step3_scenario_engine import run_scenario


PHASE1_SAMPLE_OUTPUT = {
    "strait_of_hormuz": {
        "name": "Strait of Hormuz",
        "risk_score": 40,
        "threat_level": 4,
        "traffic_halted": False,
    }
}


CORRIDOR_KEY_TO_NAME = {

    "strait_of_hormuz":
        "Strait of Hormuz",

    "red_sea":
        "Suez Canal / Red Sea",

    "cape_of_good_hope":
        "Cape of Good Hope",

    "strait_of_malacca":
        "Strait of Malacca",

    "chennai_vladivostok_maritime_corridor":
        "Direct Indian Ocean route",

}


def simulate(
    phase1_output: dict,
    corridor_key: str,
    duration_days: int,
    severity: float,
):

    corridor_name = (
        CORRIDOR_KEY_TO_NAME.get(
            corridor_key
        )
    )

    if corridor_name is None:

        raise ValueError(
            f"No corridor-name mapping for "
            f"'{corridor_key}'"
        )

    phase1_context = (
        phase1_output.get(
            corridor_key,
            {}
        )
    )

    scenario_result = run_scenario(
        corridor_name,
        duration_days,
        severity,
    )

    return {
        "phase1_context":
            phase1_context,

        **scenario_result,
    }


if __name__ == "__main__":

    result = simulate(
        PHASE1_SAMPLE_OUTPUT,
        corridor_key="strait_of_hormuz",
        duration_days=15,
        severity=0.80,
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )