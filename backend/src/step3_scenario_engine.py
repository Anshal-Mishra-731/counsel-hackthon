from src.step1_baseline import load_baseline_oil_balance
from src.step2_corridor_mapping import load_supplier_corridor_dependency


MANUAL_CORRIDOR_FIX = {
    "Iran": "Strait of Hormuz"
}

STRATEGIC_RESERVE_BARRELS = 9_500_000


def run_scenario(
    corridor: str,
    duration_days: int,
    severity: float,
):

    if not 0 <= severity <= 1:
        raise ValueError(
            "severity must be between 0 and 1"
        )

    baseline = load_baseline_oil_balance()

    corridor_data = (
        load_supplier_corridor_dependency()
    )

    supplier_breakdown = (
        corridor_data["supplier_breakdown"]
        .copy()
    )

    supplier_breakdown["primary_corridor"] = (
        supplier_breakdown.apply(
            lambda row:
            MANUAL_CORRIDOR_FIX.get(
                row["supplier_country"],
                row["primary_corridor"],
            ),
            axis=1,
        )
    )

    india_total_bpd = (
        baseline["latest_year_bpd"]
    )

    dep_share = (
        supplier_breakdown
        .dropna(subset=["primary_corridor"])
        .groupby("primary_corridor")[
            "share_of_imports"
        ]
        .sum()
    )

    corridor_dependency_share = float(
        dep_share.get(corridor, 0.0)
    )

    corridor_dependent_bpd = (
        india_total_bpd
        * corridor_dependency_share
    )

    daily_loss_bbl = (
        corridor_dependent_bpd
        * severity
    )

    gross_loss_bbl = (
        daily_loss_bbl
        * duration_days
    )

    inventory_offset = min(
        STRATEGIC_RESERVE_BARRELS,
        gross_loss_bbl,
    )

    net_gap_bbl = max(
        0,
        gross_loss_bbl - inventory_offset,
    )

    unaffected = supplier_breakdown[
        supplier_breakdown["primary_corridor"]
        != corridor
    ].copy()

    unaffected = unaffected.sort_values(
        "share_of_imports",
        ascending=False,
    )

    unaffected["current_bpd"] = (
        unaffected["share_of_imports"]
        * india_total_bpd
    )

    unaffected["max_additional_bpd"] = (
        unaffected["current_bpd"]
        * 0.30
    )

    alt_sources = []

    remaining = net_gap_bbl

    for _, row in unaffected.iterrows():

        if remaining <= 0:
            break

        headroom_over_duration = (
            row["max_additional_bpd"]
            * duration_days
        )

        take = min(
            headroom_over_duration,
            remaining,
        )

        if take > 0:

            alt_sources.append(
                {
                    "supplier":
                        row["supplier_country"],

                    "corridor":
                        row["primary_corridor"],

                    "additional_barrels_offered":
                        round(take),
                }
            )

            remaining -= take

    residual_shortage_bbl = max(
        0,
        remaining,
    )

    return {
        "scenario": {
            "corridor": corridor,
            "duration_days": duration_days,
            "severity": severity,
        },

        "baseline": {
            "india_total_import_bpd":
                round(india_total_bpd),

            "corridor_dependency_share":
                round(
                    corridor_dependency_share,
                    4,
                ),

            "corridor_dependent_bpd":
                round(
                    corridor_dependent_bpd
                ),
        },

        "supply_impact": {
            "daily_loss_bbl":
                round(daily_loss_bbl),

            "gross_loss_bbl":
                round(gross_loss_bbl),

            "inventory_offset_bbl":
                round(inventory_offset),

            "net_gap_bbl":
                round(net_gap_bbl),
        },

        "alternative_sources":
            alt_sources,

        "residual_shortage_bbl":
            round(residual_shortage_bbl),
    }


if __name__ == "__main__":

    import json

    result = run_scenario(
        corridor="Strait of Hormuz",
        duration_days=15,
        severity=0.80,
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )