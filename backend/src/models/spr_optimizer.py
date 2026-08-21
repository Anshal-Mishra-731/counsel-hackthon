import json
import os
import numpy as np
from scipy.optimize import linprog

def load_reserves_data() -> dict:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    reserves_path = os.path.join(base_dir, 'national_reserves.json')
    try:
        with open(reserves_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading national_reserves.json: {e}")
        return {}

def run_spr_optimization(daily_deficit_curve: list[int]) -> dict:
    reserves = load_reserves_data()
    if not reserves or not daily_deficit_curve:
        return {"status": "No active deficit or reserves file missing."}

    isprl = reserves["strategic_petroleum_reserves_isprl"]
    omc = reserves["commercial_buffer_omc"]

    T = len(daily_deficit_curve)
    num_vars = 3 * T 

    c = []
    bounds = []

    for t in range(T):
        c.append(1.0 + 0.0001 * t)
        bounds.append((0, isprl["max_combined_discharge_rate_bpd"]))

    for t in range(T):
        c.append(2.0 + 0.0001 * t)
        bounds.append((0, omc["max_commercial_drawdown_rate_bpd"]))

    for t in range(T):
        c.append(1000.0) 
        bounds.append((0, None))

    A_eq = np.zeros((T, num_vars))
    b_eq = []
    for t in range(T):
        A_eq[t, t] = 1.0           
        A_eq[t, T + t] = 1.0       
        A_eq[t, 2 * T + t] = 1.0   
        b_eq.append(daily_deficit_curve[t])

    A_ub = np.zeros((2, num_vars))
    A_ub[0, 0:T] = 1.0
    A_ub[1, T:2 * T] = 1.0
    b_ub = [
        isprl["current_stock_barrels"],
        omc["estimated_usable_buffer_barrels"]
    ]

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if not res.success:
        return {"error": "Optimization solver failed to converge."}

    spr_schedule = [int(x) for x in res.x[0:T]]
    omc_schedule = [int(x) for x in res.x[T:2 * T]]
    unmet_schedule = [int(x) for x in res.x[2 * T:]]

    total_spr_drawn = sum(spr_schedule)
    total_omc_drawn = sum(omc_schedule)
    total_unmet = sum(unmet_schedule)
    ending_spr_stock = isprl["current_stock_barrels"] - total_spr_drawn

    cavern_breakdown = []
    for cavern in isprl["caverns"]:
        ratio = cavern["max_discharge_rate_bpd"] / isprl["max_combined_discharge_rate_bpd"]
        drawn = int(total_spr_drawn * ratio)
        cavern_breakdown.append({
            "location": cavern["location"],
            "barrels_drawn": drawn,
            "remaining_stock_barrels": cavern["current_stock_barrels"] - drawn,
            "connected_refinery": cavern["primary_connected_refinery"]
        })

    payload = {
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
                "isprl_drawdown_bpd": spr_schedule[t],
                "omc_drawdown_bpd": omc_schedule[t],
                "unmet_shortfall_bpd": unmet_schedule[t]
            }
            for t in range(T)
        ]
    }

    # === NEW: DOOMSDAY THRESHOLD LOGIC ===
    if total_unmet > 0:
        payload["status"] = "CRITICAL FAILURE: Reserves Exhausted. Rationing Protocols Activated."
        payload["national_rationing_protocols"] = {
            "alert_level": "RED (Doomsday Scenario)",
            "rationale": f"The national reserves and commercial buffers were entirely depleted before the {T}-day transit gap could close. {total_unmet:,} barrels remain unfulfilled.",
            "immediate_actions": [
                {"tier": 1, "sector": "Civilian Mobility", "action": "Institute immediate odd/even license plate rationing for private vehicles. Halt non-essential domestic aviation."},
                {"tier": 2, "sector": "Industrial Manufacturing", "action": "Mandate 40% reduction in power allocation to non-essential petrochemical and heavy manufacturing plants."},
                {"tier": 3, "sector": "Protected Infrastructure (Exempt)", "action": "Ring-fence remaining operational crude flows strictly for Defense, Agricultural logistics (tractors/fertilizer), and Emergency Grid Power."}
            ]
        }

    return payload

if __name__ == "__main__":
    # Test a massive Doomsday shortfall (15 million bpd deficit over 30 days) to trigger the threshold
    mock_doomsday_deficit = [15000000] * 30
    print("Testing Phase 4 SPR Optimizer (Doomsday Scenario)...")
    result = run_spr_optimization(mock_doomsday_deficit)
    print(json.dumps(result, indent=2))