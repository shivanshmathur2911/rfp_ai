import pandas as pd

# -------------------------------------------------
# CONFIG: which fields participate in spec matching
# (SKU column name, RFP spec key)
# -------------------------------------------------
MATCH_FIELDS = [
    ("Voltage_kV", "voltage_kV"),
    ("Conductor", "conductor"),
    ("Insulation", "insulation"),
    ("Cores", "cores"),
    ("Armoured", "armoured")
]

# -------------------------------------------------
# Load SKU master from Excel
# -------------------------------------------------
def load_skus(sku_path: str) -> pd.DataFrame:
    """
    Loads SKU master data from Excel file
    """
    df = pd.read_excel(sku_path)
    return df


# -------------------------------------------------
# Compute Spec Match %
# -------------------------------------------------
def compute_spec_match(df: pd.DataFrame, rfp_specs: dict) -> pd.DataFrame:
    """
    Compares RFP specs with SKU specs and computes Spec Match %

    rfp_specs expected keys:
    - voltage_kV
    - conductor
    - insulation
    - cores
    - armoured
    """

    df = df.copy()
    match_columns = []

    # Compare each spec (equal weight)
    for sku_col, rfp_key in MATCH_FIELDS:
        match_col = f"match_{sku_col.lower()}"

        df[match_col] = (
            df[sku_col].astype(str).str.lower()
            == str(rfp_specs.get(rfp_key)).lower()
        )

        match_columns.append(match_col)

    # Count matched specs
    df["matched_count"] = df[match_columns].sum(axis=1)

    # Spec Match %
    df["spec_match_pct"] = (
        df["matched_count"] / len(MATCH_FIELDS)
    ) * 100

    # Rank:
    # 1) Higher spec match first
    # 2) Lower price as tie-breaker
    df = df.sort_values(
        by=["spec_match_pct", "Unit_Price_per_km_INR"],
        ascending=[False, True]
    )

    return df
def build_comparison_table(df: pd.DataFrame, rfp_specs: dict, top_n: int = 3) -> pd.DataFrame:
    """
    Builds a comparison table between RFP requirements and top N SKU matches
    """
    top_df = df.head(top_n)

    comparison = {
        "Spec": [],
        "RFP Requirement": []
    }

    # Initialize SKU columns
    for sku in top_df["SKU_ID"]:
        comparison[sku] = []

    # Define specs to compare
    specs = [
        ("Voltage_kV", "voltage_kV", "Voltage (kV)"),
        ("Conductor", "conductor", "Conductor"),
        ("Insulation", "insulation", "Insulation"),
        ("Cores", "cores", "Cores"),
        ("Armoured", "armoured", "Armoured")
    ]

    for sku_col, rfp_key, label in specs:
        comparison["Spec"].append(label)
        comparison["RFP Requirement"].append(rfp_specs[rfp_key])

        for _, row in top_df.iterrows():
            comparison[row["SKU_ID"]].append(row[sku_col])

    return pd.DataFrame(comparison)
def classify_match(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds business-level match classification based on spec_match_pct
    """
    df = df.copy()

    def classify(pct):
        if pct >= 80:
            return "STRONG_MATCH"
        elif pct >= 50:
            return "PARTIAL_MATCH"
        else:
            return "NO_MATCH"

    df["match_classification"] = df["spec_match_pct"].apply(classify)
    return df
