import json
import os
import numpy as np
from scipy.optimize import linprog

def load_reserves_data() -> dict:
    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'national_reserves.json')),
        os.path.abspath(os.path.join(os.getcwd(), 'backend', 'data', 'national_reserves.json')),
        os.path.abspath(os.path.join(os.getcwd(), 'data', 'national_reserves.json'))
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    return {}

def run_spr_optimization(daily_deficit_curve: list[int]) -> dict:
    reserves = load_reserves_data()
    if not reserves or not daily_deficit_curve:
        return {"status": "No active deficit or reserves file missing."}

    isprl = reserves["strategic_petroleum_reserves_isprl"]
    omc = reserves["commercial_buffer_omc"]
    caverns = isprl["caverns"]
    num_caverns = len(caverns)

    T = len(daily_deficit_curve)
    num_vars_per_day = num_caverns + 2  # [Caverns..., OMC, Unmet]
    total_vars = num_vars_per_day * T

    c = []
    bounds = []

    # Loop day-by-day to maintain perfect variable ordering alignment
    for t in range(T):
        # 1. Cavern discharge variables
        for cavern in caverns:
            c.append(1.0)
            bounds.append((0, cavern["max_discharge_rate_bpd"]))
            
        # 2. OMC commercial buffer variable
        c.append(2.0)
        bounds.append((0, omc["max_commercial_drawdown_rate_bpd"]))
        
        # 3. Unmet deficit variable
        c.append(500.0)
        bounds.append((0, None))

    # Equality Constraints: Caverns + OMC + Unmet == Deficit for each day
    A_eq = np.zeros((T, total_vars))
    b_eq = []
    for t in range(T):
        start_idx = t * num_vars_per_day
        for c_idx in range(num_caverns):
            A_eq[t, start_idx + c_idx] = 1.0
        A_eq[t, start_idx + num_caverns] = 1.0     # OMC
        A_eq[t, start_idx + num_caverns + 1] = 1.0 # Unmet
        b_eq.append(daily_deficit_curve[t])

    # Inequality Constraints: Cumulative stock capacity limits across all days
    A_ub = np.zeros((num_caverns + 1, total_vars))
    b_ub = []
    
    for c_idx, cavern in enumerate(caverns):
        for t in range(T):
            A_ub[c_idx, t * num_vars_per_day + c_idx] = 1.0
        b_ub.append(cavern["current_stock_barrels"])

    omc_idx = num_caverns
    for t in range(T):
        A_ub[num_caverns, t * num_vars_per_day + omc_idx] = 1.0
    b_ub.append(omc["estimated_usable_buffer_barrels"])

    # Run LP solver
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
    if not res.success:
        res = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='interior-point')

    if not res.success:
        return {"error": "Optimization solver failed to converge.", "details": res.message}

    cavern_schedules = [[] for _ in range(num_caverns)]
    omc_schedule = []
    unmet_schedule = []

    for t in range(T):
        start_idx = t * num_vars_per_day
        for c_idx in range(num_caverns):
            cavern_schedules[c_idx].append(int(res.x[start_idx + c_idx]))
        omc_schedule.append(int(res.x[start_idx + num_caverns]))
        unmet_schedule.append(int(res.x[start_idx + num_caverns + 1]))

    cavern_breakdown = []
    total_spr_drawn = 0
    for c_idx, cavern in enumerate(caverns):
        drawn = sum(cavern_schedules[c_idx])
        total_spr_drawn += drawn
        cavern_breakdown.append({
            "location": cavern["location"],
            "barrels_drawn": drawn,
            "remaining_stock_barrels": cavern["current_stock_barrels"] - drawn,
            "connected_refinery": cavern["primary_connected_refinery"]
        })

    total_omc_drawn = sum(omc_schedule)
    total_unmet = sum(unmet_schedule)
    ending_spr_stock = isprl["current_stock_barrels"] - total_spr_drawn

    return {
        "status": "Reserve Drawdown Optimization Successful",
        "crisis_duration_days": T,
        "isprl_summary": {
            "initial_stock_barrels": isprl["current_stock_barrels"],
            "total_drawn_barrels": total_spr_drawn,
            "ending_stock_barrels": ending_spr_stock,
            "ending_fill_pct": round((ending_spr_stock / isprl["total_capacity_barrels"]) * 100, 1),
            "caverns_operation": cavern_breakdown
        },
        "omc_commercial_summary": {
            "initial_stock_barrels": omc["estimated_usable_buffer_barrels"],
            "total_drawn_barrels": total_omc_drawn,
            "ending_stock_barrels": omc["estimated_usable_buffer_barrels"] - total_omc_drawn
        },
        "total_unmet_shortfall_barrels": total_unmet,
        "daily_drawdown_schedule": [
            {
                "day": t + 1,
                "target_deficit_bpd": daily_deficit_curve[t],
                "cavern_drawdowns_bpd": {caverns[c_idx]["location"]: cavern_schedules[c_idx][t] for c_idx in range(num_caverns)},
                "omc_drawdown_bpd": omc_schedule[t],
                "unmet_shortfall_bpd": unmet_schedule[t]
            }
            for t in range(T)
        ]
    }