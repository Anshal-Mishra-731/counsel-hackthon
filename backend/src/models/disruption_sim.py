import json
import os
import pandas as pd
from src.models.risk_agent import calculate_global_risk, master_routes
from src.models.procurement_opt import run_procurement_optimization

def generate_dynamic_baseline() -> dict:
    """
    Ingests raw UN Comtrade & PPAC CSV files to dynamically build the supply chain baseline.
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

    # Standardize country names between datasets
    df_imports['supplier_country'] = df_imports['supplier_country'].replace({
        'Russian Federation': 'Russia',
        'USA': 'United States'
    })

    # 2023 full-year baseline
    df_latest = df_imports[df_imports['year'] == 2023]
    total_kg = df_latest.groupby('supplier_country')['net_weight_kg'].sum().reset_index()

    # Convert Kg to BPD: (Kg / 1000) * 7.33 / 365
    total_kg['bpd'] = (total_kg['net_weight_kg'] / 1000 * 7.33) / 365
    total_kg['bpd'] = total_kg['bpd'].round(0).astype(int)

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
    Phase 2 + Phase 3 Orchestrator:
    1. Evaluates daily shortfall from Phase 1 risk scores.
    2. Calls Phase 3 LP Solver to find optimal rerouting and dynamic transit lead time.
    3. Calculates total barrel deficit and macroeconomic impact over that exact lead time window.
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

    # 3. Dynamic Lead-Time Calculation (Calling Phase 3 LP Solver)
    procurement_solution = {}
    if total_shortfall_bpd > 0:
        procurement_solution = run_procurement_optimization(
            target_deficit_bpd=total_shortfall_bpd, 
            live_risk_report=live_risk_report
        )
        calculated_days = procurement_solution.get("critical_transit_lead_time_days", 15)
    else:
        calculated_days = 0

    # Allow optional manual user override from dashboard, otherwise use LP solver lead time
    effective_duration_days = override_days if override_days is not None else calculated_days

    # 4. Compute final cumulative deficits & price shocks
    total_barrels_lost = total_shortfall_bpd * effective_duration_days
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
            "daily_shortfall_bpd": total_shortfall_bpd,
            "total_barrels_lost": total_barrels_lost,
            "affected_suppliers": affected_suppliers
        },
        "procurement_optimization_phase3": procurement_solution,
        "economic_estimates": {
            "estimated_crude_price_spike_pct": round(estimated_price_spike_pct, 2),
            "disclaimer": "Modelled estimates based on historical supply-price elasticity."
        }
    }

if __name__ == "__main__":
    print("Initiating full autonomous pipeline test (Phase 1 -> Phase 2 & 3)...")
    
    # 1. Fetch live risk scores
    print("Running Phase 1...")
    live_risk = calculate_global_risk(master_routes)
    
    # 2. Run integrated Phase 2 & Phase 3 pipeline
    print("Running Phase 2 & 3...")
    result = run_simulation(live_risk_report=live_risk)
    
    print("\n=== INTEGRATED PIPELINE OUTPUT ===")
    print(json.dumps(result, indent=2))