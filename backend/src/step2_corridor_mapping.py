import pandas as pd


NAME_FIXES = {
    "Russian Federation": "Russia",
    "USA": "United States",
}


def load_supplier_corridor_dependency(
    supplier_csv="data/india_crude_imports_by_supplier_2022_2025.csv",
    corridor_map_csv="data/supplier_corridor_map.csv",
):

    imports = pd.read_csv(supplier_csv)
    corridor_map = pd.read_csv(corridor_map_csv)

    imports["supplier_country"] = (
        imports["supplier_country"]
        .replace(NAME_FIXES)
    )

    latest_year = imports["year"].max()

    latest = imports[
        imports["year"] == latest_year
    ].copy()

    supplier_totals = (
        latest
        .groupby("supplier_country")["qty_kg"]
        .sum()
        .reset_index()
    )

    total_all = supplier_totals["qty_kg"].sum()

    supplier_totals["share_of_imports"] = (
        supplier_totals["qty_kg"] / total_all
    )

    merged = supplier_totals.merge(
        corridor_map[
            [
                "supplier_country",
                "primary_corridor",
                "base_risk_exposure",
            ]
        ],
        on="supplier_country",
        how="left",
    )

    unmapped = merged[
        merged["primary_corridor"].isna()
    ]["supplier_country"].tolist()

    corridor_dependency = (
        merged
        .dropna(subset=["primary_corridor"])
        .groupby("primary_corridor")[
            "share_of_imports"
        ]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    return {
        "latest_year": int(latest_year),
        "supplier_breakdown": merged,
        "corridor_dependency": corridor_dependency,
        "unmapped_suppliers": unmapped,
    }


if __name__ == "__main__":

    result = load_supplier_corridor_dependency()

    print(
        f"Latest year in data: "
        f"{result['latest_year']}\n"
    )

    print(
        "=== Corridor-wise dependency ==="
    )

    print(
        result["corridor_dependency"]
        .to_string(index=False)
    )

    print(
        "\n=== Unmapped suppliers ==="
    )

    print(
        result["unmapped_suppliers"]
    )