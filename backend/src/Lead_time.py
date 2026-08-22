def get_lead_time_days(supplier, corridor=None):
    lead_times = {
        "Azerbaijan": 0,
        "Kazakhstan": 0,
        "Iran": 5,
        "Oman": 5,
        "United Arab Emirates": 5,
        "Iraq": 8,
        "Kuwait": 9,
        "Saudi Arabia": 9,
        "Nigeria": 18,
        "Russia": 18,
        "Angola": 20,
        "United States": 25,
        "Canada": 26,
        "Colombia": 27,
        "Venezuela": 27,
        "Brazil": 28,
    }
    return lead_times.get(supplier, 20)


def weighted_average_lead_time(suppliers):
    total_bpd = 0
    weighted_days = 0

    for item in suppliers:
        bpd = item.get("additional_bpd_offered", 0)
        days = item.get("lead_time_days")

        if days is None:
            days = get_lead_time_days(
                item.get("supplier"),
                item.get("corridor"),
            )

        if bpd > 0:
            weighted_days += bpd * days
            total_bpd += bpd

    return round(weighted_days / total_bpd) if total_bpd else 0
