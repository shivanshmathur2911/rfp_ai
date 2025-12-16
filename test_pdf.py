from utils.pdf_reader import extract_full_text
from utils.section_finder import find_section
from utils.normalizer import (
    extract_voltage,
    extract_conductor,
    extract_insulation,
    extract_cores,
    extract_armouring
)

from src.technical_agent import (
    load_skus,
    compute_spec_match,
    build_comparison_table,
    classify_match
)

from src.pricing_agent import compute_pricing


# -------------------------------
# STEP 1: Read full RFP text
# -------------------------------
pdf_path = "data/rfps/RFP1_sim.pdf"
text = extract_full_text(pdf_path)

# -------------------------------
# STEP 2: Isolate technical section
# -------------------------------
tech_section = find_section(
    text,
    start_keywords=[
        "technical requirements",
        "technical requirements & scope of supply",
        "scope of supply"
    ],
    end_keywords=[
        "integration approach",
        "security",
        "timelines",
        "deliverables"
    ]
)

# -------------------------------
# STEP 3: Extract RFP specifications
# -------------------------------
rfp_specs = {
    "voltage_kV": extract_voltage(tech_section),
    "conductor": extract_conductor(tech_section),
    "insulation": extract_insulation(tech_section),
    "cores": extract_cores(tech_section),
    "armoured": extract_armouring(tech_section)
}

print("\nRFP Specs Extracted:")
print(rfp_specs)

# -------------------------------
# STEP 4: Load SKU master
# -------------------------------
sku_df = load_skus("data/skus/SKUs.xlsx")

print("\nSKU Master Loaded:")
print(sku_df)

# -------------------------------
# STEP 5: Technical matching
# -------------------------------
result_df = compute_spec_match(sku_df, rfp_specs)
result_df = classify_match(result_df)

print("\nRanked SKU Matches (Spec Match %):")
print(result_df[[
    "SKU_ID",
    "Voltage_kV",
    "Conductor",
    "Insulation",
    "Cores",
    "Armoured",
    "spec_match_pct"
]])

# -------------------------------
# STEP 6: Comparison table
# -------------------------------
comparison_df = build_comparison_table(result_df, rfp_specs)

print("\nRFP vs SKU Comparison Table:")
print(comparison_df)

print("\nRanked SKU Matches with Classification:")
print(result_df[[
    "SKU_ID",
    "spec_match_pct",
    "match_classification"
]])

# -------------------------------
# STEP 7: Pricing Agent
# -------------------------------
pricing_df = compute_pricing(
    matched_df=result_df,
    quantity_km=10,
    test_price_path="data/pricing/test_prices.xlsx"
)

print("\nPricing Output:")
print(pricing_df)
