import pandas as pd

def build_gap_table(rfp_specs: dict, closest_sku_row: dict) -> pd.DataFrame:
    rows = []
    mapping = {
        "voltage_kV": "Voltage_kV",
        "conductor": "Conductor",
        "insulation": "Insulation",
        "cores": "Cores",
        "armoured": "Armoured",
    }

    for rfp_key, sku_col in mapping.items():
        rows.append({
            "Parameter": rfp_key.replace("_", " ").title(),
            "RFP Requirement": rfp_specs.get(rfp_key),
            "Closest SKU Value": closest_sku_row.get(sku_col),
            "Match": "Yes" if str(rfp_specs.get(rfp_key)).strip().lower() == str(closest_sku_row.get(sku_col)).strip().lower() else "No"
        })

    return pd.DataFrame(rows)

def generate_mto_request(rfp_meta: dict, rfp_specs: dict, closest_sku_row: dict) -> dict:
    gap_df = build_gap_table(rfp_specs, closest_sku_row)

    request = {
        "rfp_id": rfp_meta.get("rfp_id"),
        "due_date": str(rfp_meta.get("due_date")),
        "workflow": "MTO_NEW_SKU_REQUEST",
        "reason": "No standard SKU meets mandatory requirements",
        "rfp_specs": rfp_specs,
        "closest_sku": {
            "SKU_ID": closest_sku_row.get("SKU_ID"),
            "Product_Category": closest_sku_row.get("Product_Category"),
            "Unit_Price_per_km_INR": closest_sku_row.get("Unit_Price_per_km_INR"),
        },
        "actions": [
            "Engineering feasibility check",
            "Design/BOM finalization",
            "Prototype/test sample if required",
            "Finalize new SKU code and lead time",
            "Commercial approval for deviations"
        ],
        "gap_table": gap_df.to_dict(orient="records")
    }

    return request
