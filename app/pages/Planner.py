"""MessWise - Cooking Quantity Planner & Optimiser.

Operational interface for institutional kitchen managers (Module B: B1-B5 per PLAN.md).
Transforms demand forecasts into per-dish cooking quantities with:
- B1: Explainable cooking quantities: Quantity_d = H_q * r_d * (1 + prep_loss) with batch rounding.
- B2: Per-head consumption learning: robust median over recent meals, split by meal type.
- B3: Service-level slider: manager chooses protection level (e.g. 90%, 95%, 99%) and inspects trade-offs.
- B4: Cost-Aware Optimiser (Newsvendor logic): service level derived from shortage vs waste cost trade-offs,
      dish criticality policy defaults (staples 99%, mains 95%, sides 90%), safety floor, and overrides.
- B5: Kaplan-Meier Shortage-Aware Consumption Learning: historical meals where a dish ran out are retained
      as right-censored lower-bound observations rather than discarded or treated as complete demand.

Adheres strictly to synthetic/real data separation.
Never displays fabricated or non-functional placeholder values.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Ensure root directory is on Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from messwise.db import (
    get_data_environment_summary,
    get_session_factory,
    init_db,
    save_meal_plan,
)
from messwise.forecast import MEAL_TYPES, get_trained_forecaster
from messwise.planner import (
    DEFAULT_BATCH_SIZES,
    DEFAULT_CRITICALITY_TIERS,
    DEFAULT_SAFETY_FLOOR,
    DishCostConfig,
    calculate_newsvendor_service_level,
    calculate_service_headcount,
    compute_dish_consumption_rates,
    generate_meal_plan,
)

st.set_page_config(
    page_title="MessWise | Cooking Planner",
    page_icon="📋",
    layout="wide",
)
init_db()

# Custom CSS for operational clarity, distinct badges, and high legibility
st.markdown("""
<style>
    .planner-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-title {
        font-size: 0.80rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-big {
        font-size: 2.0rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
        margin-top: 4px;
    }
    .metric-subtext {
        font-size: 0.84rem;
        color: #475569;
        margin-top: 4px;
    }
    .badge-real {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-synth {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-policy {
        background-color: #eff6ff;
        color: #1d4ed8;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-cost {
        background-color: #f5f3ff;
        color: #6d28d9;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-censored {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-exact {
        background-color: #ecfdf5;
        color: #047857;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .explanation-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-top: 14px;
        font-size: 0.95rem;
        color: #1e293b;
        line-height: 1.5;
    }
    .criticality-card {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)

# Page Header
st.title("📋 Cooking Quantity Planner & Optimiser")
st.caption("Module B: Per-Dish Quantity Plans, Newsvendor Optimiser & Kaplan-Meier Learning (PLAN.md Section 5 & 8.2–8.3)")

# Inspect database for actual record counts before rendering environment controls
session_factory = get_session_factory()
with session_factory() as check_session:
    env_summary = get_data_environment_summary(check_session)

real_meals_count = env_summary["real_meals_count"]
synth_meals_count = env_summary["synthetic_meals_count"]
has_real_records = env_summary["has_real_data"]

# Top Bar: Data Environment Selector & Truthfulness Guard
if not has_real_records:
    env_choice = 1  # Strictly enforce Synthetic Demo Data
    st.warning(
        f"🧪 **Synthetic Development Data — Demonstration Only**\n\n"
        f"• **Real pilot records: 0** (Real Pilot Data environment is disabled until kitchen staff record operational meals via Kitchen mode).\n"
        f"• Currently loaded: **{synth_meals_count} synthetic demonstration meals** used strictly for algorithmic verification and workflow testing."
    )
    col_env, col_hint = st.columns([2, 1])
    with col_env:
        st.markdown(
            f"<div style='margin-top: 4px;'><strong>Active Data Environment:</strong> "
            f"<span class='badge-synth'>Synthetic Demo Dataset ({synth_meals_count} meals)</span></div>",
            unsafe_allow_html=True,
        )
    with col_hint:
        st.markdown(
            "<div style='text-align: right; color: #64748b; font-size: 0.84rem; margin-top: 4px;'>"
            "🔒 Real Pilot Data: <em>Unavailable (0 meals logged)</em></div>",
            unsafe_allow_html=True,
        )
else:
    col_env, col_hint = st.columns([2, 1])
    with col_env:
        env_choice = st.radio(
            "Select Data Environment:",
            options=[0, 1],
            format_func=lambda x: (
                env_summary["real_env_label"]
                if x == 0
                else f"🧪 Synthetic Demo Data ({synth_meals_count} demonstration meals)"
            ),
            index=0,
            horizontal=True,
            key="planner_env_mode",
        )
    with col_hint:
        if env_choice == 0:
            badge_cls = env_summary["real_env_badge_class"]
            badge_text = env_summary["real_env_badge"]
            st.markdown(
                f"<div style='text-align: right; margin-top: 14px;'><span class='{badge_cls}'>"
                f"{badge_text}</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='text-align: right; margin-top: 14px;'><span class='badge-synth'>"
                f"▲ Active Environment: Synthetic Demo Data ({synth_meals_count} records)</span></div>",
                unsafe_allow_html=True,
            )

    if env_choice == 0 and not env_summary["is_verified_pilot"]:
        unv = env_summary["unverified_test_meals_count"]
        st.warning(
            f"⚠️ **Unverified Manual Test Entries — Not Verified Pilot Data**\n\n"
            f"• Currently **{unv} non-synthetic meals** exist in the database with status `verification_status: unverified_test`.\n"
            f"• These entries were logged during development/manual testing and have **not** been operator-confirmed as live pilot measurements.\n"
            f"• Planning rates and historical demand models below reflect these test logs only."
        )

st.divider()

# Controls Row: Meal, Date, Strength, Loss
col_date, col_meal, col_strength, col_loss = st.columns([1.5, 1.2, 1.2, 1.5])

with col_date:
    today_val = date.today()
    target_date = st.date_input(
        "Target Meal Date:",
        value=today_val,
        min_value=today_val - timedelta(days=30),
        max_value=today_val + timedelta(days=14),
        key="planner_date",
    )
    target_date_str = target_date.strftime("%Y-%m-%d")

with col_meal:
    meal_type = st.selectbox(
        "Meal Slot:",
        options=list(MEAL_TYPES),
        index=1,  # Lunch by default
        format_func=lambda m: m.title(),
        key="planner_meal_type",
    )

with col_strength:
    hostel_strength = st.number_input(
        "Hostel Capacity (S):",
        min_value=50,
        max_value=3000,
        value=500,
        step=25,
        help="Current total registered student strength.",
        key="planner_strength",
    )

with col_loss:
    prep_loss_pct = st.slider(
        "Prep Loss Allowance:",
        min_value=0.0,
        max_value=10.0,
        value=3.0,
        step=0.5,
        format="%.1f%%",
        help="Transparent kitchen allowance for peeling, trimming, and steam loss (default 3%).",
        key="planner_prep_loss",
    ) / 100.0

# -----------------------------------------------------------------------------
# Planning Strategy Selection: B3 Manual vs B4 Cost-Aware Newsvendor
# -----------------------------------------------------------------------------
st.markdown("### ⚖️ Service-Level Protection & Cost Policy (B3 & B4)")

plan_mode_choice = st.radio(
    "Select Protection Strategy:",
    options=["Manual Service Level (B3)", "Cost-Aware Optimiser / Newsvendor (B4)"],
    index=0,
    horizontal=True,
    help="Choose between manager-selected global safety level (B3) or cost-minimizing Newsvendor optimization per dish tier (B4).",
    key="planner_strategy_selector",
)
is_cost_aware = (plan_mode_choice == "Cost-Aware Optimiser / Newsvendor (B4)")

# Initialize state variables
manual_service_level = 0.95
safety_floor_val = 0.90
cost_configs_input: Dict[str, Any] = {}
overrides_input: Dict[str, Any] = {}

if not is_cost_aware:
    # -------------------------------------------------------------------------
    # B3 Manual Mode Controls
    # -------------------------------------------------------------------------
    st.caption("Manual Mode (B3): Manager selects a uniform safety protection level driving planning headcount H_q.")

    if "service_level_pct" not in st.session_state:
        st.session_state["service_level_pct"] = 95

    def _set_service_level_preset(pct_val: int) -> None:
        st.session_state["service_level_pct"] = pct_val

    col_presets, col_slider = st.columns([1.8, 2.2])
    current_service_pct = st.session_state.get("service_level_pct", 95)

    with col_presets:
        st.markdown("**Quick Preset Selection:**")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            st.button(
                "90% Lean",
                type="primary" if current_service_pct == 90 else "secondary",
                use_container_width=True,
                help="Lower buffer; minimal waste, ~10% run-out risk",
                on_click=_set_service_level_preset,
                args=(90,),
                key="btn_preset_90",
            )
        with p_col2:
            st.button(
                "95% Balanced ★",
                type="primary" if current_service_pct == 95 else "secondary",
                use_container_width=True,
                help="Recommended operational safety level, ~5% risk",
                on_click=_set_service_level_preset,
                args=(95,),
                key="btn_preset_95",
            )
        with p_col3:
            st.button(
                "99% Safe",
                type="primary" if current_service_pct == 99 else "secondary",
                use_container_width=True,
                help="Near-zero shortage tolerance, ~1% risk",
                on_click=_set_service_level_preset,
                args=(99,),
                key="btn_preset_99",
            )

    with col_slider:
        service_level_pct = st.slider(
            "Service Level Target (q):",
            min_value=85,
            max_value=99,
            step=1,
            format="%d%%",
            key="service_level_pct",
            help="Adjusts planning headcount H_q using forecast empirical residuals.",
        )
        manual_service_level = float(service_level_pct) / 100.0
        mode_label = "Lean" if service_level_pct <= 90 else ("Balanced" if service_level_pct <= 95 else "Safe Protection")
        st.caption(f"🎯 **Active Manual Target:** `{service_level_pct}%` ({mode_label}) — Coverage target: `q = {manual_service_level:.2f}`")

else:
    # -------------------------------------------------------------------------
    # B4 Cost-Aware Optimiser Controls
    # -------------------------------------------------------------------------
    st.caption(
        "Cost-Aware Optimiser (B4): Derives optimal service level from Newsvendor equation "
        "q* = Cu / (Cu + Co) = k / (k + 1), balancing shortage penalty against excess food waste."
    )

    # Criticality Policy Tiers Overview
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        st.markdown("""
        <div class="criticality-card">
            <strong>🍚 Staples (Rice, Roti)</strong><br>
            Target: <strong>99%</strong> (k = 99)<br>
            <span style="color:#64748b; font-size:0.80rem;">Near-zero shortage tolerance</span>
        </div>
        """, unsafe_allow_html=True)
    with tc2:
        st.markdown("""
        <div class="criticality-card">
            <strong>🍛 Main Curries (Dal, Sabzi)</strong><br>
            Target: <strong>95%</strong> (k = 19)<br>
            <span style="color:#64748b; font-size:0.80rem;">Balanced operational protection</span>
        </div>
        """, unsafe_allow_html=True)
    with tc3:
        st.markdown("""
        <div class="criticality-card">
            <strong>🥗 Sides & Salads (Raita, etc.)</strong><br>
            Target: <strong>90%</strong> (k = 9)<br>
            <span style="color:#64748b; font-size:0.80rem;">Lean waste-preventing buffer</span>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("⚙️ Cost Assumptions & Protection Floor Settings", expanded=True):
        f_col1, f_col2 = st.columns([1.5, 2.5])
        with f_col1:
            safety_floor_pct = st.slider(
                "Safety Protection Floor (q_floor):",
                min_value=80,
                max_value=95,
                value=90,
                step=1,
                format="%d%%",
                help="Safety guard: prevents economic cost optimization from recommending risky service below this floor.",
                key="planner_safety_floor",
            )
            safety_floor_val = float(safety_floor_pct) / 100.0

        with f_col2:
            cost_source_mode = st.radio(
                "Cost Parameter Source:",
                options=[
                    "Documented Criticality Policy Defaults (No prices configured)",
                    "Manager Cost Ratio Assumptions (Configured Estimates)",
                ],
                index=0,
                key="cost_source_mode",
                help="Choose whether to use documented institutional criticality policy defaults or enter custom cost penalties.",
            )

        if "Manager Cost Ratio" in cost_source_mode:
            st.info(
                "ℹ️ **Manager-Configured Assumptions:** These cost values are manager-entered estimates, "
                "not verified procurement invoices or observed penalties. The system will derive Newsvendor targets from these entered values."
            )
            k_col1, k_col2, k_col3 = st.columns(3)
            with k_col1:
                k_staple = st.number_input(
                    "Staple Penalty Ratio (k = Cu / Co):",
                    min_value=1.0,
                    max_value=200.0,
                    value=99.0,
                    step=5.0,
                    help="How many times worse is running out of rice/roti than wasting a kg? Default 99 => 99% target.",
                    key="k_staple_input",
                )
            with k_col2:
                k_main = st.number_input(
                    "Main Curry Penalty Ratio (k):",
                    min_value=1.0,
                    max_value=100.0,
                    value=19.0,
                    step=1.0,
                    help="Default 19 => 95% target.",
                    key="k_main_input",
                )
            with k_col3:
                k_side = st.number_input(
                    "Side Dish Penalty Ratio (k):",
                    min_value=1.0,
                    max_value=50.0,
                    value=9.0,
                    step=1.0,
                    help="Default 9 => 90% target.",
                    key="k_side_input",
                )

            # Pass configured cost ratios keyed by category
            cost_configs_input = {
                "staple": {"cost_ratio_k": k_staple, "safety_floor": safety_floor_val},
                "main": {"cost_ratio_k": k_main, "safety_floor": safety_floor_val},
                "side": {"cost_ratio_k": k_side, "safety_floor": safety_floor_val},
            }
        else:
            st.caption(
                "📌 Using documented criticality policy defaults: Staples 99%, Mains 95%, Sides 90%. "
                "No verified financial purchase prices are asserted."
            )


# -----------------------------------------------------------------------------
# Execute Meal Plan Engine (B1-B5)
# -----------------------------------------------------------------------------
session_factory = get_session_factory()
session = session_factory()

try:
    meal_plan = generate_meal_plan(
        session=session,
        target_date=target_date_str,
        meal_type=meal_type,
        service_level=manual_service_level,
        prep_loss_pct=prep_loss_pct,
        hostel_strength=hostel_strength,
        is_synthetic=env_choice,
        cost_mode=is_cost_aware,
        safety_floor=safety_floor_val,
        dish_cost_configs=cost_configs_input if is_cost_aware else None,
        manager_overrides=overrides_input if overrides_input else None,
    )

    # -------------------------------------------------------------------------
    # Planning Summary Cards
    # -------------------------------------------------------------------------
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        st.markdown(f"""
        <div class="planner-card">
            <div class="metric-title">Forecast Attendance (Ĥ)</div>
            <div class="metric-big">{meal_plan.forecast_h_hat}</div>
            <div class="metric-subtext">Base Expected Turnout</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col2:
        st.markdown(f"""
        <div class="planner-card">
            <div class="metric-title">Planning Headcount (H<sub>q</sub>)</div>
            <div class="metric-big" style="color: #2563eb;">{meal_plan.planning_headcount}</div>
            <div class="metric-subtext">Buffer: +{meal_plan.headcount_buffer} students</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col3:
        risk_color = "#047857" if meal_plan.service_level >= 0.95 else ("#b45309" if meal_plan.service_level >= 0.90 else "#b91c1c")
        mode_badge = "Cost-Aware Newsvendor" if is_cost_aware else f"Manual {meal_plan.service_level:.0%}"
        st.markdown(f"""
        <div class="planner-card">
            <div class="metric-title">Effective Service Level</div>
            <div class="metric-big" style="color: {risk_color};">{meal_plan.service_level:.1%}</div>
            <div class="metric-subtext">{mode_badge} (Risk ~{meal_plan.run_out_risk_pct:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col4:
        st.markdown(f"""
        <div class="planner-card">
            <div class="metric-title">Estimated Kitchen Surplus</div>
            <div class="metric-big" style="color: #475569;">{meal_plan.total_expected_surplus_kg:.1f} kg</div>
            <div class="metric-subtext">Across {meal_plan.total_planned_kg:.1f} kg Planned Food</div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Operational Trade-off Curve (Plotly Visualization)
    # -------------------------------------------------------------------------
    with st.expander("📊 Inspect Waste vs Shortage Trade-Off Curve", expanded=False):
        forecaster, df_hist = get_trained_forecaster(session=session, is_synthetic=env_choice)
        f_slot = forecaster.predict_slot(
            df_history=df_hist,
            target_date_str=target_date_str,
            meal_type=meal_type,
            hostel_strength=hostel_strength,
            is_synthetic=env_choice,
        )

        test_levels = [0.85, 0.88, 0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99]
        hq_curve = []
        risk_curve = []
        for lvl in test_levels:
            t_hq, t_trade = calculate_service_headcount(forecaster, f_slot, lvl)
            hq_curve.append(t_hq)
            risk_curve.append(t_trade["run_out_risk_pct"])

        fig_tradeoff = go.Figure()
        fig_tradeoff.add_trace(go.Scatter(
            x=[lvl * 100 for lvl in test_levels],
            y=hq_curve,
            name="Planning Headcount (Hq)",
            mode="lines+markers",
            line=dict(color="#2563eb", width=3),
            yaxis="y1",
        ))
        fig_tradeoff.add_trace(go.Scatter(
            x=[lvl * 100 for lvl in test_levels],
            y=risk_curve,
            name="Estimated Run-Out Risk (%)",
            mode="lines+markers",
            line=dict(color="#dc2626", width=2, dash="dash"),
            yaxis="y2",
        ))
        fig_tradeoff.add_vline(
            x=meal_plan.service_level * 100,
            line_dash="dot",
            line_color="#0f172a",
            annotation_text=f"Active Target: {meal_plan.service_level*100:.1f}%",
            annotation_position="top left",
        )
        fig_tradeoff.update_layout(
            title="Operational Trade-Off: Safety Buffer vs Estimated Run-Out Risk",
            xaxis=dict(title="Service Level Target (%)", tickmode="linear", dtick=2),
            yaxis=dict(title="Planning Headcount (Students)", side="left"),
            yaxis2=dict(title="Estimated Run-Out Risk (%)", side="right", overlaying="y", showgrid=False, range=[0, 20]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=50, b=40),
            height=300,
        )
        st.plotly_chart(fig_tradeoff, use_container_width=True)

    # -------------------------------------------------------------------------
    # Per-Dish Quantity Plan Table (B1, B4, B5)
    # -------------------------------------------------------------------------
    st.markdown("### 🍲 Recommended Cooking Quantities (B1, B4 & B5)")
    st.caption("Per-dish recommendations reflecting dish criticality, Kaplan-Meier learned rates, and practical batch sizes.")

    if not meal_plan.dishes:
        st.info("No dishes registered in the database catalog. Please register dishes on the Kitchen page.")
    else:
        table_rows = []
        for dish in meal_plan.dishes:
            batch_str = f"{dish.batch_size:g} {dish.unit}" if dish.batch_size else "—"

            # Service-level source badge
            if dish.is_cost_aware:
                if dish.is_floor_applied:
                    policy_badge = f"{dish.effective_service_level:.0%} (Floored at {dish.safety_floor:.0%})"
                elif dish.cost_ratio_k is not None:
                    policy_badge = f"{dish.effective_service_level:.1%} (k={dish.cost_ratio_k:g})"
                else:
                    policy_badge = f"{dish.effective_service_level:.0%} ({dish.criticality_tier.title()} Policy)"
            else:
                policy_badge = f"{dish.effective_service_level:.0%} (Manual Slider)"

            # Appetite rate method badge
            method_label = dish.estimation_method.replace("_", " ").title()
            rate_display = f"{dish.per_head_rate:.3f} {dish.unit}"

            # Shortage & censoring breakdown
            if dish.num_observations > 0:
                history_display = f"{dish.num_observations} meals ({dish.num_exact} exact, {dish.num_censored} ran out)"
            else:
                history_display = "0 meals (portion default)"

            conf_badge = (
                "🟢 High" if dish.confidence_status == "high"
                else ("🟡 Moderate" if dish.confidence_status == "moderate" else "🔴 Low (Fallback)")
            )

            table_rows.append({
                "Dish Name": dish.dish_name,
                "Category / Tier": f"{dish.category.title()} ({dish.criticality_tier})",
                "Service Level (q*)": policy_badge,
                "Learned Rate (rd)": f"{rate_display} ({method_label})",
                "History & Shortages (B5)": history_display,
                "Batch Size": batch_str,
                "Recommended Cook Qty": f"**{dish.planned_quantity:.1f} {dish.unit}**",
                "Expected Surplus": f"{dish.expected_surplus_qty:.1f} {dish.unit}",
                "Confidence": conf_badge,
            })

        df_display = pd.DataFrame(table_rows)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # -------------------------------------------------------------------------
        # B6 Joint Demand Monte Carlo Simulation Breakdown
        # -------------------------------------------------------------------------
        with st.expander("🎲 B6 Joint Demand Monte-Carlo Simulation (Headcount × Appetite Uncertainty)", expanded=False):
            st.caption(
                "Monte-Carlo draws combine forecast headcount uncertainty H (via conformal residuals) "
                "with per-dish appetite distribution r (via bootstrap/censored rates) over 5,000 deterministic simulations."
            )
            mc_rows = []
            for dish in meal_plan.dishes:
                if dish.mc_demand:
                    mc = dish.mc_demand
                    fb_badge = "⚠️ Fallback Prior" if mc.is_fallback else "✅ Empirical Bootstrap"
                    mc_rows.append({
                        "Dish Name": dish.dish_name,
                        "Target (q)": f"{mc.service_level:.0%}",
                        "Expected Demand (Mean)": f"{mc.expected_demand:.1f} {mc.unit}",
                        "Median Demand (P50)": f"{mc.demand_p50:.1f} {mc.unit}",
                        "P90 Demand": f"{mc.demand_p90:.1f} {mc.unit}",
                        "P95 Demand": f"{mc.demand_p95:.1f} {mc.unit}",
                        "P99 Demand": f"{mc.demand_p99:.1f} {mc.unit}",
                        "Planned Cook Qty": f"{mc.planned_cook_quantity:.1f} {mc.unit}",
                        "P(Run-Out)": f"{mc.p_runout * 100.0:.1f}%",
                        "Expected Surplus": f"{mc.expected_surplus:.1f} {mc.unit}",
                        "Appetite Basis": fb_badge,
                    })
            if mc_rows:
                st.dataframe(pd.DataFrame(mc_rows), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # Plain-Language Kitchen Explanation Box
    # -------------------------------------------------------------------------
    st.markdown("### 🗣️ Kitchen Explanation & Manager Briefing")
    first_dish = meal_plan.dishes[0] if meal_plan.dishes else None
    dish_ex_sample = first_dish.explanation if first_dish else "No dishes planned."

    st.markdown(f"""
    <div class="explanation-box">
        <strong>Manager Operational Briefing:</strong><br>
        {meal_plan.summary_explanation}<br><br>
        <strong>Per-Dish Calculation Sample ({first_dish.dish_name if first_dish else 'N/A'}):</strong><br>
        {dish_ex_sample}
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Plan Persistence Action & Configuration
    # -------------------------------------------------------------------------
    st.markdown("---")
    col_act1, col_act2 = st.columns([2, 1])

    with col_act1:
        if st.button("💾 Save & Confirm Plan for Kitchen", type="primary", use_container_width=True):
            saved_pred = save_meal_plan(
                session=session,
                meal_date=target_date_str,
                meal_type=meal_type,
                plan_dict=meal_plan.to_dict(),
                service_level=meal_plan.service_level,
                is_synthetic=env_choice,
                who="kitchen_manager",
            )
            st.success(
                f"✅ Plan confirmed and recorded in Prediction Log & Audit Trail! "
                f"Prediction ID: {saved_pred.id if saved_pred else 'N/A'}. "
                f"Policy mode: {meal_plan.plan_mode}. "
                f"Logged at {datetime.now().strftime('%H:%M:%S')}."
            )

    with col_act2:
        if st.button("🔄 Refresh / Recalculate", use_container_width=True):
            st.rerun()

    # -------------------------------------------------------------------------
    # Consumption Rates & Audit Inspector (B5 Data Audit)
    # -------------------------------------------------------------------------
    with st.expander("🔍 Deep-Dive: Kaplan-Meier Shortage-Aware Learning Audit (B5 Data History)"):
        st.markdown(f"**Historical Observations Analyzed ({meal_plan.data_basis_label}):**")
        st.write(
            f"- Total Real Pilot Observations Analyzed: **{meal_plan.real_obs_count}**\n"
            f"- Total Synthetic Observations Analyzed: **{meal_plan.synthetic_obs_count}**"
        )

        all_rates = compute_dish_consumption_rates(session, meal_type=meal_type, is_synthetic=env_choice)
        audit_rows = []
        for d_id, rec in all_rates.items():
            km_info = rec.km_result
            audit_rows.append({
                "Dish": rec.dish_name,
                "Category": rec.category.title(),
                "Criticality Tier": rec.criticality_tier,
                "Estimated Rate": f"{rec.estimated_rate:.4f} {rec.unit}",
                "Estimation Method": rec.estimation_method.replace("_", " ").title(),
                "Total Meals": rec.num_observations,
                "Exact Meals (E=1)": rec.num_exact,
                "Ran-Out Meals (E=0)": rec.num_ran_out,
                "Ambiguous Zero Meals": rec.num_ambiguous,
                "Confidence": rec.confidence_status.title(),
                "Fallback Reason": rec.fallback_reason or "Unbiased Kaplan-Meier estimation",
            })
        st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)

finally:
    session.close()
