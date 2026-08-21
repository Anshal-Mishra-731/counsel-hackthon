"""
India's baseline crude oil demand (bpd), from PPAC monthly import data.
"""
import pandas as pd

MT_TO_BARRELS = 7.33


def load_baseline_oil_balance(path="data/pt_import_export_combined.csv"):
    df = pd.read_csv(path)

    crude_imports = df[
        (df["Flow"] == "IMPORT")
        & (df["Category"] == "CRUDE OIL")
        & (df["Product"] == "Crude Oil")
        & (df["Month"].str.upper() != "TOTAL")   # exclude yearly TOTAL rows
    ].copy()

    crude_imports["barrels"] = crude_imports["Value_000_MT"] * 1000 * MT_TO_BARRELS

    avg_monthly_barrels = crude_imports["barrels"].mean()
    avg_daily_bpd = avg_monthly_barrels / 30.44

    latest_year = sorted(crude_imports["Year"].unique())[-1]
    latest = crude_imports[crude_imports["Year"] == latest_year]
    latest_avg_daily_bpd = latest["barrels"].mean() / 30.44

    return {
        "avg_all_years_bpd": round(avg_daily_bpd),
        "latest_year": latest_year,
        "latest_year_bpd": round(latest_avg_daily_bpd),
        "months_of_data": len(crude_imports),
    }


if __name__ == "__main__":
    print(load_baseline_oil_balance())