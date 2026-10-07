import json
import os
import pandas as pd
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.procurement_opt import run_procurement_optimization
from src.models.spr_optimizer import run_spr_optimization

def generate_dynamic_baseline() -> dict:
    """
    Ingests raw UN Comtrade & PPAC CSV files to dynamically build 
    India's empirical supply chain baseline.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    imports_path = os.path.join(base_dir, 'india_crude_imports_by_supplier_2022_2025.csv')
    map_path = os.path.join(base_dir, 'supplier_corridor_map.csv')
    
    try:
        df_imports = pd.read_csv(imports_path)
        df_map = pd.read_csv(map_path)
    except Exception as e:
        print(f"Error loading CSV files from 'data' folder: {e}")
        return {}

    # Standardize country aliases
    df_imports['supplier_country'] = df_imports['supplier_country'].replace({
        'Russian Federation': 'Russia',
        'USA': 'United States'
    })

    # Filter for full-year 2023 baseline
    df_latest = df_imports[df_imports['year'] == 2023]
    total_kg = df_latest.groupby('supplier_country')['net_weight_kg'].sum().reset_index()

    # Convert Kg to BPD: (Kg / 1000) * 7.33 (bbl/MT) / 365 days
    total_kg['bpd'] = ((total_kg['net_weight_kg'] / 1000 * 7.33) / 365).round(0).astype(int)

    merged = pd.merge(total_kg, df_map, on='supplier_country', how='inner')

    def standardize_corridor(name):
        name = str(name).lower()
        if "hormuz" in name: return "strait_of_hormuz"
        if "red sea" in name or "suez" in name: return "red_sea"
        if "cape" in name: return "cape_of_good_hope"
        if "malacca" in name: return "strait_of_malacca"
        if "vladivostok" in name or "eastern maritime" in name: return "chennai_vladivostok_maritime_corridor"
        return "direct_ocean"

    suppliers = []
    for _, row in merged.iterrows():
        if row['bpd'] > 20000:
            suppliers.append({
                "country": row['supplier_country'],
                "corridor": standardize_corridor(row['primary_corridor']),
                "daily_volume_bpd": row['bpd'],
                "notes": row['notes']
            })

    total_demand = int((df_latest['net_weight_kg'].sum() / 1000 * 7.33) / 365)

    return {
        "total_demand_bpd": total_demand,
        "suppliers": suppliers,
        "economic_multipliers": {
            "price_elasticity_of_supply": 1.25
        }
    }

def run_simulation(live_risk_report: dict, override_days: int | None = None) -> dict:
    """
    Unified Pipeline Orchestrator (Phase 1 -> 2 -> 3 -> 4):
    1. Evaluates live corridor risks against the UN Comtrade baseline.
    2. Runs Phase 3 Linear Programming to calculate optimal alternative crude routing.
    3. Models a day-by-day staggered replenishment curve.
    4. Runs Phase 4 Linear Programming to optimize ISPRL reserve release.
    5. Estimates macroeconomic shocks and landed costs.
    """
    baseline = generate_dynamic_baseline()
    if not baseline:
        return {"error": "Failed to generate dynamic baseline from CSVs."}

    total_baseline_bpd = baseline.get("total_demand_bpd", 0)
    suppliers = baseline.get("suppliers", [])
    
    total_shortfall_bpd = 0
    affected_suppliers = []
    triggered_corridors = []

    # 1. Identify disrupted corridors
    for corridor_key, metrics in live_risk_report.items():
        if corridor_key.startswith("_") or not isinstance(metrics, dict):
                continue
        is_halted = metrics.get("traffic_halted", False)
        risk_score = metrics.get("risk_score", 0)
        
        if is_halted or risk_score >= 60:
            severity_pct = 1.0 if is_halted else (risk_score / 100.0)
            triggered_corridors.append({
                "corridor": corridor_key,
                "severity_pct": round(severity_pct * 100, 1),
                "reason": metrics.get("summary", "")
            })

    # 2. Map severed corridors to supplier shortfalls
    for supplier in suppliers:
        for trigger in triggered_corridors:
            if trigger["corridor"] == supplier["corridor"]:
                severity = trigger["severity_pct"] / 100.0
                lost_bpd = int(supplier["daily_volume_bpd"] * severity)
                
                total_shortfall_bpd += lost_bpd
                affected_suppliers.append({
                    "country": supplier["country"],
                    "normal_bpd": supplier["daily_volume_bpd"],
                    "lost_bpd": lost_bpd,
                    "chokepoint_blocked": trigger["corridor"]
                })

    # 3. Phase 3: Procurement & Re-allocation LP Optimization
    procurement_solution = {}
    reallocations = []
    if total_shortfall_bpd > 0:
        procurement_solution = run_procurement_optimization(
            target_deficit_bpd=total_shortfall_bpd, 
            live_risk_report=live_risk_report
        )
        reallocations = procurement_solution.get("reallocation_plan", [])
        calculated_lead_time = procurement_solution.get("critical_transit_lead_time_days", 15)
    else:
        calculated_lead_time = 0

    effective_duration_days = override_days if override_days is not None else calculated_lead_time

    # 4. Staggered Supply Arrival & Daily Deficit Curve Modeling
    daily_unmet_profile = []
    cumulative_lost_staggered = 0
    active_deficit = total_shortfall_bpd
    
    # Map scheduled arrivals by day
    day_arrivals = {}
    for item in reallocations:
        d = item.get("transit_lead_time_days", effective_duration_days)
        day_arrivals[d] = day_arrivals.get(d, 0) + item.get("allocated_bpd", 0)

    for day in range(1, effective_duration_days + 1):
        if day in day_arrivals:
            active_deficit = max(0, active_deficit - day_arrivals[day])
        daily_unmet_profile.append(active_deficit)
        cumulative_lost_staggered += active_deficit

    # 5. Phase 4: SPR Drawdown Linear Programming Optimization
    spr_solution = {}
    if daily_unmet_profile:
        spr_solution = run_spr_optimization(daily_deficit_curve=daily_unmet_profile)

    # 6. Macroeconomic Price Shock Modeling
    surviving_bpd = total_baseline_bpd - total_shortfall_bpd
    supply_drop_pct = (total_shortfall_bpd / total_baseline_bpd) * 100 if total_baseline_bpd > 0 else 0
    estimated_price_spike_pct = supply_drop_pct * baseline["economic_multipliers"]["price_elasticity_of_supply"]

    return {
        "simulation_parameters": {
            "lead_time_source": "Phase 3 LP Solver (Dynamic)" if override_days is None else "User Override",
            "duration_days": effective_duration_days,
            "triggered_corridors": triggered_corridors
        },
        "impact_metrics": {
            "total_baseline_demand_bpd": total_baseline_bpd,
            "surviving_supply_bpd": surviving_bpd,
            "initial_daily_shortfall_bpd": total_shortfall_bpd,
            "cumulative_barrels_lost_staggered": cumulative_lost_staggered,
            "affected_suppliers": affected_suppliers
        },
        "phase3_procurement_optimization": procurement_solution,
        "phase4_spr_drawdown_optimization": spr_solution,
        "economic_estimates": {
            "estimated_crude_price_spike_pct": round(estimated_price_spike_pct, 2),
            "disclaimer": "Modelled estimates based on historical supply-price elasticity."
        }
    }

if __name__ == "__main__":
    print("Initiating full autonomous pipeline test (Phase 1 -> 2 -> 3 -> 4)...")
    
    # 1. Phase 1: Live news risk scores
    print("\n--- Running Phase 1 (Geopolitical News Risk Engine) ---")
    live_risk = calculate_global_risk(master_routes)
    
    # 2. Phase 2-4: Disruption, Reallocation, and SPR Optimization
    print("\n--- Running Phase 2, 3, & 4 Integrated Optimization ---")
    result = run_simulation(live_risk_report=live_risk)
    
    print("\n=== COMPLETE SYSTEM PAYLOAD ===")
    print(json.dumps(result, indent=2))