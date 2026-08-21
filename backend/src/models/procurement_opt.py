import json
import math
from scipy.optimize import linprog

def run_procurement_optimization(target_deficit_bpd: int, live_risk_report: dict) -> dict:
    """
    Phase 3 Engine: Solves a Linear Programming model to re-allocate disrupted crude 
    to alternative global suppliers across unblocked corridors.
    """
    # 1. Alternative Supplier Matrix (Global Spare Capacity & Route profiles)
    candidates = [
        {
            "supplier": "Russia (Cape Route Diversion)", 
            "corridor": "cape_of_good_hope", 
            "spare_capacity_bpd": 1500000, 
            "base_cost_usd_bbl": 70.0, 
            "freight_cost_usd_bbl": 8.5, 
            "transit_days": 32
        },
        {
            "supplier": "Russia (Vladivostok CVMC)", 
            "corridor": "chennai_vladivostok_maritime_corridor", 
            "spare_capacity_bpd": 600000, 
            "base_cost_usd_bbl": 72.0, 
            "freight_cost_usd_bbl": 4.5, 
            "transit_days": 18
        },
        {
            "supplier": "West Africa (Angola/Nigeria)", 
            "corridor": "cape_of_good_hope", 
            "spare_capacity_bpd": 700000, 
            "base_cost_usd_bbl": 78.0, 
            "freight_cost_usd_bbl": 5.0, 
            "transit_days": 22
        },
        {
            "supplier": "United States (Gulf Coast)", 
            "corridor": "cape_of_good_hope", 
            "spare_capacity_bpd": 800000, 
            "base_cost_usd_bbl": 76.0, 
            "freight_cost_usd_bbl": 9.0, 
            "transit_days": 35
        },
        {
            "supplier": "Latin America (Brazil/Guyana)", 
            "corridor": "cape_of_good_hope", 
            "spare_capacity_bpd": 500000, 
            "base_cost_usd_bbl": 75.0, 
            "freight_cost_usd_bbl": 8.0, 
            "transit_days": 28
        },
        {
            "supplier": "Saudi Arabia (Red Sea Yanbu Bypass)", 
            "corridor": "red_sea", 
            "spare_capacity_bpd": 300000, 
            "base_cost_usd_bbl": 77.0, 
            "freight_cost_usd_bbl": 3.0, 
            "transit_days": 8
        }
    ]

    c = []       # Objective Function: Cost per barrel
    bounds = []  # Constraints: 0 to Spare Capacity

    # 2. Build the Linear Equation based on Phase 1 Live Risk
    for cand in candidates:
        corridor = cand["corridor"]
        # Default to safe if not found in Phase 1 output
        risk = live_risk_report.get(corridor, {"risk_score": 10, "traffic_halted": False})
        
        # If the corridor is blocked or critically dangerous, hard-cap the solver from using it
        if risk.get("traffic_halted", False) or risk.get("risk_score", 0) >= 65:
            c.append(1e6) # Punishingly high mathematical cost
            bounds.append((0, 0)) # Capacity restricted to 0
        else:
            # Objective Cost = Base Cost + Freight + (Risk Penalty Factor)
            risk_penalty = risk.get("risk_score", 0) * 0.1 
            unit_cost = cand["base_cost_usd_bbl"] + cand["freight_cost_usd_bbl"] + risk_penalty
            c.append(unit_cost)
            bounds.append((0, cand["spare_capacity_bpd"]))

    # Constraint: Sum of allocated barrels must be >= target_deficit_bpd
    # Scipy expects <= constraints, so we multiply by -1
    A_ub = [[-1.0] * len(candidates)]
    b_ub = [-target_deficit_bpd]

    # 3. Execute the Mathematical Solver
    res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if not res.success:
        return {
            "error": "Optimization Failed. The global supply network cannot fulfill a deficit this massive without unblocking primary routes."
        }

    # 4. Parse the Solver Output
    reallocations = []
    max_transit_days = 0
    total_new_cost = 0

    for i, allocated_bpd in enumerate(res.x):
        if allocated_bpd > 1: # Ignore floating point zeroes
            cand = candidates[i]
            allocated_bpd = int(allocated_bpd)
            landed_price = round(c[i], 2)
            
            total_new_cost += allocated_bpd * landed_price
            max_transit_days = max(max_transit_days, cand["transit_days"])
            
            reallocations.append({
                "supplier": cand["supplier"],
                "corridor_used": cand["corridor"],
                "allocated_bpd": allocated_bpd,
                "transit_lead_time_days": cand["transit_days"],
                "landed_cost_usd_per_bbl": landed_price
            })

    blended_avg_price = round(total_new_cost / target_deficit_bpd, 2) if target_deficit_bpd > 0 else 0

    return {
        "status": "Optimal Supply Re-allocation Found",
        "target_deficit_bpd": target_deficit_bpd,
        "critical_transit_lead_time_days": max_transit_days, # <--- THIS IS THE MAGIC VARIABLE FOR PHASE 2
        "blended_reallocation_cost_usd_bbl": blended_avg_price,
        "reallocation_plan": reallocations
    }

# --- TEST THE PHASE 3 SOLVER DIRECTLY ---
if __name__ == "__main__":
    # Mocking Phase 1 Input: Hormuz is safe, but the Red Sea is blocked.
    mock_risk = {
        "red_sea": {"risk_score": 80, "traffic_halted": True},
        "cape_of_good_hope": {"risk_score": 20, "traffic_halted": False},
        "chennai_vladivostok_maritime_corridor": {"risk_score": 10, "traffic_halted": False}
    }
    
    # Mocking Phase 2 Output: We are short 2.5 Million barrels a day
    mock_deficit = 2500000
    
    print("Executing Phase 3 Procurement Linear Programming...")
    result = run_procurement_optimization(mock_deficit, mock_risk)
    print(json.dumps(result, indent=2))