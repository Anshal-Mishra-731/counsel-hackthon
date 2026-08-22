"""
PHASE 2 ENGINE:
    1. Take Phase-1's risk_score / traffic_halted for a corridor
    2. Work out the DAILY loss rate for that corridor (not yet multiplied
       by any duration)
    3. Find alternative suppliers (full details: country, corridor,
       current bpd, how much extra they could realistically supply)
    4. Using those alternative suppliers' REAL shipping lead-times,
       predict how many days it will actually take before enough
       replacement oil is flowing - this REPLACES an arbitrary
       threat_level -> duration_days guess table
    5. ONLY THEN calculate gross barrel loss, inventory offset, net gap
    6. Calculate economic impact (estimated price spike %)
    7. Return affected_suppliers + everything above, all in one payload
"""
import math

from src.step1_baseline import load_baseline_oil_balance
from src.step2_corridor_mapping import load_supplier_corridor_dependency
from src.lead_time import get_lead_time_days, weighted_average_lead_time

# ---------------------------------------------------------------------------
# MODEL ASSUMPTIONS (all in one place, clearly labelled)
# ---------------------------------------------------------------------------
STRATEGIC_RESERVE_BARRELS = 9_500_000       # India's usable strategic reserve (approx public figure)
ALTERNATIVE_SUPPLY_HEADROOM_PCT = 0.30        # an unaffected supplier can flex up by ~30% of current volume
PRICE_ELASTICITY_OF_SUPPLY = 1.25             # rough elasticity: % price spike per % supply drop
CHRONIC_EXPOSURE_WINDOW_DAYS = 30             # if alt. supply can't fully cover the gap, how long we
                                               # assume the residual shortfall persists (reporting only)

CORRIDOR_KEY_TO_NAME = {
    "strait_of_hormuz": "Strait of Hormuz",
    "red_sea": "Suez Canal / Red Sea",
    "cape_of_good_hope": "Cape of Good Hope",
    "strait_of_malacca": None,                        # no crude-import dependency in our dataset
    "chennai_vladivostok_maritime_corridor": None,
    "international_north_south_transport_corridor": None,
}


def derive_severity_from_risk(risk_score: int, traffic_halted: bool) -> float:
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

    if traffic_halted:
        severity = min(1.0, severity + 0.20)
    return round(severity, 2)


def evaluate_corridor(corridor_name: str, severity: float, supplier_breakdown, india_total_bpd):
    """
    Runs the full new-order calculation for ONE corridor:
    daily loss -> alternative suppliers -> lead time -> barrel loss -> economics
    """
    # --- 1. Daily loss RATE for this corridor (no duration yet) ---
    dep_share_series = (
        supplier_breakdown.dropna(subset=["primary_corridor"])
        .groupby("primary_corridor")["share_of_imports"].sum()
    )
    corridor_dependency_share = float(dep_share_series.get(corridor_name, 0.0))
    corridor_dependent_bpd = india_total_bpd * corridor_dependency_share
    daily_shortfall_bpd = corridor_dependent_bpd * severity

    # --- 2. Affected suppliers (the ones actually ON this corridor) ---
    affected_suppliers = []
    on_corridor = supplier_breakdown[supplier_breakdown["primary_corridor"] == corridor_name]
    for _, row in on_corridor.iterrows():
        normal_bpd = row["share_of_imports"] * india_total_bpd
        lost_bpd = normal_bpd * severity
        affected_suppliers.append({
            "country": row["supplier_country"],
            "normal_bpd": round(normal_bpd),
            "lost_bpd": round(lost_bpd),
            "surviving_bpd": round(normal_bpd - lost_bpd),
        })
    affected_suppliers.sort(key=lambda x: x["lost_bpd"], reverse=True)

    # --- 3. Alternative suppliers: anyone NOT on this corridor, with headroom ---
    unaffected = supplier_breakdown[supplier_breakdown["primary_corridor"] != corridor_name].copy()
    unaffected["current_bpd"] = unaffected["share_of_imports"] * india_total_bpd
    unaffected["headroom_bpd"] = unaffected["current_bpd"] * ALTERNATIVE_SUPPLY_HEADROOM_PCT
    unaffected["lead_time_days"] = unaffected["supplier_country"].apply(get_lead_time_days)

    # Prioritise FASTEST-arriving alternative supply first (this is what actually
    # determines how quickly the gap can be closed)
    unaffected = unaffected.sort_values("lead_time_days", ascending=True)

    alternative_sources = []
    allocations_for_lead_time = []   # used to compute weighted lead time
    remaining_daily_bpd = daily_shortfall_bpd

    for _, row in unaffected.iterrows():
        if remaining_daily_bpd <= 0:
            break
        take_bpd = min(row["headroom_bpd"], remaining_daily_bpd)
        if take_bpd <= 0:
            continue

        alternative_sources.append({
            "supplier": row["supplier_country"],
            "corridor": row["primary_corridor"],
            "current_bpd": round(row["current_bpd"]),
            "additional_bpd_offered": round(take_bpd),
            "lead_time_days": row["lead_time_days"],
        })
        allocations_for_lead_time.append({
            "supplier": row["supplier_country"],
            "additional_bpd_allocated": take_bpd,
        })
        remaining_daily_bpd -= take_bpd

    residual_daily_shortfall_bpd = max(0, remaining_daily_bpd)
    covered_daily_bpd = daily_shortfall_bpd - residual_daily_shortfall_bpd

    # --- 4. Duration derived from alt-supplier lead times ---
    if allocations_for_lead_time:
        estimated_replacement_days = math.ceil(
            weighted_average_lead_time(allocations_for_lead_time)
        )
    else:
        estimated_replacement_days = 0  # no alternative supply available at all

    # --- 5. NOW calculate the actual barrel loss, using that derived duration ---
    ramp_up_loss_bbl = daily_shortfall_bpd * estimated_replacement_days
    chronic_loss_bbl = residual_daily_shortfall_bpd * CHRONIC_EXPOSURE_WINDOW_DAYS
    gross_loss_bbl = ramp_up_loss_bbl + chronic_loss_bbl

    inventory_offset_bbl = min(STRATEGIC_RESERVE_BARRELS, gross_loss_bbl)
    net_gap_bbl = max(0, gross_loss_bbl - inventory_offset_bbl)

    # --- 6. Economic estimate ---
    supply_drop_pct = (daily_shortfall_bpd / india_total_bpd * 100) if india_total_bpd else 0
    estimated_price_spike_pct = round(supply_drop_pct * PRICE_ELASTICITY_OF_SUPPLY, 2)

    return {
        "scenario": {
            "corridor": corridor_name,
            "severity": severity,
        },
        "baseline": {
            "india_total_import_bpd": round(india_total_bpd),
            "corridor_dependency_share": round(corridor_dependency_share, 4),
            "corridor_dependent_bpd": round(corridor_dependent_bpd),
            "daily_shortfall_bpd": round(daily_shortfall_bpd),
        },
        "affected_suppliers": affected_suppliers,
        "alternative_sources": alternative_sources,
        "derived_lead_time": {
            "estimated_replacement_days": estimated_replacement_days,
            "covered_daily_bpd": round(covered_daily_bpd),
            "residual_daily_shortfall_bpd": round(residual_daily_shortfall_bpd),
            "note": "Duration is derived from the barrel-weighted average shipping "
                    "lead-time of the alternative suppliers actually used to cover "
                    "the daily shortfall - not a fixed lookup table.",
        },
        "supply_impact": {
            "ramp_up_loss_bbl": round(ramp_up_loss_bbl),
            "chronic_loss_bbl": round(chronic_loss_bbl),
            "gross_loss_bbl": round(gross_loss_bbl),
            "inventory_offset_bbl": round(inventory_offset_bbl),
            "net_gap_bbl": round(net_gap_bbl),
        },
        "economic_estimates": {
            "supply_drop_pct": round(supply_drop_pct, 2),
            "price_elasticity_assumption": PRICE_ELASTICITY_OF_SUPPLY,
            "estimated_crude_price_spike_pct": estimated_price_spike_pct,
            "note": "Modelled estimate based on supply shock and assumed elasticity; "
                    "not an official forecast.",
        },
    }


def run_full_pipeline(phase1_output: dict):
    baseline = load_baseline_oil_balance()
    corridor_data = load_supplier_corridor_dependency()
    supplier_breakdown = corridor_data["supplier_breakdown"]
    india_total_bpd = baseline["latest_year_bpd"]

    report = {}
    for corridor_key, p1 in phase1_output.items():
        corridor_name = CORRIDOR_KEY_TO_NAME.get(corridor_key, "UNMAPPED")

        if corridor_name is None:
            report[corridor_key] = {
                "phase1_context": p1,
                "note": "No crude-oil import dependency data available for this "
                        "corridor - cannot compute barrel-level impact.",
            }
            continue
        if corridor_name == "UNMAPPED":
            report[corridor_key] = {
                "phase1_context": p1,
                "note": f"corridor_key '{corridor_key}' not mapped - add it to CORRIDOR_KEY_TO_NAME.",
            }
            continue

        risk_score = p1.get("risk_score", 0)
        traffic_halted = p1.get("traffic_halted", False)
        severity = derive_severity_from_risk(risk_score, traffic_halted)

        corridor_result = evaluate_corridor(corridor_name, severity, supplier_breakdown, india_total_bpd)

        report[corridor_key] = {
            "phase1_context": p1,
            **corridor_result,
        }

    return {
        "baseline_year": baseline["latest_year"],
        "india_total_import_bpd": round(india_total_bpd),
        "corridors": report,
    }


if __name__ == "__main__":
    import json
    PHASE1_SAMPLE = {
        "strait_of_hormuz": {"name": "Strait of Hormuz", "risk_score": 40, "traffic_halted": False},
        "red_sea": {"name": "Red Sea", "risk_score": 80, "traffic_halted": True},
        "cape_of_good_hope": {"name": "Cape of Good Hope", "risk_score": 20, "traffic_halted": False},
    }
    print(json.dumps(run_full_pipeline(PHASE1_SAMPLE), indent=2))