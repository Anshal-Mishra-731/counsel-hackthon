import json
import os
from scipy.optimize import linprog

def load_alternative_suppliers() -> list:
    """Robustly loads alternative supplier candidates from data/alternative_suppliers.json."""
    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'alternative_suppliers.json')),
        os.path.abspath(os.path.join(os.getcwd(), 'backend', 'data', 'alternative_suppliers.json')),
        os.path.abspath(os.path.join(os.getcwd(), 'data', 'alternative_suppliers.json'))
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    return data.get("alternative_suppliers", [])
            except Exception:
                continue
    print("Error: alternative_suppliers.json could not be located.")
    return []

def run_procurement_optimization(target_deficit_bpd: int, live_risk_report: dict) -> dict:
    candidates = load_alternative_suppliers()
    if not candidates:
        return {"error": "Alternative suppliers configuration missing."}

    c = []
    bounds = []

    for cand in candidates:
        corridor = cand["corridor"]
        risk = live_risk_report.get(corridor, {"risk_score": 10, "traffic_halted": False})
        
        if risk.get("traffic_halted", False) or risk.get("risk_score", 0) >= 65:
            c.append(1e6)
            bounds.append((0, 0))
        else:
            risk_penalty = risk.get("risk_score", 0) * 0.1 
            unit_cost = cand["base_cost_usd_bbl"] + cand["freight_cost_usd_bbl"] + risk_penalty
            c.append(unit_cost)
            bounds.append((0, cand["spare_capacity_bpd"]))

    A_ub = [[-1.0] * len(candidates)]
    b_ub = [-target_deficit_bpd]

    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    if not res.success:
        res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='interior-point')

    if not res.success:
        return {"error": "Optimization Failed to converge."}

    reallocations = []
    max_transit_days = 0
    total_new_cost = 0
    total_allocated_volume = 0

    for i, allocated_bpd in enumerate(res.x):
        if allocated_bpd > 1:
            cand = candidates[i]
            allocated_bpd = int(allocated_bpd)
            landed_price = round(c[i], 2)
            
            total_new_cost += allocated_bpd * landed_price
            max_transit_days = max(max_transit_days, cand["transit_days"])
            total_allocated_volume += allocated_bpd
            
            reallocations.append({
                "supplier": cand["supplier"],
                "corridor_used": cand["corridor"],
                "crude_grade": cand["crude_grade"],
                "assay_compatibility_score": cand["assay_compatibility_score"],
                "allocated_bpd": allocated_bpd,
                "transit_lead_time_days": cand["transit_days"],
                "landed_cost_usd_per_bbl": landed_price
            })

    blended_avg_price = round(total_new_cost / total_allocated_volume, 2) if total_allocated_volume > 0 else 0
    required_vlccs = round(total_allocated_volume * max_transit_days / 2000000, 1)

    return {
        "status": "Optimal Supply Re-allocation Found",
        "target_deficit_bpd": target_deficit_bpd,
        "critical_transit_lead_time_days": max_transit_days,
        "blended_reallocation_cost_usd_bbl": blended_avg_price,
        "logistics_execution": {
            "estimated_vlcc_vessels_required": int(required_vlccs) + 1,
            "average_freight_rate_index_usd_day": 52000,
            "primary_discharge_ports": ["Mundra (Gujarat)", "Sikka (Jamnagar)", "Paradip (Odisha)"]
        },
        "reallocation_plan": reallocations
    }