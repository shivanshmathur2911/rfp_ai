import streamlit as st
from datetime import datetime
import pandas as pd
import altair as alt
import json

from src.sales_agent import scan_rfps, prioritize_rfps
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
from src.mto_agent import generate_mto_request  # <-- NEW IMPORT

# ---------------- CONFIG ----------------
RFP_SALES_FOLDER = "data/rfps_sales"
SKU_PATH = "data/skus/SKUs.xlsx"
TEST_PRICE_PATH = "data/pricing/test_prices.xlsx"
QUANTITY_KM = 10

st.set_page_config(
    page_title="Agentic AI – RFP Response Automation",
    layout="wide"
)

st.title("Agentic AI – B2B RFP Response Automation")
st.caption("EY Techathon | Demonstratable Agentic AI Prototype")

# =====================================================
# SALES AGENT
# =====================================================
st.header("Sales Agent – RFP Discovery & 90-Day Prioritization")

if st.button("Scan & Prioritize RFPs"):
    rfps = scan_rfps(RFP_SALES_FOLDER)
    prioritized = prioritize_rfps(rfps, days=90)

    today = datetime.today()
    sales_rows = []

    for r in rfps:
        days_left = (r["due_date"] - today).days if r["due_date"] else None
        sales_rows.append({
            "RFP ID": r["rfp_id"],
            "Source": r["source"],
            "Due Date": r["due_date"].date(),
            "Days Left": days_left,
            "Eligible (≤90 days)": "Yes" if r in prioritized else "No"
        })

    st.subheader("Discovered RFPs")
    st.dataframe(sales_rows, use_container_width=True)

    eligible_pdfs = [r for r in prioritized if r["source"] == "PDF"]
    st.session_state["eligible_rfps"] = eligible_pdfs

    st.success(f"{len(eligible_pdfs)} RFP(s) selected for technical processing")

# =====================================================
# TECHNICAL + PRICING (MULTI-RFP)
# =====================================================
if "eligible_rfps" in st.session_state and st.session_state["eligible_rfps"]:
    st.header("Technical & Pricing Agents – Multi-RFP Processing")

    sku_df = load_skus(SKU_PATH)

    decision_summary = []
    pricing_summary = []

    for rfp in st.session_state["eligible_rfps"]:
        st.subheader(f"RFP: {rfp['rfp_id']}")

        # ---------------- Technical Agent ----------------
        rfp_text = extract_full_text(rfp["path"])
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

        st.markdown("**Extracted RFP Specifications**")
        st.table(
            [{"Parameter": k.replace("_", " ").title(), "Required Value": v}
             for k, v in rfp_specs.items()]
        )

        match_df = classify_match(
            compute_spec_match(sku_df, rfp_specs)
        )

        best = match_df.iloc[0]

        # =====================================================
        # OPTION B: VOLTAGE MISMATCH HARD TRIGGER FOR MTO
        # =====================================================
        rfp_v = rfp_specs.get("voltage_kV")
        best_v = best.get("Voltage_kV")

        voltage_mismatch = False
        try:
            if rfp_v is not None and best_v is not None:
                voltage_mismatch = float(rfp_v) != float(best_v)
        except Exception:
            voltage_mismatch = False

        mto_triggered = (best["match_classification"] == "NO_MATCH") or voltage_mismatch

        # ---------------- Decision Summary (FIXED) ----------------
        decision_summary.append({
            "RFP ID": rfp["rfp_id"],
            "Best SKU": best["SKU_ID"],
            "Spec Match %": f"{best['spec_match_pct']}%",
            "Classification": ("MTO_TRIGGERED" if mto_triggered else best["match_classification"]),
            "Reason": (
                "Voltage mismatch (mandatory)" if voltage_mismatch
                else ("Low spec match" if best["match_classification"] == "NO_MATCH" else "Standard SKU available")
            )
        })

        # ---------- Slim Spec Match Bar ----------
        st.markdown("**Spec Match Confidence by SKU**")

        chart_df = match_df[["SKU_ID", "spec_match_pct", "match_classification"]]

        bar_chart = (
            alt.Chart(chart_df)
            .mark_bar(size=18)
            .encode(
                y=alt.Y("SKU_ID:N", sort="-x", title=None),
                x=alt.X(
                    "spec_match_pct:Q",
                    scale=alt.Scale(domain=[0, 100]),
                    title="Spec Match (%)"
                ),
                color=alt.Color(
                    "match_classification:N",
                    scale=alt.Scale(
                        domain=["STRONG_MATCH", "PARTIAL_MATCH", "NO_MATCH"],
                        range=["#2E7D32", "#F9A825", "#C62828"]
                    ),
                    legend=None
                ),
                tooltip=["SKU_ID", "spec_match_pct", "match_classification"]
            )
            .properties(height=140)
        )

        label_chart = (
            alt.Chart(chart_df)
            .mark_text(align="left", baseline="middle", dx=5)
            .encode(
                y=alt.Y("SKU_ID:N", sort="-x"),
                x=alt.X("spec_match_pct:Q"),
                text=alt.Text("spec_match_pct:Q", format=".0f")
            )
        )

        st.altair_chart(bar_chart + label_chart, use_container_width=True)

        with st.expander("View Detailed Technical Comparison"):
            comparison_df = build_comparison_table(match_df, rfp_specs)
            st.dataframe(comparison_df, use_container_width=True)

        # ---------------- NO_MATCH FLOW (UPGRADED) ----------------
        if mto_triggered:
            st.error(
                "No suitable standard SKU found (Mandatory voltage class mismatch)"
                if voltage_mismatch else
                "No suitable standard SKU found"
            )
            st.info("Made-to-Order workflow triggered for engineering feasibility")

            # Closest SKU (best row even if NO_MATCH) to show gaps
            closest_sku = match_df.iloc[0].to_dict()

            # Build a structured MTO request payload
            mto_payload = generate_mto_request(
                rfp_meta=rfp,
                rfp_specs=rfp_specs,
                closest_sku_row=closest_sku
            )

            st.markdown("**Engineering / MTO Request Generated**")
            gap_df = pd.DataFrame(mto_payload["gap_table"])
            st.dataframe(gap_df, use_container_width=True)

            # Download button (EY LOVES downloadable artifacts)
            safe_rfp_id = str(rfp["rfp_id"]).replace("/", "_").replace("\\", "_").replace(" ", "_")
            st.download_button(
                label="Download MTO Request (JSON)",
                data=json.dumps(mto_payload, indent=2),
                file_name=f"MTO_Request_{safe_rfp_id}.json",
                mime="application/json"
            )

            # Optional: rough pricing fallback estimate (closest SKU + customization premium)
            st.markdown("**Pricing Fallback (Rough Estimate)**")
            base_unit_price = closest_sku.get("Unit_Price_per_km_INR", 0) or 0
            customization_premium_pct = 12  # simple, explainable assumption
            estimated_material_cost = int(base_unit_price * QUANTITY_KM * (1 + customization_premium_pct / 100))

            st.write(f"Closest SKU used for estimate: **{closest_sku.get('SKU_ID')}**")
            st.write(f"Customization premium applied: **{customization_premium_pct}%**")
            st.write(f"Estimated Material Cost (₹): **₹ {estimated_material_cost:,.0f}**")
            st.caption("Note: Final pricing requires engineering feasibility, BOM, and lead-time confirmation.")

            # ---------------- Consolidated Pricing Summary (FIXED) ----------------
            pricing_summary.append({
                "RFP ID": rfp["rfp_id"],
                "SKU": closest_sku.get("SKU_ID"),
                "Material Cost (₹)": f"₹ {estimated_material_cost:,.0f}",
                "Test Cost (₹)": "MTO",
                "Total Cost (₹)": f"₹ {estimated_material_cost:,.0f}"
            })

            continue

        # ---------------- Pricing Agent ----------------
        pricing_df = compute_pricing(
            matched_df=match_df,
            quantity_km=QUANTITY_KM,
            test_price_path=TEST_PRICE_PATH
        )

        for _, row in pricing_df.iterrows():
            pricing_summary.append({
                "RFP ID": rfp["rfp_id"],
                "SKU": row["SKU_ID"],
                "Material Cost (₹)": f"₹ {row['material_cost']:,.0f}",
                "Test Cost (₹)": f"₹ {row['test_cost']:,.0f}",
                "Total Cost (₹)": f"₹ {row['total_cost']:,.0f}"
            })

    # =====================================================
    # CONSOLIDATED OUTPUTS
    # =====================================================
    st.header("Consolidated Decision Summary")
    st.dataframe(decision_summary, use_container_width=True)

    st.header("Consolidated Pricing Summary")
    if pricing_summary:
        st.dataframe(pricing_summary, use_container_width=True)
    else:
        st.warning("No RFPs qualified for standard pricing.")

st.markdown("---")
st.caption(
    "Design intent: executive-friendly decision support with explainable logic."
)
