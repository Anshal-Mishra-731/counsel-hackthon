"""
Real-world (approximate) tanker transit time from each supplier country
to major Indian ports. These are PUBLIC, well-known shipping-distance
based estimates (typical VLCC/Suezmax cruising speed ~13-14 knots),
used to answer: "if we switch to this alternative supplier, how many
days until that oil actually arrives in India?"

These are modelled assumptions, not live AIS/vessel-tracking data.
Adjust freely - this is the ONE place that controls lead-time logic.
"""

# country -> average sea transit days to India
SUPPLIER_LEAD_TIME_DAYS = {
    # Gulf / Middle East (short haul via Hormuz or Gulf of Oman)
    "Iraq": 8,
    "Saudi Arabia": 9,
    "United Arab Emirates": 5,
    "Kuwait": 9,
    "Iran": 5,
    "Oman": 5,

    # Russia (via Suez / Black Sea route)
    "Russia": 18,

    # West Africa
    "Nigeria": 18,
    "Angola": 20,

    # Americas (longest haul, via Cape of Good Hope or Panama/Suez)
    "United States": 25,
    "Canada": 26,
    "Brazil": 28,
    "Colombia": 27,
    "Venezuela": 27,
}

DEFAULT_LEAD_TIME_DAYS = 0  # fallback for any supplier not listed above


def get_lead_time_days(supplier_country: str) -> int:
    return SUPPLIER_LEAD_TIME_DAYS.get(supplier_country, DEFAULT_LEAD_TIME_DAYS)


def weighted_average_lead_time(allocations: list[dict]) -> float:
    """
    allocations: list of {"supplier": str, "additional_bpd_allocated": float}
    Returns the barrel-weighted average number of days until the
    combined alternative supply is expected to be flowing.
    """
    total_bpd = sum(a["additional_bpd_allocated"] for a in allocations)
    if total_bpd <= 0:
        return 0.0

    weighted_days = sum(
        a["additional_bpd_allocated"] * get_lead_time_days(a["supplier"])
        for a in allocations
    )
    return weighted_days / total_bpd