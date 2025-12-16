from src.sales_agent import scan_rfps, prioritize_rfps, prepare_sales_summary
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


RFP_SALES_FOLDER = "data/rfps_sales"
SKU_PATH = "data/skus/SKUs.xlsx"
TEST_PRICE_PATH = "data/pricing/test_prices.xlsx"


def run_pipeline():
    print("\n=== SALES AGENT: SCANNING RFP SOURCES ===")

    rfps = scan_rfps(RFP_SALES_FOLDER)

    prioritized = prioritize_rfps(rfps, days=90)
    selected_pdf = next((r for r in prioritized if r["source"] == "PDF"), None)

    if not selected_pdf:
        print("\n[Main Agent] No full RFP document available yet.")
        return

    print("\n=== SALES AGENT: SELECTED RFP ===")
    print(selected_pdf)

    # -----------------------------
    # MAIN AGENT: PREPARE SUMMARIES
    # -----------------------------
    sales_summary = prepare_sales_summary(selected_pdf)

    # -----------------------------
    # TECHNICAL AGENT
    # -----------------------------
    rfp_text = extract_full_text(sales_summary["technical_summary"]["document_path"])

    tech_section = find_section(
        rfp_text,
        ["technical requirements", "scope of supply"],
        ["integration approach", "security"]
    )

    rfp_specs = {
        "voltage_kV": extract_voltage(tech_section),
        "conductor": extract_conductor(tech_section),
        "insulation": extract_insulation(tech_section),
        "cores": extract_cores(tech_section),
        "armoured": extract_armouring(tech_section)
    }

    sku_df = load_skus(SKU_PATH)
    match_df = classify_match(compute_spec_match(sku_df, rfp_specs))

    print("\n[Technical Agent] Match Results:")
    print(match_df[["SKU_ID", "spec_match_pct", "match_classification"]])

    # -----------------------------
    # NO_MATCH HANDLING (KEY ADDITION)
    # -----------------------------
    no_match_rows = match_df[match_df["match_classification"] == "NO_MATCH"]

    if not no_match_rows.empty:
        print("\n[Main Agent] NO_MATCH detected.")
        print("[Main Agent] Triggering Made-to-Order (MTO) workflow.")

        print("[Engineering] Action: Assess feasibility for custom SKU.")
        print("[Engineering] Input Specs:")
        print(rfp_specs)

        print("[Pricing] Action: Creating preliminary estimate for custom SKU.")
        print("[Pricing] Assumption: +25% premium over closest standard SKU.")

    # -----------------------------
    # PRICING AGENT (STANDARD SKUs)
    # -----------------------------
    pricing_df = compute_pricing(
        matched_df=match_df,
        quantity_km=sales_summary["pricing_summary"]["quantity_km"],
        test_price_path=TEST_PRICE_PATH
    )

    print("\n=== FINAL CONSOLIDATED RFP RESPONSE ===")
    print(pricing_df)


if __name__ == "__main__":
    run_pipeline()
