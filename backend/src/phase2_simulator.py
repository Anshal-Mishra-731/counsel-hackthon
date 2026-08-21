import json
import os
from typing import Dict, Any, Optional

import pandas as pd

from src.phase1 import calculate_global_risk, master_routes


# ============================================================
# CONFIGURATION
# ============================================================

MT_TO_BARRELS = 7.33

# Modeled strategic reserve.
# Replace with your validated PPAC/strategic-reserve dataset later.
STRATEGIC_RESERVE_BARRELS = 9_500_000

# Current prototype assumption:
# an unaffected supplier can increase supply by 30%.
ALTERNATIVE_SUPPLY_HEADROOM = 0.30

# Only suppliers above this threshold are shown in the detailed
# alternative-supplier table.
MIN_SUPPLIER_BPD = 20_000


# ============================================================
# CORRIDOR NORMALIZATION
# ============================================================

def standardize_corridor(name: str) -> str:

    name = str(name).lower()

    if "hormuz" in name:
        return "strait_of_hormuz"

    if "red sea" in name or "suez" in name:
        return "red_sea"

    if "cape" in name:
        return "cape_of_good_hope"

    if "malacca" in name:
        return "strait_of_malacca"

    if "chennai" in name or "vladivostok" in name:
        return "chennai_vladivostok_maritime_corridor"

    if "north south" in name or "instc" in name:
        return "international_north_south_transport_corridor"

    return "other"


# ============================================================
# FILE PATHS
# ============================================================

def get_data_dir():

    current_file = os.path.abspath(__file__)

    # backend/src/phase2_simulator.py
    #              ↑
    # go two levels up -> backend
    backend_dir = os.path.dirname(
        os.path.dirname(current_file)
    )

    return os.path.join(
        backend_dir,
        "data"
    )


# ============================================================
# LOAD DYNAMIC BASELINE
# ============================================================

def generate_dynamic_baseline() -> dict:

    data_dir = get_data_dir()

    imports_path = os.path.join(
        data_dir,
        "india_crude_imports_by_supplier_2022_2025.csv"
    )

    map_path = os.path.join(
        data_dir,
        "supplier_corridor_map.csv"
    )

    try:

        df_imports = pd.read_csv(
            imports_path
        )

        df_map = pd.read_csv(
            map_path
        )

    except Exception as e:

        return {
            "error": (
                "Failed to load baseline datasets: "
                f"{str(e)}"
            )
        }

    # --------------------------------------------------------
    # Standardize supplier names
    # --------------------------------------------------------

    df_imports["supplier_country"] = (
        df_imports["supplier_country"]
        .replace(
            {
                "Russian Federation": "Russia",
                "USA": "United States"
            }
        )
    )

    # --------------------------------------------------------
    # Select latest complete year
    # --------------------------------------------------------

    available_years = sorted(
        df_imports["year"].dropna().unique()
    )

    if not available_years:

        return {
            "error": "No valid years found in supplier dataset."
        }

    latest_year = int(
        available_years[-1]
    )

    df_latest = df_imports[
        df_imports["year"] == latest_year
    ].copy()

    if df_latest.empty:

        return {
            "error": (
                f"No data available for year "
                f"{latest_year}."
            )
        }

    # --------------------------------------------------------
    # Aggregate supplier quantities
    # --------------------------------------------------------

    total_kg = (
        df_latest
        .groupby("supplier_country")[
            "net_weight_kg"
        ]
        .sum()
        .reset_index()
    )

    # --------------------------------------------------------
    # KG -> TONNES -> BARRELS -> BPD
    # --------------------------------------------------------

    total_kg["bpd"] = (
        total_kg["net_weight_kg"]
        / 1000
        * MT_TO_BARRELS
        / 365
    )

    total_kg["bpd"] = (
        total_kg["bpd"]
        .round()
        .astype(int)
    )

    # --------------------------------------------------------
    # Merge supplier -> corridor
    # --------------------------------------------------------

    merged = pd.merge(
        total_kg,
        df_map,
        on="supplier_country",
        how="left"
    )

    # --------------------------------------------------------
    # Normalize corridor
    # --------------------------------------------------------

    merged["corridor_key"] = (
        merged["primary_corridor"]
        .fillna("other")
        .apply(standardize_corridor)
    )

    # --------------------------------------------------------
    # Supplier records
    # --------------------------------------------------------

    suppliers = []

    for _, row in merged.iterrows():

        bpd = int(
            row["bpd"]
        )

        if bpd < MIN_SUPPLIER_BPD:
            continue

        suppliers.append(
            {
                "country":
                    row["supplier_country"],

                "corridor":
                    row["corridor_key"],

                "daily_volume_bpd":
                    bpd,

                "primary_corridor":
                    row.get(
                        "primary_corridor",
                        ""
                    ),

                "notes":
                    row.get(
                        "notes",
                        ""
                    )
            }
        )

    # --------------------------------------------------------
    # Total baseline
    # --------------------------------------------------------

    total_baseline_bpd = int(
        total_kg["bpd"].sum()
    )

    # --------------------------------------------------------
    # Corridor dependency
    # --------------------------------------------------------

    corridor_dependency = {}

    for corridor_key, group in merged.groupby(
        "corridor_key"
    ):

        corridor_bpd = int(
            group["bpd"].sum()
        )

        share = (
            corridor_bpd /
            total_baseline_bpd
            if total_baseline_bpd > 0
            else 0
        )

        corridor_dependency[
            corridor_key
        ] = {
            "bpd":
                corridor_bpd,

            "share":
                round(
                    share,
                    4
                )
        }

    return {

        "latest_year":
            latest_year,

        "total_demand_bpd":
            total_baseline_bpd,

        "suppliers":
            suppliers,

        "corridor_dependency":
            corridor_dependency,

        "economic_multipliers":
            {
                "price_elasticity_of_supply":
                    1.25
            },

        "strategic_reserve_bbl":
            STRATEGIC_RESERVE_BARRELS,

        "alternative_supply_headroom":
            ALTERNATIVE_SUPPLY_HEADROOM
    }


# ============================================================
# AUTO SEVERITY
# ============================================================

def derive_severity(
    risk_score: float,
    traffic_halted: bool
) -> float:

    if risk_score <= 20:
        severity = 0.10

    elif risk_score <= 40:
        severity = 0.30

    elif risk_score <= 60:
        severity = 0.50

    elif risk_score <= 80:
        severity = 0.70

    else:
        severity = 0.90

    # Confirmed traffic disruption increases severity.
    if traffic_halted:

        severity += 0.20

    return round(
        min(
            severity,
            1.0
        ),
        2
    )


# ============================================================
# AUTO DURATION
# ============================================================

def derive_duration(
    threat_level: int
) -> int:

    duration_map = {

        1: 3,

        2: 7,

        3: 10,

        4: 15,

        5: 30
    }

    return duration_map.get(
        threat_level,
        10
    )


# ============================================================
# ALTERNATIVE SUPPLY ALLOCATION
# ============================================================

def calculate_alternative_sources(
    suppliers: list,
    disrupted_corridors: set,
    required_barrels: int,
    duration_days: int
):

    alternatives = []

    remaining = required_barrels

    # --------------------------------------------------------
    # Find unaffected suppliers
    # --------------------------------------------------------

    unaffected = [

        supplier

        for supplier in suppliers

        if supplier["corridor"]
        not in disrupted_corridors

    ]

    # Largest suppliers first
    unaffected.sort(
        key=lambda x:
        x["daily_volume_bpd"],
        reverse=True
    )

    # --------------------------------------------------------
    # Allocate alternative capacity
    # --------------------------------------------------------

    for supplier in unaffected:

        if remaining <= 0:
            break

        current_bpd = (
            supplier["daily_volume_bpd"]
        )

        additional_bpd = (
            current_bpd
            * ALTERNATIVE_SUPPLY_HEADROOM
        )

        additional_capacity = int(
            additional_bpd
            * duration_days
        )

        take = min(
            additional_capacity,
            remaining
        )

        if take <= 0:
            continue

        alternatives.append(
            {
                "supplier":
                    supplier["country"],

                "corridor":
                    supplier["primary_corridor"],

                "corridor_key":
                    supplier["corridor"],

                "current_bpd":
                    current_bpd,

                "assumed_additional_capacity_pct":
                    ALTERNATIVE_SUPPLY_HEADROOM
                    * 100,

                "additional_barrels_offered":
                    int(take)
            }
        )

        remaining -= take

    return (
        alternatives,
        max(
            0,
            int(remaining)
        )
    )


# ============================================================
# MAIN PHASE 2 SIMULATOR
# ============================================================

def run_simulation(
    live_risk_report: dict,
    simulation_days: Optional[int] = None
) -> dict:

    # --------------------------------------------------------
    # 1. Load baseline
    # --------------------------------------------------------

    baseline = (
        generate_dynamic_baseline()
    )

    if "error" in baseline:

        return baseline

    total_baseline_bpd = int(
        baseline[
            "total_demand_bpd"
        ]
    )

    suppliers = baseline[
        "suppliers"
    ]

    # --------------------------------------------------------
    # 2. Determine triggered corridors
    # --------------------------------------------------------

    triggered_corridors = []

    for corridor_key, metrics in (
        live_risk_report.items()
    ):

        risk_score = float(
            metrics.get(
                "risk_score",
                0
            )
        )

        threat_level = int(
            metrics.get(
                "threat_level",
                1
            )
        )

        traffic_halted = bool(
            metrics.get(
                "traffic_halted",
                False
            )
        )

        # Only model actual disruption scenarios
        # when risk >= 60 OR traffic is halted.
        if (
            traffic_halted
            or risk_score >= 60
        ):

            severity = derive_severity(
                risk_score,
                traffic_halted
            )

            duration = (
                simulation_days
                if simulation_days is not None
                else derive_duration(
                    threat_level
                )
            )

            triggered_corridors.append(
                {
                    "corridor":
                        corridor_key,

                    "name":
                        metrics.get(
                            "name",
                            corridor_key
                        ),

                    "risk_score":
                        risk_score,

                    "threat_level":
                        threat_level,

                    "traffic_halted":
                        traffic_halted,

                    "severity_pct":
                        round(
                            severity * 100,
                            1
                        ),

                    "duration_days":
                        duration,

                    "reason":
                        metrics.get(
                            "summary",
                            ""
                        )
                }
            )

    # --------------------------------------------------------
    # 3. Calculate supplier-level losses
    # --------------------------------------------------------

    affected_suppliers = []

    total_shortfall_bpd = 0

    corridor_impact = {}

    triggered_map = {

        x["corridor"]: x

        for x in triggered_corridors
    }

    for supplier in suppliers:

        corridor = supplier[
            "corridor"
        ]

        if corridor not in triggered_map:
            continue

        trigger = triggered_map[
            corridor
        ]

        severity = (
            trigger["severity_pct"]
            / 100
        )

        normal_bpd = int(
            supplier[
                "daily_volume_bpd"
            ]
        )

        lost_bpd = int(
            normal_bpd
            * severity
        )

        total_shortfall_bpd += (
            lost_bpd
        )

        affected_suppliers.append(
            {
                "country":
                    supplier["country"],

                "normal_bpd":
                    normal_bpd,

                "lost_bpd":
                    lost_bpd,

                "surviving_bpd":
                    normal_bpd - lost_bpd,

                "chokepoint_blocked":
                    corridor,

                "severity_pct":
                    trigger[
                        "severity_pct"
                    ]
            }
        )

        # Corridor aggregate
        if corridor not in corridor_impact:

            corridor_impact[
                corridor
            ] = {
                "affected_bpd":
                    0,

                "lost_bpd":
                    0,

                "severity_pct":
                    trigger[
                        "severity_pct"
                    ]
            }

        corridor_impact[
            corridor
        ]["affected_bpd"] += (
            normal_bpd
        )

        corridor_impact[
            corridor
        ]["lost_bpd"] += (
            lost_bpd
        )

    # --------------------------------------------------------
    # 4. Gross loss
    # --------------------------------------------------------

    # If multiple triggered corridors have different durations,
    # use the maximum duration for the consolidated scenario.
    duration_days = max(
        [
            x["duration_days"]
            for x in triggered_corridors
        ],
        default=(
            simulation_days
            or 15
        )
    )

    total_barrels_lost = (
        total_shortfall_bpd
        * duration_days
    )

    # --------------------------------------------------------
    # 5. Strategic inventory
    # --------------------------------------------------------

    inventory_offset = min(
        STRATEGIC_RESERVE_BARRELS,
        total_barrels_lost
    )

    net_gap = max(
        0,
        total_barrels_lost
        - inventory_offset
    )

    # --------------------------------------------------------
    # 6. Alternative supply
    # --------------------------------------------------------

    disrupted_corridor_set = set(
        triggered_map.keys()
    )

    alternative_sources, residual_shortage = (
        calculate_alternative_sources(
            suppliers=suppliers,

            disrupted_corridors=
                disrupted_corridor_set,

            required_barrels=
                net_gap,

            duration_days=
                duration_days
        )
    )

    alternative_barrels = sum(
        x[
            "additional_barrels_offered"
        ]
        for x in alternative_sources
    )

    # --------------------------------------------------------
    # 7. Surviving daily supply
    # --------------------------------------------------------

    surviving_bpd = max(
        0,
        total_baseline_bpd
        - total_shortfall_bpd
    )

    supply_drop_pct = (

        total_shortfall_bpd
        / total_baseline_bpd
        * 100

        if total_baseline_bpd > 0
        else 0
    )

    # --------------------------------------------------------
    # 8. Economic estimate
    # --------------------------------------------------------

    elasticity = baseline[
        "economic_multipliers"
    ][
        "price_elasticity_of_supply"
    ]

    estimated_price_spike_pct = (
        supply_drop_pct
        * elasticity
    )

    # --------------------------------------------------------
    # 9. Final combined payload
    # --------------------------------------------------------

    return {

        # ====================================================
        # SCENARIO
        # ====================================================

        "scenario": {

            "duration_days":
                duration_days,

            "triggered_corridors":
                triggered_corridors,

            "number_of_triggered_corridors":
                len(
                    triggered_corridors
                )
        },

        # ====================================================
        # BASELINE
        # ====================================================

        "baseline": {

            "latest_year":
                baseline[
                    "latest_year"
                ],

            "india_total_import_bpd":
                total_baseline_bpd,

            "strategic_reserve_bbl":
                STRATEGIC_RESERVE_BARRELS,

            "corridor_dependency":
                baseline[
                    "corridor_dependency"
                ]
        },

        # ====================================================
        # CORRIDOR IMPACT
        # ====================================================

        "corridor_impact":
            corridor_impact,

        # ====================================================
        # SUPPLY IMPACT
        # ====================================================

        "supply_impact": {

            "daily_shortfall_bpd":
                total_shortfall_bpd,

            "surviving_supply_bpd":
                surviving_bpd,

            "supply_drop_pct":
                round(
                    supply_drop_pct,
                    2
                ),

            "gross_loss_bbl":
                int(
                    total_barrels_lost
                ),

            "inventory_offset_bbl":
                int(
                    inventory_offset
                ),

            "net_gap_bbl":
                int(
                    net_gap
                )
        },

        # ====================================================
        # AFFECTED SUPPLIERS
        # ====================================================

        "affected_suppliers":
            affected_suppliers,

        # ====================================================
        # ALTERNATIVE SUPPLY
        # ====================================================

        "alternative_supply": {

            "sources":
                alternative_sources,

            "total_alternative_barrels":
                int(
                    alternative_barrels
                ),

            "residual_shortage_bbl":
                int(
                    residual_shortage
                )
        },

        # ====================================================
        # ECONOMICS
        # ====================================================

        "economic_estimates": {

            "price_elasticity_assumption":
                elasticity,

            "estimated_crude_price_spike_pct":
                round(
                    estimated_price_spike_pct,
                    2
                ),

            "note":
                "Modelled estimate based on "
                "supply shock and assumed elasticity; "
                "not an official forecast."
        },

        # ====================================================
        # DATA / ASSUMPTIONS
        # ====================================================

        "model_assumptions": {

            "alternative_supplier_headroom_pct":
                ALTERNATIVE_SUPPLY_HEADROOM * 100,

            "strategic_reserve_bbl":
                STRATEGIC_RESERVE_BARRELS,

            "minimum_supplier_bpd":
                MIN_SUPPLIER_BPD,

            "severity_rule":
                "Risk score mapped to disruption severity; "
                "confirmed traffic halt adds 20 percentage points "
                "up to a maximum of 100%."
        }
    }


# ============================================================
# FULL PIPELINE
# ============================================================

def run_full_pipeline(
    simulation_days: Optional[int] = None
):

    print(
        "\n=========================================="
    )

    print(
        "PHASE 1: LIVE GEOPOLITICAL RISK"
    )

    print(
        "==========================================\n"
    )

    live_risk_data = (
        calculate_global_risk(
            master_routes
        )
    )

    print(
        json.dumps(
            live_risk_data,
            indent=2,
            ensure_ascii=False
        )
    )

    print(
        "\n=========================================="
    )

    print(
        "PHASE 2: DISRUPTION SIMULATOR"
    )

    print(
        "==========================================\n"
    )

    phase2_result = run_simulation(
        live_risk_report=
            live_risk_data,

        simulation_days=
            simulation_days
    )

    # Combine Phase 1 + Phase 2
    final_output = {

        "phase1_risk_report":
            live_risk_data,

        "phase2_disruption_report":
            phase2_result
    }

    return final_output


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Initiating full autonomous pipeline test..."
    )

    result = run_full_pipeline(
        simulation_days=15
    )

    print(
        "\n=========================================="
    )

    print(
        "FINAL API PAYLOAD"
    )

    print(
        "=========================================="
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )