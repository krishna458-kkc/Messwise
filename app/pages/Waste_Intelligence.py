"""MessWise - Waste Intelligence & Analytics Dashboard (Module D: D1-D3).

Interactive operational interface for kitchen managers and mess committees:
- D1: Executive KPI Dashboard (Leftover kg, Waste % of cooked, Meals & Headcount, Service Level)
- D2: Interactive Pattern Charts (Waste by weekday, meal type, top dishes, and chronological trends)
- D3: Dish Performance Ranking (Highest waste, operational performers, honest operational suggestions)

Data-Honesty & Privacy First:
- Strictly isolates synthetic demonstration vs real pilot records.
- Never fabricates prices, student ratings, or fake popularity scores.
- Clear formulas and sample sizes displayed for all metrics.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Ensure root directory is on Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from messwise.db import Meal, get_data_environment_summary, get_session_factory, init_db
from messwise.intelligence import (
    aggregate_waste_by_dish,
    aggregate_waste_by_meal_type,
    aggregate_waste_by_weekday,
    aggregate_waste_trends,
    compute_dish_performance_rankings,
    compute_kpi_summary,
    compute_override_analytics,
    detect_dish_waste_anomalies,
    generate_root_cause_hypotheses,
    generate_weekly_operational_brief,
)

st.set_page_config(
    page_title="MessWise | Waste Intelligence",
    page_icon="📊",
    layout="wide",
)
init_db()

# Styling
st.markdown("""
<style>
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-title {
        font-size: 0.80rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
        line-height: 1.2;
    }
    .kpi-subtext {
        font-size: 0.82rem;
        color: #475569;
        margin-top: 4px;
    }
    .badge-synth {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-real {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-unverified {
        background-color: #fef2f2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Page Header
st.title("📊 Waste Intelligence & Analytics")
st.caption("Module D: Operational KPIs, Empirical Pattern Breakdown & Dish Ranking (PLAN.md Section 5)")

# Environment Discovery
session_factory = get_session_factory()
with session_factory() as check_session:
    env_summary = get_data_environment_summary(check_session)

has_real_records = env_summary["has_real_data"]
real_meals_count = env_summary["real_meals_count"]
synth_meals_count = env_summary["synthetic_meals_count"]
is_verified_pilot = env_summary["is_verified_pilot"]
unverified_count = env_summary["unverified_test_meals_count"]

# Data Environment Selector & Guard
if not has_real_records:
    env_choice = 1  # Strictly Synthetic Demo
    st.warning(
        f"🧪 **Synthetic Development Data — Demonstration Only**\n\n"
        f"• **Real pilot records: 0** (Real pilot mode is disabled until operational meals are logged in Kitchen mode).\n"
        f"• Displaying intelligence from **{synth_meals_count} synthetic demonstration meals** "
        f"for workflow testing and dashboard visualization."
    )
    col_env1, col_env2 = st.columns([2, 1])
    with col_env1:
        st.markdown(
            f"<div style='margin-top: 4px;'><strong>Active Environment:</strong> "
            f"<span class='badge-synth'>Synthetic Demonstration Dataset ({synth_meals_count} meals)</span></div>",
            unsafe_allow_html=True,
        )
    with col_env2:
        st.markdown(
            "<div style='text-align: right; color: #64748b; font-size: 0.84rem; margin-top: 4px;'>"
            "🔒 Real Pilot Data: <em>Unavailable (0 meals logged)</em></div>",
            unsafe_allow_html=True,
        )
else:
    col_env1, col_env2 = st.columns([2, 1])
    with col_env1:
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
            key="wi_env_choice",
        )
    with col_env2:
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

    if env_choice == 0 and not is_verified_pilot:
        st.warning(
            f"⚠️ **Unverified Manual Test Entries — Not Verified Pilot Data**\n\n"
            f"• Currently **{unverified_count} non-synthetic meals** exist in the database with status `verification_status: unverified_test`.\n"
            f"• These entries were logged during development/manual testing and have **not** been operator-confirmed as live pilot measurements.\n"
            f"• KPIs and waste breakdowns below reflect these test logs only, and cannot be used as verified pilot evidence or claimed as real food/cost savings."
        )

st.divider()

# Session context for queries
session = session_factory()

try:
    # -------------------------------------------------------------------------
    # D1: Operational KPI Dashboard
    # -------------------------------------------------------------------------
    st.subheader("🎯 Operational Waste KPIs (D1)")

    kpis = compute_kpi_summary(session=session, is_synthetic=env_choice)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Recorded Leftover</div>
            <div class="kpi-value" style="color: #b91c1c;">{kpis.total_leftover_kg:.1f} kg</div>
            <div class="kpi-subtext">Across {kpis.total_cooked_kg:.1f} kg Total Cooked Food</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        rate_color = "#16a34a" if kpis.waste_percentage < 8.0 else ("#d97706" if kpis.waste_percentage < 15.0 else "#dc2626")
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Overall Waste Rate</div>
            <div class="kpi-value" style="color: {rate_color};">{kpis.waste_percentage:.1f}%</div>
            <div class="kpi-subtext">Leftover kg ÷ Cooked kg (Target: &lt; 8.0%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Meals & Turnout Logged</div>
            <div class="kpi-value">{kpis.total_meals_count} meals</div>
            <div class="kpi-subtext">{kpis.total_headcount_served:,} Students Served ({kpis.total_dish_logs_count} dish logs)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        sl_color = "#16a34a" if kpis.service_level_achieved >= 0.95 else "#d97706"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Service Level Achieved</div>
            <div class="kpi-value" style="color: {sl_color};">{kpis.service_level_achieved * 100:.1f}%</div>
            <div class="kpi-subtext">{kpis.shortage_incidents_count} Ran-Out Incident(s) Recorded</div>
        </div>
        """, unsafe_allow_html=True)

    # Transparency Disclosures
    with st.expander("ℹ️ Metric Formulas & Operational Disclosures (PLAN.md Section 9.1)", expanded=False):
        c_note1, c_note2 = st.columns(2)
        with c_note1:
            st.markdown(f"""
            - **Waste Rate Formula:** `(Leftover kg ÷ Cooked kg) × 100` on weight/volume records.
            - **Service Level Formula:** `1 - (Dish-meals that ran out ÷ All dish-meals)`.
            - **Evaluated Predictions:** {kpis.forecast_eval_count} prediction(s) with logged actual turnout.
              - Forecast WAPE: `{kpis.forecast_wape if kpis.forecast_wape is not None else 'N/A'}`
              - Forecast MAE: `{kpis.forecast_mae if kpis.forecast_mae is not None else 'N/A'} students`
            """)
        with c_note2:
            st.markdown(f"""
            - **Financial Cost Transparency:** `{kpis.cost_status_note}` (Prices are never fabricated).
            - **Popularity Disclaimers:** `{kpis.popularity_status_note}` (Low leftover does not equal high rating).
            - **Date Window:** `{kpis.date_range_start or 'N/A'}` to `{kpis.date_range_end or 'N/A'}`.
            """)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # D2: Interactive Pattern Breakdown Charts (Plotly)
    # -------------------------------------------------------------------------
    st.subheader("📈 Empirical Waste Patterns (D2)")

    tab_weekday, tab_slot, tab_dish, tab_trend = st.tabs([
        "📅 Waste by Weekday",
        "🕒 Waste by Meal Slot",
        "🍲 Waste by Dish",
        "📊 Longitudinal Trends",
    ])

    with tab_weekday:
        df_weekday = aggregate_waste_by_weekday(session=session, is_synthetic=env_choice)
        if df_weekday.empty or df_weekday["leftover_kg"].sum() == 0:
            st.info("No weekday waste data available for the active environment.")
        else:
            fig_w = go.Figure()
            fig_w.add_trace(go.Bar(
                x=df_weekday["weekday_name"],
                y=df_weekday["leftover_kg"],
                name="Leftover (kg)",
                marker_color="#3b82f6",
                text=[f"{v:.1f} kg" for v in df_weekday["leftover_kg"]],
                textposition="auto",
            ))
            fig_w.add_trace(go.Scatter(
                x=df_weekday["weekday_name"],
                y=df_weekday["waste_pct"],
                name="Waste Rate (%)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#ef4444", width=3),
                marker=dict(size=8),
            ))
            fig_w.update_layout(
                title="Total Leftover Quantity & Waste Percentage by Weekday",
                xaxis_title="Day of Week",
                yaxis=dict(title="Total Leftover (kg)"),
                yaxis2=dict(title="Waste Rate (%)", overlaying="y", side="right", rangemode="tozero"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=380,
                margin=dict(l=40, r=40, t=50, b=40),
            )
            st.plotly_chart(fig_w, use_container_width=True)

    with tab_slot:
        df_slot = aggregate_waste_by_meal_type(session=session, is_synthetic=env_choice)
        if df_slot.empty or df_slot["leftover_kg"].sum() == 0:
            st.info("No meal slot data available for the active environment.")
        else:
            fig_s = px.bar(
                df_slot,
                x="meal_type",
                y="leftover_kg",
                color="waste_pct",
                color_continuous_scale="Reds",
                title="Leftover Waste (kg) Across Meal Slots",
                labels={"meal_type": "Meal Slot", "leftover_kg": "Leftover (kg)", "waste_pct": "Waste %"},
                text_auto=".1f",
            )
            fig_s.update_layout(height=380, margin=dict(l=40, r=40, t=50, b=40))
            st.plotly_chart(fig_s, use_container_width=True)

    with tab_dish:
        df_dishes = aggregate_waste_by_dish(session=session, is_synthetic=env_choice, top_n=10)
        if df_dishes.empty:
            st.info("No dish records available.")
        else:
            fig_d = px.bar(
                df_dishes.sort_values(by="total_leftover", ascending=True),
                x="total_leftover",
                y="dish_name",
                orientation="h",
                color="category",
                title="Top 10 Dishes by Total Leftover Quantity (kg/L)",
                labels={"total_leftover": "Total Leftover Quantity", "dish_name": "Dish Name", "category": "Category"},
                text_auto=".1f",
            )
            fig_d.update_layout(height=420, margin=dict(l=40, r=40, t=50, b=40))
            st.plotly_chart(fig_d, use_container_width=True)

    with tab_trend:
        df_trends = aggregate_waste_trends(session=session, is_synthetic=env_choice)
        if df_trends.empty:
            st.info("No timeline records available.")
        else:
            fig_t = go.Figure()
            fig_t.add_trace(go.Scatter(
                x=df_trends["date"] + " (" + df_trends["meal_type"] + ")",
                y=df_trends["leftover_kg"],
                mode="lines+markers",
                name="Leftover (kg)",
                line=dict(color="#f97316", width=2.5),
            ))
            fig_t.add_trace(go.Bar(
                x=df_trends["date"] + " (" + df_trends["meal_type"] + ")",
                y=df_trends["headcount"],
                name="Turnout Headcount",
                yaxis="y2",
                marker_color="rgba(148, 163, 184, 0.3)",
            ))
            fig_t.update_layout(
                title="Chronological Leftover Volume & Attendance Timeline",
                xaxis=dict(title="Meal (Date + Slot)", tickangle=-45),
                yaxis=dict(title="Leftover (kg)"),
                yaxis2=dict(title="Turnout Headcount", overlaying="y", side="right", rangemode="tozero"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=420,
                margin=dict(l=40, r=40, t=50, b=80),
            )
            st.plotly_chart(fig_t, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # D3: Dish Performance Ranking & Grounded Review Hypotheses
    # -------------------------------------------------------------------------
    st.subheader("📋 Dish Performance Ranking & Review (D3)")
    st.caption("Empirical ranking of dishes to identify high-surplus items and operational clearance profiles (PLAN.md Section 5)")

    rankings = compute_dish_performance_rankings(session=session, is_synthetic=env_choice)

    col_rank1, col_rank2 = st.columns(2)

    with col_rank1:
        st.markdown("#### 🚨 Highest Surplus Volume Dishes")
        hw_list = rankings["highest_waste_dishes"]
        if not hw_list:
            st.info("No high-waste dishes recorded.")
        else:
            for item in hw_list:
                st.markdown(f"""
                <div style="background:#fff; border:1px solid #fee2e2; border-left:4px solid #ef4444; border-radius:6px; padding:12px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{item['dish_name']}</strong>
                        <span style="color:#b91c1c; font-weight:700;">{item['total_leftover']:.1f} {item['unit']} left ({item['waste_percentage']:.1f}%)</span>
                    </div>
                    <div style="font-size:0.83rem; color:#64748b; margin-top:2px;">
                        Category: {item['category'].title()} • Cooked: {item['total_cooked']:.1f} {item['unit']} across {item['observations_count']} meal(s)
                    </div>
                    <div style="font-size:0.84rem; color:#475569; margin-top:6px;">
                        💡 <em>{item['recommendation_note']}</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col_rank2:
        st.markdown("#### 🟢 High Operational Clearance Profiles")
        perf_list = rankings["operational_performers"]
        if not perf_list:
            st.info("No operational clearance performers found.")
        else:
            for item in perf_list:
                st.markdown(f"""
                <div style="background:#fff; border:1px solid #dcfce7; border-left:4px solid #16a34a; border-radius:6px; padding:12px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>{item['dish_name']}</strong>
                        <span style="color:#15803d; font-weight:700;">{item['waste_percentage']:.1f}% leftover ({item['total_leftover']:.1f} {item['unit']})</span>
                    </div>
                    <div style="font-size:0.83rem; color:#64748b; margin-top:2px;">
                        Category: {item['category'].title()} • Cooked: {item['total_cooked']:.1f} {item['unit']} across {item['observations_count']} meal(s)
                    </div>
                    <div style="font-size:0.84rem; color:#475569; margin-top:6px;">
                        ✓ <em>{item['recommendation_note']}</em>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.info(f"📌 **Data Integrity & Scientific Candor Note**: {rankings['data_limitation_note']}")

    # -------------------------------------------------------------------------
    # D4 & D5: Statistical Anomaly Detection & Operational Root-Cause Hypotheses
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("🔬 Statistical Anomaly Detection & Root-Cause Hypotheses (D4 & D5)")
    st.caption(
        "Robust z-score anomaly screening (z = 0.6745 * (x - median) / MAD, threshold |z| > 3.5, min 6 history) "
        "paired with transparent operational hypotheses for manager review (PLAN.md Section 8.9)."
    )

    anom_col1, anom_col2 = st.columns([1.2, 1.8])

    with anom_col1:
        st.markdown("#### 🚨 Flagged Waste Anomalies (D4)")
        all_anomalies = detect_dish_waste_anomalies(session=session, is_synthetic=env_choice)
        flagged = [a for a in all_anomalies if a.is_anomaly]
        insufficient = [a for a in all_anomalies if a.status == "insufficient_history"]

        if flagged:
            for anom in flagged[:5]:
                st.error(
                    f"**{anom.dish_name}** ({anom.meal_date} {anom.meal_type}): "
                    f"Waste rate **{anom.observed_waste_pct:.1f}%** vs historical median **{anom.historical_median_pct:.1f}%** "
                    f"(z = {anom.z_score:+.2f}, MAD = {anom.mad_val:.1f})."
                )
        else:
            st.success("✅ No statistical waste anomalies flagged (|z| > 3.5).")

        if insufficient:
            st.caption(f"ℹ️ {len(insufficient)} dish logs marked as insufficient history (< 6 observations required).")

    with anom_col2:
        st.markdown("#### 💡 Operational Root-Cause Hypotheses (D5)")
        recent_meals_q = (
            session.query(Meal)
            .filter(Meal.is_synthetic == env_choice)
            .order_by(Meal.date.desc())
            .limit(4)
            .all()
        )
        found_hypotheses = False
        for rm in recent_meals_q:
            hyps = generate_root_cause_hypotheses(session=session, meal_id=rm.id)
            for h in hyps:
                found_hypotheses = True
                st.markdown(f"""
                <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:4px solid #3b82f6; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
                    <div style="font-weight:700; color:#1e293b;">{rm.date} {rm.meal_type.title()} — {h.hypothesis_shown}</div>
                    <div style="font-size:0.82rem; color:#64748b; margin-top:2px;">Pattern: {h.pattern_observed}</div>
                    <div style="font-size:0.84rem; color:#0f766e; margin-top:4px;"><strong>Suggested Action:</strong> {h.suggested_action}</div>
                    <div style="font-size:0.75rem; color:#94a3b8; margin-top:2px;"><em>Label: {h.confidence_label} ({h.trigger_metric})</em></div>
                </div>
                """, unsafe_allow_html=True)
        if not found_hypotheses:
            st.info("No active pattern alerts for recent meals. Operational patterns appear stable.")

    # -------------------------------------------------------------------------
    # D6: Kitchen Override Analytics
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("⚖️ Kitchen Staff Override Analytics (D6)")
    st.caption("Tracks staff modifications to automated quantity recommendations with recorded reasons and outcomes (PLAN.md Section 8.9).")

    ov_data = compute_override_analytics(session=session, is_synthetic=env_choice)

    oc1, oc2, oc3, oc4 = st.columns(4)
    with oc1:
        st.metric("Total Recorded Overrides", ov_data.total_overrides)
    with oc2:
        st.metric("Override Rate", f"{ov_data.override_rate_pct:.1f}%")
    with oc3:
        st.metric("Avg Override Delta", f"{ov_data.avg_delta_qty:+.1f} units")
    with oc4:
        st.metric("Positive vs Negative", f"+{ov_data.net_positive_overrides} / -{ov_data.net_negative_overrides}")

    if ov_data.reasons_breakdown:
        st.markdown("**Override Reasons Breakdown:**")
        df_reasons = pd.DataFrame([
            {"Reason": r, "Frequency": count}
            for r, count in sorted(ov_data.reasons_breakdown.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(df_reasons, use_container_width=True, hide_index=True)
    st.caption(f"📊 **Outcome Assessment**: {ov_data.outcome_comparison_note}")

    # -------------------------------------------------------------------------
    # D7: Automatic Weekly Operational Brief
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📰 Automatic Weekly Operational Brief (D7)")
    st.caption("Deterministic template-based executive summary generated directly from verified database records (no external LLM keys required).")

    brief = generate_weekly_operational_brief(session=session, is_synthetic=env_choice)

    with st.expander("📄 View Full Weekly Operational Intelligence Brief", expanded=True):
        st.markdown(f"### {brief.report_title}")
        st.markdown(f"**Period**: {brief.date_range_label} &nbsp;|&nbsp; **Provenance**: `{brief.environment_label}`")
        st.write(brief.brief_narrative)

        if brief.top_wasted_dishes:
            st.markdown(f"- **Top Surplus Items Under Review**: {', '.join(brief.top_wasted_dishes)}")
        if brief.chief_operational_hypotheses:
            st.markdown("- **Chief Operational Pattern Hypotheses**:")
            for ch in brief.chief_operational_hypotheses:
                st.markdown(f"  - {ch}")

        st.caption(f"⚠️ **Data Governance Warning**: {brief.data_quality_warning}")

finally:
    session.close()
