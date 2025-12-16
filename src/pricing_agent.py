import pandas as pd

# -------------------------------------------------
# Load test pricing table
# -------------------------------------------------
def load_test_prices(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    return df


# -------------------------------------------------
# Resolve price column robustly
# -------------------------------------------------
def resolve_price_column(df: pd.DataFrame) -> str:
    """
    Finds the column that represents price/cost in a robust way
    """
    for col in df.columns:
        if any(keyword in col for keyword in ["price", "cost", "amount", "inr"]):
            return col

    raise ValueError(
        f"No price column found in test pricing table. Columns found: {df.columns.tolist()}"
    )


# -------------------------------------------------
# Compute pricing
# -------------------------------------------------
def compute_pricing(
    matched_df: pd.DataFrame,
    quantity_km: float,
    test_price_path: str
) -> pd.DataFrame:
    """
    Computes material + test pricing for eligible SKUs
    Only STRONG_MATCH and PARTIAL_MATCH SKUs are priced
    """

    # Load and normalize test pricing
    test_df = load_test_prices(test_price_path)
    price_col = resolve_price_column(test_df)

    # Filter eligible SKUs
    eligible = matched_df[
        matched_df["match_classification"].isin(["STRONG_MATCH", "PARTIAL_MATCH"])
    ].copy()

    # Material cost
    eligible["material_cost"] = (
        eligible["Unit_Price_per_km_INR"] * quantity_km
    )

    # Total test cost (same for all SKUs)
    total_test_cost = test_df[price_col].sum()
    eligible["test_cost"] = total_test_cost

    # Grand total
    eligible["total_cost"] = (
        eligible["material_cost"] + eligible["test_cost"]
    )

    return eligible[[
        "SKU_ID",
        "match_classification",
        "material_cost",
        "test_cost",
        "total_cost"
    ]]
