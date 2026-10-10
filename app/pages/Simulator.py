"""MessWise — Module E: Savings Simulator (E3) & Blind Forecast Reveal (E4).

Demonstrates the core MessWise feedback loop:
PREDICT -> PLAN -> COOK -> MEASURE -> LEARN

Guarantees:
1. Zero look-ahead leakage: pre-cutoff history only.
2. Strict isolation of synthetic vs. real pilot data.
3. Unit-compatible comparisons (kg, L, count never summed across incompatible units).
4. Shortage candor: actual ran-out events flagged as right-censored appetite.
5. Missing cost disclosure: never invents rupee savings when ingredient prices are unconfigured.
6. Two-stage Blind Forecast Reveal: freezes predictions before outcome disclosure.
"""

from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import select

from messwise.db import get_session_factory, Meal, Dish, get_data_environment_summary
from messwise.simulator import (
    run_savings_simulation,
    generate_blind_forecast,
    reveal_blind_forecast,
    BlindForecastState,
    SavingsSimulationReport,
)

st.set_page_config(
    page_title="MessWise | Simulator & Blind Reveal",
    page_icon="🎮",
    layout="wide",
)

# Top Header
st.title("🎮 Simulator & Blind Forecast Reveal")
st.caption("Module E: Historical Savings Replay (E3) and Pre-Cutoff Blind Reveal (E4)")

# Sidebar Environment Selector
st.sidebar.header("Data Environment")
env_choice = st.sidebar.radio(
    "Active Environment",
    ["Synthetic Demonstration", "Real Pilot Records"],
    index=0,
    help="Isolate synthetic test data (is_synthetic=1) from verified real pilot data (is_synthetic=0).",
)
is_synthetic = 1 if env_choice == "Synthetic Demonstration" else 0

# Database Session
session_factory = get_session_factory()
session = session_factory()

# Data Environment Summary Check
env_summary = get_data_environment_summary(session)
real_count = env_summary.get("real", {}).get("total_meals", 0)
synth_count = env_summary.get("synthetic", {}).get("total_meals", 0)

if is_synthetic == 1:
    st.info(
        f"🔬 **Synthetic Demonstration ({synth_count} Meals Available)**: "
        "Running in synthetic test mode. Replay evaluates simulated recommendations against generated history. "
        "These figures demonstrate methodology and must NOT be cited as real-world operational savings."
    )
else:
    if real_count == 0:
        st.warning(
            "⚠️ **Zero Real Pilot Records (0 Meals Available)**: "
            "No real pilot records exist in the database yet. "
            "In strict compliance with PLAN.md Section 8 data-honesty safeguards, "
            "no real-world food savings, financial gains, or pilot efficacy claims can be generated."
        )
    else:
        st.success(f"🌱 **Real Pilot Environment ({real_count} Meals Available)**: Querying live kitchen records.")

# Main Navigation Tabs
tab_reveal, tab_sim = st.tabs(["🎯 Blind Forecast Reveal (E4)", "📊 Historical Savings Simulator (E3)"])

# ==============================================================================
# TAB 1: BLIND FORECAST REVEAL (E4)
# ==============================================================================
with tab_reveal:
    st.markdown("### 🎯 Blind Forecast & Cooking Plan Reveal")
    st.markdown(
        "Demonstrates MessWise forecast candor. "
        "Select a historical meal, review context available **before** decision time, "
        "freeze the prediction and cooking plan, then reveal actual outcomes to audit accuracy."
    )

    # 1. Fetch eligible historical meals
    meals_stmt = (
        select(Meal)
        .where(Meal.is_synthetic == is_synthetic)
        .order_by(Meal.date.desc(), Meal.id.desc())
    )
    available_meals = session.execute(meals_stmt).scalars().all()

    if not available_meals:
        st.info(f"No historical meals found in active environment ({env_choice}).")
    else:
        # Meal Selector
        meal_options = {
            f"Meal #{m.id} | {m.date} | {m.meal_type.title()} (Recorded: {m.date})": m.id
            for m in available_meals
        }
        selected_label = st.selectbox(
            "Select Historical Meal to Audit:",
            list(meal_options.keys()),
            key="reveal_meal_select",
        )
        selected_meal_id = meal_options[selected_label]
        target_meal = session.execute(select(Meal).where(Meal.id == selected_meal_id)).scalar_one()

        # Service level selection with B3 presets
        st.markdown("#### Service-Level Planning Target")
        col_preset1, col_preset2, col_preset3, col_custom = st.columns([1, 1, 1, 3])
        if "blind_sl_preset" not in st.session_state:
            st.session_state["blind_sl_preset"] = 0.95

        with col_preset1:
            if st.button("90% Preset (Lean)", key="blind_p90"):
                st.session_state["blind_sl_preset"] = 0.90
        with col_preset2:
            if st.button("95% Preset (Standard)", key="blind_p95"):
                st.session_state["blind_sl_preset"] = 0.95
        with col_preset3:
            if st.button("99% Preset (Safety)", key="blind_p99"):
                st.session_state["blind_sl_preset"] = 0.99

        with col_custom:
            service_level_reveal = st.slider(
                "Service Level Target (Coverage Probability)",
                min_value=0.50,
                max_value=0.999,
                value=float(st.session_state["blind_sl_preset"]),
                step=0.01,
                format="%.2f",
                key="blind_sl_slider",
            )

        # Stage 1: Pre-Meal Information Display (Strictly masking outcomes)
        st.markdown("---")
        st.markdown("#### Stage 1: Pre-Meal Context (Legitimately Known Prior to Service)")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Target Date", target_meal.date)
        c2.metric("Meal Type", target_meal.meal_type.title())
        c3.metric("Hostel Strength", target_meal.hostel_strength)
        day_name = pd.to_datetime(target_meal.date).strftime("%A")
        c4.metric("Day of Week", day_name)

        flag_cols = st.columns(4)
        flag_cols[0].write(f"📅 **Exam Flag**: {'Yes' if target_meal.exam_flag else 'No'}")
        flag_cols[1].write(f"🎉 **Event Flag**: {'Yes' if target_meal.event_flag else 'No'}")
        flag_cols[2].write(f"🏖️ **Holiday Flag**: {'Yes' if target_meal.holiday_flag else 'No'}")
        flag_cols[3].write(f"🌡️ **Weather**: {target_meal.temp_c or 28}°C | {target_meal.rain_mm or 0}mm rain")

        st.caption("🔒 **Integrity Guard**: Actual student headcount, cooked dishes, leftovers, and shortages are masked.")

        # Stage 2 Action: Generate Blind Forecast
        if st.button("🔮 Generate Blind Forecast & Cooking Plan", type="primary", key="btn_gen_blind"):
            with st.spinner("Generating blind forecast and cooking plan using pre-cutoff data..."):
                blind_state = generate_blind_forecast(
                    session=session,
                    meal_id=selected_meal_id,
                    service_level=service_level_reveal,
                    hostel_strength=target_meal.hostel_strength,
                )
                st.session_state["current_blind_state"] = blind_state
                st.session_state["blind_revealed"] = False

        # If a blind state is active for this meal
        if "current_blind_state" in st.session_state and st.session_state["current_blind_state"].meal_id == selected_meal_id:
            blind_state: BlindForecastState = st.session_state["current_blind_state"]

            if not blind_state.is_eligible:
                st.warning(f"⚠️ **Ineligible Meal**: {blind_state.ineligibility_reason}")
            else:
                st.markdown("---")
                st.markdown("#### Stage 2: Frozen Prediction & Operational Plan")
                st.info(f"❄️ **Plan Frozen at {blind_state.frozen_timestamp}**. Actual outcomes remain hidden until you click reveal.")

                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                f_col1.metric("Central Forecast (H_hat)", f"{blind_state.h_hat} students")
                f_col2.metric("80% Uncertainty Interval", f"[{blind_state.h_lo}, {blind_state.h_hi}]")
                f_col3.metric("Service Planning Headcount (H_q)", f"{blind_state.h_q} students")
                b_text = f"Lag-7: {blind_state.baseline_lag7 or 'N/A'} | Trailing: {blind_state.baseline_trailing_avg or 'N/A'}"
                f_col4.metric("Honest Baselines", b_text)

                st.write(f"**Forecasting Explanation**: {blind_state.explanation}")

                # Planned Dishes Table
                st.markdown("##### Recommended Cooking Quantities")
                plan_rows = []
                for p in blind_state.planned_dishes:
                    plan_rows.append({
                        "Dish": p["dish_name"],
                        "Category": p["category"].title(),
                        "Learned Rate": f"{p['per_head_rate']:.3f} {p['unit']}/head",
                        "Planned Cooking Qty": f"{p['planned_cooking_qty']} {p['unit']}",
                        "Batch Size": f"{p['batch_size']} {p['unit']}" if p["batch_size"] else "Standard",
                        "Expected Surplus": f"{p['expected_surplus']} {p['unit']}",
                        "Run-Out Risk": p["run_out_risk"],
                    })
                st.dataframe(pd.DataFrame(plan_rows), use_container_width=True)

                # Stage 3 Action: Reveal Actual Outcome
                st.markdown("---")
                st.markdown("#### Stage 3: Audit & Comparison Reveal")
                
                if st.button("🔓 Reveal Actual Outcome", type="secondary", key="btn_reveal"):
                    with st.spinner("Revealing actual measured outcomes and auditing predictions..."):
                        revealed_state = reveal_blind_forecast(session=session, frozen_state=blind_state)
                        st.session_state["current_blind_state"] = revealed_state
                        st.session_state["blind_revealed"] = True

                # Display Revealed Results
                if st.session_state.get("blind_revealed", False) and blind_state.is_revealed:
                    st.success("✅ **Actual Outcomes Revealed**")
                    
                    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                    r_col1.metric("Actual Attendance", f"{blind_state.actual_headcount} students")
                    err_sign = "+" if (blind_state.forecast_error or 0) > 0 else ""
                    r_col2.metric("Forecast Error (H_hat - Actual)", f"{err_sign}{blind_state.forecast_error}")
                    r_col3.metric("Absolute Error", f"{blind_state.abs_forecast_error} students")
                    cov_label = "Inside 80% Interval ✅" if blind_state.inside_interval else "Outside Interval ⚠️"
                    r_col4.metric("Interval Coverage", cov_label)

                    st.markdown(f"**Outcome Assessment**: {blind_state.evaluation_summary}")

                    # Comparison Chart: MessWise vs Baselines vs Actual
                    chart_labels = ["MessWise Forecast", "Actual Attendance"]
                    chart_vals = [blind_state.h_hat, blind_state.actual_headcount]
                    chart_colors = ["#2563EB", "#10B981"]

                    if blind_state.baseline_lag7 is not None:
                        chart_labels.append("Baseline (Lag-7)")
                        chart_vals.append(blind_state.baseline_lag7)
                        chart_colors.append("#6B7280")
                    if blind_state.baseline_trailing_avg is not None:
                        chart_labels.append("Baseline (Trailing Avg)")
                        chart_vals.append(blind_state.baseline_trailing_avg)
                        chart_colors.append("#9CA3AF")

                    fig_compare = go.Figure(data=[
                        go.Bar(
                            x=chart_labels,
                            y=chart_vals,
                            marker_color=chart_colors,
                            text=[str(v) for v in chart_vals],
                            textposition="auto",
                        )
                    ])
                    fig_compare.update_layout(
                        title="Headcount Comparison: Model vs Baselines vs Actual Attendance",
                        yaxis_title="Students",
                        template="plotly_white",
                        height=350,
                    )
                    st.plotly_chart(fig_compare, use_container_width=True)

                    # Dish-by-Dish Cooking Outcome Comparison
                    st.markdown("##### Dish-Level Operational Audit")
                    outcome_rows = []
                    for o in blind_state.dish_outcomes:
                        c_qty_str = f"{o['actual_cooked_qty']} {o['unit']}" if o['actual_cooked_qty'] is not None else "Not Logged"
                        diff_str = f"{o['diff_qty']:+.2f} {o['unit']}" if o['diff_qty'] is not None else "N/A"
                        left_str = f"{o['actual_leftover_qty']} {o['unit']}" if o['actual_leftover_qty'] is not None else "N/A"
                        ran_str = "Yes ⚠️ (Ran Out)" if o['actual_ran_out'] else "No"
                        risk_str = "Shortage Risk ⚠️" if o['shortage_risk'] else "Safe"
                        outcome_rows.append({
                            "Dish": o["dish_name"],
                            "MessWise Planned": f"{o['planned_qty']} {o['unit']}",
                            "Actual Cooked": c_qty_str,
                            "Quantity Difference": diff_str,
                            "Actual Leftovers": left_str,
                            "Ran Out in Reality?": ran_str,
                            "Simulated Plan Sufficiency": risk_str,
                        })
                    st.dataframe(pd.DataFrame(outcome_rows), use_container_width=True)

                    if blind_state.actual_shortage_occurred:
                        st.warning(
                            "⚠️ **Right-Censored Appetite Notice**: One or more dishes ran out during service. "
                            "Actual recorded consumption represents a lower bound and does not reflect true unconstrained demand."
                        )


# ==============================================================================
# TAB 2: SAVINGS SIMULATOR (E3)
# ==============================================================================
with tab_sim:
    st.markdown("### 📊 Historical Savings Simulator")
    st.markdown(
        "Replays historical meals as if MessWise had planned them using **strictly prior information**. "
        "Evaluates potential cooking quantity adjustments, isolates compatible units, and reports actual shortages."
    )

    # Date range and filter controls
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        meal_type_filter = st.selectbox(
            "Meal Type Filter",
            ["All", "breakfast", "lunch", "snacks", "dinner"],
            key="sim_meal_filter",
        )
    with col_f2:
        sim_service_level = st.slider(
            "Target Service Level",
            min_value=0.50,
            max_value=0.999,
            value=0.95,
            step=0.01,
            key="sim_service_level",
        )
    with col_f3:
        sim_start_date = st.text_input("Start Date (YYYY-MM-DD)", value="", key="sim_start")
    with col_f4:
        sim_end_date = st.text_input("End Date (YYYY-MM-DD)", value="", key="sim_end")

    if st.button("🚀 Run Historical Savings Replay", type="primary", key="btn_run_sim"):
        with st.spinner("Replaying historical decisions without look-ahead leakage..."):
            report = run_savings_simulation(
                session=session,
                is_synthetic=is_synthetic,
                start_date=sim_start_date.strip() or None,
                end_date=sim_end_date.strip() or None,
                meal_type=meal_type_filter if meal_type_filter != "All" else None,
                service_level=sim_service_level,
            )
            st.session_state["savings_report"] = report

    # Render Simulation Report
    if "savings_report" in st.session_state:
        report: SavingsSimulationReport = st.session_state["savings_report"]

        st.markdown("---")
        st.markdown(f"#### Simulation Results ({report.environment_label})")

        # Top-level replay counts
        kpi_cols = st.columns(5)
        kpi_cols[0].metric("Total Meals Replayed", report.total_meals_replayed)
        kpi_cols[1].metric("Evaluable Meals", report.meals_evaluable)
        kpi_cols[2].metric("Excluded (Cold Start)", report.meals_excluded)
        kpi_cols[3].metric("Actual Historical Shortages", report.actual_shortage_events_count)
        kpi_cols[4].metric("Simulated Shortage Risks", report.simulated_shortage_risk_count)

        # Financial Status Card
        st.info(f"💰 **Financial Assessment**: {report.cost_status_message}")

        if not report.has_sufficient_data:
            st.warning("No evaluable meals found. Historical meals may lack the required 3-meal pre-cutoff history.")
        else:
            # Breakdown by Strictly Compatible Units
            st.markdown("#### Quantity Breakdown by Measurement Unit")
            st.caption("Kilograms (kg), Litres (L), and Item Counts are strictly separated and never aggregated together.")

            unit_tabs = st.tabs([f"Unit: {u.upper()}" for u in sorted(report.totals_by_unit.keys())])
            for idx, u in enumerate(sorted(report.totals_by_unit.keys())):
                u_stats = report.totals_by_unit[u]
                with unit_tabs[idx]:
                    u_col1, u_col2, u_col3, u_col4 = st.columns(4)
                    u_col1.metric("Recorded Cooked Quantity", f"{u_stats['actual_cooked']:.1f} {u}")
                    u_col2.metric("MessWise Recommended Qty", f"{u_stats['simulated_recommended']:.1f} {u}")
                    red_sign = "+" if u_stats['potential_reduction'] > 0 else ""
                    u_col3.metric(
                        "Potential Quantity Reduction",
                        f"{red_sign}{u_stats['potential_reduction']:.1f} {u}",
                        help="Theoretical difference: Recorded Cooked minus MessWise Recommended.",
                    )
                    u_col4.metric("Recorded Actual Leftovers", f"{u_stats['actual_leftovers']:.1f} {u}")

                    # Bar chart comparison for this unit
                    fig_unit = go.Figure(data=[
                        go.Bar(
                            name="Actual Cooked",
                            x=["Aggregate"],
                            y=[u_stats['actual_cooked']],
                            marker_color="#DC2626",
                        ),
                        go.Bar(
                            name="MessWise Recommended",
                            x=["Aggregate"],
                            y=[u_stats['simulated_recommended']],
                            marker_color="#2563EB",
                        ),
                        go.Bar(
                            name="Recorded Leftovers",
                            x=["Aggregate"],
                            y=[u_stats['actual_leftovers']],
                            marker_color="#F59E0B",
                        ),
                    ])
                    fig_unit.update_layout(
                        barmode="group",
                        title=f"Total Quantities Comparison ({u.upper()})",
                        yaxis_title=f"Quantity ({u})",
                        height=280,
                        template="plotly_white",
                    )
                    st.plotly_chart(fig_unit, use_container_width=True)

            # Detailed Meal Audit Table
            st.markdown("#### Detailed Historical Replay Log")
            meal_audit_rows = []
            for m in report.replayed_meals:
                meal_audit_rows.append({
                    "Meal ID": m.meal_id,
                    "Date": m.meal_date,
                    "Meal Type": m.meal_type.title(),
                    "Pre-Cutoff History": f"{m.pre_cutoff_meals_count} meals",
                    "Status": "Evaluable" if m.is_evaluable else "Excluded",
                    "Actual Headcount": m.actual_headcount,
                    "Forecast Headcount": str(m.forecast_headcount) if m.forecast_headcount is not None else "N/A",
                    "Actual Shortage?": "Yes ⚠️" if m.actual_shortage_event else "No",
                    "Sim Shortage Risk?": "Risk ⚠️" if m.simulated_shortage_risk_event else "Safe",
                    "Exclusion Note": m.exclusion_reason or "None",
                })
            st.dataframe(pd.DataFrame(meal_audit_rows), use_container_width=True)

        # Candor Disclosures
        st.markdown("---")
        st.markdown("#### 🛡️ Candor Disclosures & Methodological Honesty")
        for disc in report.candor_disclosures:
            st.write(f"- {disc}")

# Close DB session
session.close()
