import json
import os
import pandas as pd
from src.models.risk_agent import calculate_global_risk, master_routes # Importing Phase 1

def generate_dynamic_baseline() -> dict:
    """
    Ingests raw UN Comtrade & PPAC CSV files to dynamically build the supply chain baseline.
    No hardcoding.
    """
    # Define file paths (assuming a 'data' folder at the root level)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    imports_path = os.path.join(base_dir, 'india_crude_imports_by_supplier_2022_2025.csv')
    map_path = os.path.join(base_dir, 'supplier_corridor_map.csv')
    
    try:
        df_imports = pd.read_csv(imports_path)
        df_map = pd.read_csv(map_path)
    except Exception as e:
        print(f"Error loading CSV files. Ensure they are in the 'data' folder. Details: {e}")
        return {}

    # Standardize country names to match between datasets
    df_imports['supplier_country'] = df_imports['supplier_country'].replace({
        'Russian Federation': 'Russia',
        'USA': 'United States'
    })

    # Filter for the most recent complete year (e.g., 2023) to establish a realistic baseline
    df_latest = df_imports[df_imports['year'] == 2023]
    total_kg = df_latest.groupby('supplier_country')['net_weight_kg'].sum().reset_index()

    # Convert Kg to Barrels per Day (BPD)
    # Formula: (Kg / 1000) * 7.33 (approx bbl/tonne) / 365 days
    total_kg['bpd'] = (total_kg['net_weight_kg'] / 1000 * 7.33) / 365
    total_kg['bpd'] = total_kg['bpd'].round(0).astype(int)

    # Merge with the corridor map
    merged = pd.merge(total_kg, df_map, on='supplier_country', how='inner')

    # Standardize corridor keys to match Phase 1 LLM output
    def standardize_corridor(name):
        name = str(name).lower()
        if "hormuz" in name: return "strait_of_hormuz"
        if "red sea" in name or "suez" in name: return "red_sea"
        if "cape" in name: return "cape_of_good_hope"
        return "other"

    suppliers = []
    for _, row in merged.iterrows():
        # Only include major suppliers (e.g., > 20,000 bpd) to keep the graph focused
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

def run_simulation(live_risk_report: dict, simulation_days: int = 15) -> dict:
    """
    Phase 2 Engine: Evaluates the live Phase 1 risk scores against the dynamic baseline.
    """
    baseline = generate_dynamic_baseline()
    if not baseline:
        return {"error": "Failed to generate dynamic baseline from CSVs."}

    total_baseline_bpd = baseline.get("total_demand_bpd", 0)
    suppliers = baseline.get("suppliers", [])
    
    total_shortfall_bpd = 0
    affected_suppliers = []
    triggered_corridors = []

    # 1. Check which corridors from Phase 1 breached the threshold
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

    # 2. Calculate the barrel deficit by mapping suppliers to the severed corridors
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

    # 3. Aggregate Phase 2 final metrics
    total_barrels_lost = total_shortfall_bpd * simulation_days
    surviving_bpd = total_baseline_bpd - total_shortfall_bpd
    
    supply_drop_pct = (total_shortfall_bpd / total_baseline_bpd) * 100 if total_baseline_bpd > 0 else 0
    estimated_price_spike_pct = supply_drop_pct * baseline["economic_multipliers"]["price_elasticity_of_supply"]

    return {
        "simulation_parameters": {
            "duration_days": simulation_days,
            "triggered_corridors": triggered_corridors
        },
        "impact_metrics": {
            "total_baseline_demand_bpd": total_baseline_bpd,
            "surviving_supply_bpd": surviving_bpd,
            "daily_shortfall_bpd": total_shortfall_bpd,
            "total_barrels_lost": total_barrels_lost,
            "affected_suppliers": affected_suppliers
        },
        "economic_estimates": {
            "estimated_crude_price_spike_pct": round(estimated_price_spike_pct, 2)
        }
    }

# --- TEST THE FULL PIPELINE (PHASE 1 -> PHASE 2) ---
if __name__ == "__main__":
    # Ensure pandas is installed: pip install pandas
    print("Initiating full autonomous pipeline test...")
    
    # 1. Run Phase 1 (Live Geopolitical LLM Parsing)
    print("Running Phase 1 (Fetching live news & generating risk scores)...")
    live_risk_data = calculate_global_risk(master_routes)
    
    # 2. Run Phase 2 (Dynamic CSV baseline ingestion + Disruption Math)
    print("Running Phase 2 (Ingesting UN Comtrade CSVs & simulating impact)...")
    final_output = run_simulation(live_risk_report=live_risk_data, simulation_days=15)
    
    print("\n=== FINAL PHASE 2 API PAYLOAD ===")
    print(json.dumps(final_output, indent=2))