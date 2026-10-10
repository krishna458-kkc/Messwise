"""MessWise - Sustainability & Financial Impact (Module H: H1, H2, H4).

Executive sustainability intelligence interface:
- H1: Greenhouse Gas (GHG) CO₂e emissions mitigation band (Low / Central / High).
- H2: Meals-Equivalent social impact based on learned per-head appetite.
- H4: One-click Green-Campus PDF Report generator and download.
- Full methodological disclosure and strict synthetic-versus-real data separation.
"""

from datetime import datetime
from typing import Optional

import streamlit as st
import plotly.graph_objects as go

from messwise.db import get_data_environment_summary, get_session_factory, init_db
from messwise.impact import (
    FACTOR_CENTRAL,
    FACTOR_HIGH,
    FACTOR_LOW,
    compute_green_campus_summary,
)
from messwise.pdf_report import generate_green_campus_pdf, is_pdf_available

st.set_page_config(
    page_title="MessWise | Sustainability Impact",
    page_icon="🌱",
    layout="wide",
)

init_db()

st.title("🌱 Sustainability & Environmental Impact")
st.caption("Module H: H1 CO₂e Estimate  •  H2 Meals-Equivalent  •  H4 Green-Campus Report (PLAN.md)")

st.markdown("---")

# Data Environment Selector & Honesty Guards
env_summary = get_data_environment_summary()
has_real = env_summary["has_real_data"]
has_verified = env_summary["has_verified_pilot_data"]
real_label = env_summary["real_env_label"]

col_env1, col_env2 = st.columns([2, 3])
with col_env1:
    env_choice = st.radio(
        "Data Environment:",
        options=["Synthetic Demonstration", real_label],
        index=0 if not has_verified else 1,
        horizontal=True,
        help="MessWise strictly isolates synthetic demonstration data from real pilot records.",
    )
    is_synthetic = 1 if env_choice == "Synthetic Demonstration" else 0

with col_env2:
    if is_synthetic == 1:
        st.warning(
            "⚠️ **Synthetic Demonstration — Not Real-World Impact**\n\n"
            "Metrics displayed below are derived from synthetic development records to verify "
            "the calculation pipeline. No real food or greenhouse gas emissions have been saved."
        )
    else:
        if not has_verified:
            unv = env_summary["unverified_test_meals_count"]
            st.warning(
                "ℹ️ **Real Pilot Data Collection Pending — Unverified Test Entries Only**\n\n"
                f"Currently **0 verified pilot meals** are recorded in the database "
                f"({unv} unverified manual test entries exist in database). "
                "Per PLAN.md Section 10, impact numbers are never fabricated. "
                "Real impact estimates will activate automatically once operator-verified pilot records are logged."
            )
        else:
            st.success(
                f"🟢 **Verified Pilot Environment Active** — Showing authentic measured impact "
                f"across {env_summary['verified_pilot_meals_count']} verified operational meals."
            )

st.markdown("---")

# Compute Green Campus Summary
session_factory = get_session_factory()
with session_factory() as session:
    summary = compute_green_campus_summary(
        session=session,
        is_synthetic=is_synthetic,
        reporting_period="October 2026",
    )

# Section 1: Executive KPI Overview
st.subheader("1. Operational Waste & Mitigation Overview")
c1, c2, c3, c4 = st.columns(4)

c1.metric("Meals Sampled", summary.meals_count, help="Total meals analyzed in reporting window")
c2.metric("Total Food Cooked", f"{summary.total_cooked_kg:,.1f} kg")
c3.metric(
    "Total Surplus / Leftovers",
    f"{summary.total_waste_kg:,.1f} kg",
    f"{summary.waste_percentage:.1f}% waste rate",
    delta_color="inverse",
)
c4.metric(
    "Estimated Avoided Food",
    f"{summary.eligible_avoided_kg:,.1f} kg",
    help="Verified reduction achieved through assisted quantity planning",
)

st.markdown("---")

# Section 2: H1 Greenhouse Gas (GHG) CO₂e Mitigation
st.subheader("2. Greenhouse Gas (GHG) Mitigation Band (H1)")
co2e = summary.co2e_impact

if not co2e.is_available:
    st.info(f"📊 **CO₂e Impact Status**: {co2e.availability_reason}")
else:
    st.markdown(
        f"Based on **{co2e.eligible_food_kg:,.1f} kg** of avoided food waste, estimated carbon emissions "
        f"mitigation is calculated using a peer-reviewed lifecycle uncertainty band:"
    )

    g1, g2, g3 = st.columns(3)
    g1.metric(
        "Low Estimate (Conservative)",
        f"{co2e.low_co2e_kg:,.1f} kg CO₂e",
        f"{(co2e.low_co2e_kg / 1000.0):.2f} tonnes CO₂e",
        help=f"Factor: {co2e.factor_config.low_factor:.2f} kg CO₂e/kg (Energies 2021 canteen study)",
    )
    g2.metric(
        "Central Estimate (Target)",
        f"{co2e.central_co2e_kg:,.1f} kg CO₂e",
        f"{(co2e.central_co2e_kg / 1000.0):.2f} tonnes CO₂e",
        help=f"Factor: {co2e.factor_config.central_factor:.2f} kg CO₂e/kg (Institutional catering average)",
    )
    g3.metric(
        "High Estimate (Upper Bound)",
        f"{co2e.high_co2e_kg:,.1f} kg CO₂e",
        f"{(co2e.high_co2e_kg / 1000.0):.2f} tonnes CO₂e",
        help=f"Factor: {co2e.factor_config.high_factor:.2f} kg CO₂e/kg (Sustainability 2021 hospitality LCA)",
    )

    # Uncertainty Band Chart
    fig_band = go.Figure()
    fig_band.add_trace(go.Bar(
        x=["Low Bound", "Central Target", "High Bound"],
        y=[co2e.low_co2e_kg, co2e.central_co2e_kg, co2e.high_co2e_kg],
        marker_color=["#74c69d", "#2d6a4f", "#1b4332"],
        text=[f"{co2e.low_co2e_kg:,.0f} kg", f"{co2e.central_co2e_kg:,.0f} kg", f"{co2e.high_co2e_kg:,.0f} kg"],
        textposition="outside",
    ))
    fig_band.update_layout(
        title="CO₂e Avoided by Estimation Tier (kg CO₂e)",
        yaxis_title="kg CO₂e Avoided",
        xaxis_title="Uncertainty Tier",
        height=320,
        margin=dict(l=40, r=40, t=50, b=40),
    )
    st.plotly_chart(fig_band, width='stretch')

with st.expander("🔍 Inspect Emission Factor Source & Lifecycle Boundaries"):
    st.markdown(f"""
    - **Governing Literature**: *{co2e.factor_config.source_name}*
    - **Methodology Version**: `{co2e.factor_config.version}`
    - **System Boundary**: {co2e.factor_config.system_boundary}
    - **Factor Constants**:
      - Low: `{co2e.factor_config.low_factor:.2f}` kg CO₂e / kg food waste
      - Central: `{co2e.factor_config.central_factor:.2f}` kg CO₂e / kg food waste
      - High: `{co2e.factor_config.high_factor:.2f}` kg CO₂e / kg food waste
    """)

st.markdown("---")

# Section 3: UN SDG 12.3 Food Waste Halving Tracker (H3)
st.subheader("3. UN SDG Target 12.3 Food Waste Halving Tracker (H3)")
st.markdown("Tracks per-capita institutional food waste toward the UN Sustainable Development Goal 12.3 target (halving food waste by 2030).")
sdg = summary.sdg123
if not sdg or not sdg.is_available:
    st.info(f"🎯 **SDG 12.3 Status**: {sdg.availability_reason if sdg else 'Insufficient operational records in period.'}")
else:
    s_c1, s_c2, s_c3 = st.columns(3)
    with s_c1:
        st.metric(
            "Current Waste per Diner",
            f"{sdg.current_waste_per_head_g:.1f} g/meal",
            f"-{sdg.reduction_pct:.1f}% vs Baseline",
            delta_color="inverse",
            help="Measured grams of unconsumed food per student per meal",
        )
    with s_c2:
        st.metric(
            "SDG 12.3 Goal Progress",
            f"{sdg.target_progress_pct:.1f}%",
            f"{sdg.status_label}",
            help="Progress toward 50% waste reduction benchmark",
        )
    with s_c3:
        st.metric(
            "Pilot Baseline Benchmark",
            f"{sdg.baseline_waste_per_head_g:.1f} g/meal",
            "Pre-intervention institutional baseline",
        )

st.markdown("---")

# Section 4: H2 Social & Meals-Equivalent Impact
st.subheader("4. Social & Meals-Equivalent Impact (H2)")
meals_eq = summary.meals_equivalent

if not meals_eq.is_available:
    st.info(f"🍲 **Meals-Equivalent Status**: {meals_eq.availability_reason}")
else:
    m_col1, m_col2 = st.columns([1, 2])
    with m_col1:
        st.metric(
            "Illustrative Meals-Equivalent",
            f"{meals_eq.meals_equivalent:,.0f} meals",
            help="Computed from learned average per-head meal consumption",
        )
    with m_col2:
        st.markdown(f"""
        - **Calculation Basis**: `Avoided Food ({meals_eq.eligible_food_kg:.1f} kg) ÷ Average Consumption ({meals_eq.avg_consumption_per_head_kg:.3f} kg/meal)`.
        - **Data Source**: {meals_eq.consumption_source}.
        - **Operational Caveat**: This figure represents an *illustrative equivalent* of food nutrition preserved.
          Per core safety principles, MessWise **never** re-serves cooked leftovers to students.
        """)

st.markdown("---")

# Section 5: Resource Efficiency: Embedded Water & Energy Footprint (H5)
st.subheader("5. Resource Efficiency: Virtual Water & Energy Preserved (H5)")
st.markdown("Quantifies embedded natural resource savings associated with avoided agricultural production and food preparation.")
we = summary.water_energy
if not we or not we.is_available:
    st.info(f"💧 **Resource Footprint Status**: {we.availability_reason if we else 'Resource footprint unavailable in selected period.'}")
else:
    w_c1, w_c2 = st.columns(2)
    with w_c1:
        st.metric(
            "Virtual Water Preserved",
            f"{we.central_water_litres:,.0f} Litres",
            f"{we.low_water_litres:,.0f} – {we.high_water_litres:,.0f} L band",
            help="Agricultural and processing freshwater requirements avoided",
        )
        st.caption(f"**Source**: {we.water_source}")
    with w_c2:
        st.metric(
            "Embedded Primary Energy",
            f"{we.central_energy_mj:,.1f} MJ",
            f"{we.low_energy_mj:,.1f} – {we.high_energy_mj:,.1f} MJ band",
            help="Cumulative primary energy demand in agricultural production and transport",
        )
        st.caption(f"**Source**: {we.energy_source}")

st.markdown("---")

# Section 6: Institutional Budget-vs-Actual Food Cost Utilisation (H6)
st.subheader("6. Institutional Budget-vs-Actual Food Cost Utilisation (H6)")
st.markdown("Compares meal cost utilisation against the mess committee's target budget per plate.")
bva = summary.budget_vs_actual
if not bva or not bva.is_available:
    st.info(f"📊 **Financial Utilisation Status**: {bva.status_message if bva else 'Financial metrics unavailable.'}")
else:
    b_c1, b_c2, b_c3 = st.columns(3)
    with b_c1:
        st.metric("Target Meal Budget", f"₹{bva.target_budget_per_meal_inr:.2f} / plate")
    with b_c2:
        st.metric("Actual Food Cost", f"₹{bva.actual_cost_per_meal_inr:.2f} / plate" if bva.actual_cost_per_meal_inr is not None else "N/A")
    with b_c3:
        st.metric("Budget Utilisation", f"{bva.utilization_pct:.1f}%" if bva.utilization_pct is not None else "N/A")

st.markdown("---")

# Section 7: H4 One-Click Green-Campus PDF Report Download
st.subheader("7. One-Click Green-Campus Sustainability Report (H4)")
st.markdown(
    "Generate an executive, downloadable PDF report formatted for college leadership, "
    "mess committees, and institutional ESG audits."
)

if is_pdf_available():
    try:
        # Generate PDF in-memory
        pdf_bytes = generate_green_campus_pdf(summary)
        report_filename = f"MessWise_GreenCampus_{'Synthetic' if is_synthetic else 'Real'}_{datetime.now().strftime('%Y%m')}.pdf"

        d_col1, d_col2 = st.columns([2, 3])
        with d_col1:
            st.download_button(
                label="📄 Download Green-Campus Report (PDF)",
                data=pdf_bytes,
                file_name=report_filename,
                mime="application/pdf",
                type="primary",
                help="Generates an in-memory audit PDF formatted for university administration.",
            )
        with d_col2:
            st.caption(
                f"**File**: `{report_filename}` ({len(pdf_bytes):,} bytes)<br/>"
                "Includes executive summary, emission factor citations, meals-equivalent, and zero-hunger shortage checks.",
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.error(f"Error generating PDF report: {e}")
else:
    st.warning(
        "ℹ️ **PDF Generation Unavailable**: The `reportlab` library is not installed in the active Python environment. "
        "Please run `python -m pip install -r requirements.txt` to enable one-click PDF reports."
    )
