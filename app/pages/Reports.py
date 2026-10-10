"""MessWise - Pilot Evidence Reports & Governance (Module E: E2 & Module I).

Implements the pilot before/after evidence methodology specified in PLAN.md Section 5 (Module E),
Section 9.1 & 9.2 (Statistical treatment of the pilot):
- E2: Matched weekday x meal comparison between baseline and pilot periods
- Nonparametric bootstrap 95% confidence intervals (fixed seed 42)
- Event-day separation (exams, events, holidays excluded from matched pairs)
- Service-level preservation check (proves waste reduction did not cause shortages)
- Strict Data Honesty Guard: reports 'Insufficient Real Pilot Data' when 0 real records exist

Also preserves Module I system audit log for governance and data integrity.
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Ensure root directory is on Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select

from messwise.db import AuditLog, get_data_environment_summary, get_session_factory, init_db
from messwise.reports import compute_pilot_evidence_report

st.set_page_config(
    page_title="MessWise | Pilot Reports & Evidence",
    page_icon="📑",
    layout="wide",
)
init_db()

# Custom CSS
st.markdown("""
<style>
    .report-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .report-title {
        font-size: 0.80rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .report-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
        line-height: 1.2;
    }
    .report-sub {
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
</style>
""", unsafe_allow_html=True)

st.title("📑 Pilot Evidence Report & Governance")
st.caption("Module E2: Before/After Matched Pair Evaluation & Module I Audit Trail (PLAN.md Section 5 & 9)")

# Database Environment Inspection
session_factory = get_session_factory()
with session_factory() as check_session:
    env_summary = get_data_environment_summary(check_session)

has_real_records = env_summary["has_real_data"]
real_meals_count = env_summary["real_meals_count"]
synth_meals_count = env_summary["synthetic_meals_count"]

st.markdown("### 🔬 Pilot Before/After Evidence (E2)")

if not has_real_records:
    # Strict Data Honesty Banner
    st.error(
        f"🔒 **Insufficient Real Pilot Data — 0 Operational Meals Logged**\n\n"
        f"• Real pilot records in database: **0**.\n"
        f"• The formal Pilot Evidence Report (E2) cannot evaluate real-world food savings, emissions avoided, "
        f"or statistical significance until actual kitchen measurements are recorded via Kitchen mode.\n"
        f"• MessWise adheres strictly to scientific candor: no fake savings or fabricated confidence intervals "
        f"are reported for real operations."
    )

    demo_mode = st.checkbox(
        "🧪 Inspect Synthetic Demonstration Methodology (Demonstration Workflow Only)",
        value=True,
        help="Runs matched-pair before/after evaluation on synthetic development records to verify statistical algorithms.",
    )

    if not demo_mode:
        st.info("Select the demonstration checkbox above to review the statistical evaluation pipeline.")
        eval_env = None
    else:
        eval_env = 1
        st.markdown(
            f"<div style='margin-bottom: 12px;'><span class='badge-synth'>"
            f"▲ Active Evaluation Mode: Synthetic Development Records ({synth_meals_count} meals) — Demonstration Only</span></div>",
            unsafe_allow_html=True,
        )
else:
    eval_choice = st.radio(
        "Select Evidence Evaluation Target:",
        options=[0, 1],
        format_func=lambda x: (
            env_summary["real_env_label"]
            if x == 0
            else f"🧪 Synthetic Workflow Demonstration ({synth_meals_count} demonstration meals)"
        ),
        index=1 if not env_summary["is_verified_pilot"] else 0,
        horizontal=True,
    )
    eval_env = eval_choice

if eval_env is not None:
    # Date window selector
    if eval_env == 1:
        # Synthetic date range is 2026-10-01 to 2026-10-07
        def_b_start, def_b_end = date(2026, 10, 1), date(2026, 10, 4)
        def_p_start, def_p_end = date(2026, 10, 5), date(2026, 10, 7)
    else:
        t_now = date.today()
        def_b_start, def_b_end = t_now - timedelta(days=14), t_now - timedelta(days=8)
        def_p_start, def_p_end = t_now - timedelta(days=7), t_now

    col_win1, col_win2 = st.columns(2)
    with col_win1:
        st.markdown("**1. Baseline Period (Unassisted / Pre-Intervention):**")
        b_c1, b_c2 = st.columns(2)
        with b_c1:
            base_start_val = st.date_input("Baseline Start:", value=def_b_start, key="rep_base_start")
        with b_c2:
            base_end_val = st.date_input("Baseline End:", value=def_b_end, key="rep_base_end")

    with col_win2:
        st.markdown("**2. Pilot Period (MessWise Assisted):**")
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            pilot_start_val = st.date_input("Pilot Start:", value=def_p_start, key="rep_pilot_start")
        with p_c2:
            pilot_end_val = st.date_input("Pilot End:", value=def_p_end, key="rep_pilot_end")

    session = session_factory()
    try:
        report = compute_pilot_evidence_report(
            session=session,
            baseline_start=base_start_val.strftime("%Y-%m-%d"),
            baseline_end=base_end_val.strftime("%Y-%m-%d"),
            pilot_start=pilot_start_val.strftime("%Y-%m-%d"),
            pilot_end=pilot_end_val.strftime("%Y-%m-%d"),
            is_synthetic=eval_env,
            random_seed=42,
            n_bootstraps=1000,
        )

        if not report.has_sufficient_data:
            st.warning(f"⚠️ {report.status_message}")
        else:
            # Render Core Evidence Cards
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                avoided_val = report.mean_waste_avoided_kg_per_meal or 0.0
                st.markdown(f"""
                <div class="report-card">
                    <div class="report-title">Waste Avoided / Meal</div>
                    <div class="report-value" style="color: #16a34a;">+{avoided_val:.1f} kg</div>
                    <div class="report-sub">Matched mean: {report.baseline_avg_leftover_kg:.1f} kg → {report.pilot_avg_leftover_kg:.1f} kg</div>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                red_pct = report.percentage_waste_reduction or 0.0
                st.markdown(f"""
                <div class="report-card">
                    <div class="report-title">Relative Waste Reduction</div>
                    <div class="report-value" style="color: #16a34a;">{red_pct:.1f}%</div>
                    <div class="report-sub">Compared against matched unassisted baseline</div>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                ci_lo = report.bootstrap_ci_95_lower_kg or 0.0
                ci_hi = report.bootstrap_ci_95_upper_kg or 0.0
                st.markdown(f"""
                <div class="report-card">
                    <div class="report-title">95% Bootstrap CI</div>
                    <div class="report-value" style="font-size: 1.35rem; color: #2563eb;">[{ci_lo:.1f}, {ci_hi:.1f}] kg</div>
                    <div class="report-sub">1,000 resamples (seed 42, m={report.matched_pairs_count})</div>
                </div>
                """, unsafe_allow_html=True)

            with c4:
                b_sl = (report.baseline_service_level or 1.0) * 100
                p_sl = (report.pilot_service_level or 1.0) * 100
                st.markdown(f"""
                <div class="report-card">
                    <div class="report-title">Service Level Check</div>
                    <div class="report-value" style="color: #0f172a;">{p_sl:.1f}%</div>
                    <div class="report-sub">Baseline: {b_sl:.1f}% ({report.pilot_shortages} shortage in pilot)</div>
                </div>
                """, unsafe_allow_html=True)

            # Matched Pairs Inspection Table & Chart
            st.markdown("#### 🔬 Matched Weekday × Meal Slot Detail (Section 9.2)")
            st.caption("Compares identical meal slots between periods, excluding non-representative event and exam meals.")

            df_pairs = pd.DataFrame(report.matched_pairs)
            if not df_pairs.empty:
                # Plotly comparison bar chart
                fig_cmp = go.Figure()
                fig_cmp.add_trace(go.Bar(
                    x=df_pairs["weekday_name"] + " " + df_pairs["meal_type"],
                    y=df_pairs["baseline_leftover_kg"],
                    name="Baseline Leftover (kg)",
                    marker_color="#94a3b8",
                ))
                fig_cmp.add_trace(go.Bar(
                    x=df_pairs["weekday_name"] + " " + df_pairs["meal_type"],
                    y=df_pairs["pilot_leftover_kg"],
                    name="Assisted Pilot Leftover (kg)",
                    marker_color="#10b981",
                ))
                fig_cmp.update_layout(
                    barmode="group",
                    title="Matched Meal Slots: Baseline vs Pilot Leftover Quantities",
                    xaxis_title="Matched Meal Slot",
                    yaxis_title="Leftover (kg)",
                    height=360,
                    margin=dict(l=40, r=40, t=50, b=40),
                )
                st.plotly_chart(fig_cmp, use_container_width=True)

                st.dataframe(
                    df_pairs[[
                        "weekday_name", "meal_type", "baseline_date", "pilot_date",
                        "baseline_leftover_kg", "pilot_leftover_kg", "waste_avoided_kg", "percentage_reduction"
                    ]].rename(columns={
                        "weekday_name": "Day",
                        "meal_type": "Slot",
                        "baseline_date": "Baseline Date",
                        "pilot_date": "Pilot Date",
                        "baseline_leftover_kg": "Baseline Leftover (kg)",
                        "pilot_leftover_kg": "Pilot Leftover (kg)",
                        "waste_avoided_kg": "Avoided (kg)",
                        "percentage_reduction": "Reduction %",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

            # Scientific Disclosures & Limitations
            with st.expander("📝 Statistical Methodology, Caveats & Limitations", expanded=True):
                for cav in report.limitations_and_caveats:
                    st.write(f"- {cav}")
                st.markdown("""
                **Guiding Evaluation Principle (PLAN.md Section 9.1):**
                *“A reduction in food waste that causes student shortages is not a success. The pilot measures both waste
                reduction and service-level preservation, candidly reporting sample sizes and caveats without hindsight claims.”*
                """)
    finally:
        session.close()

st.markdown("---")

# -----------------------------------------------------------------------------
# Module I: System Audit Trail & Governance (Preserved)
# -----------------------------------------------------------------------------
st.subheader("🛡️ System Audit Trail & Governance (Module I)")
st.caption("Immutable operational audit log tracking service-level updates, plan confirmations, and record modifications.")

session = session_factory()
try:
    logs = session.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).limit(50)
    ).scalars().all()

    if not logs:
        st.info("No audit log entries recorded yet.")
    else:
        df_logs = pd.DataFrame([
            {
                "Log ID": entry.id,
                "Timestamp": entry.ts,
                "Actor": entry.who,
                "Action": entry.action,
                "Details": entry.new_value or entry.old_value or "-",
            }
            for entry in logs
        ])
        st.dataframe(df_logs, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # Module I6: Operational & Audit CSV Data Exports
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📥 Data Export Center (Module I: I6)")
    st.caption("Export validated operational records and audit logs to CSV with strict environment filtering (no personal identifiers).")

    exp_col1, exp_col2, exp_col3 = st.columns(3)

    from messwise.db import DishLog, Meal

    export_env = eval_env if eval_env is not None else (0 if has_real_records else 1)

    # 1. Meals Export
    meals_records = session.execute(
        select(Meal).where(Meal.is_synthetic == export_env).order_by(Meal.date.desc())
    ).scalars().all()
    df_exp_meals = pd.DataFrame([m.to_dict() for m in meals_records])

    with exp_col1:
        st.markdown("**Meals Register Export**")
        st.caption(f"{len(df_exp_meals)} records in active environment.")
        if not df_exp_meals.empty:
            csv_meals = df_exp_meals.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Meals (CSV)",
                data=csv_meals,
                file_name=f"messwise_meals_{'synthetic' if export_env else 'pilot'}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_meals_csv",
            )
        else:
            st.button("No Meals Available", disabled=True, use_container_width=True, key="btn_no_meals")

    # 2. Dish Logs Export
    dish_log_records = session.execute(
        select(DishLog).where(DishLog.is_synthetic == export_env).order_by(DishLog.id.desc())
    ).scalars().all()
    df_exp_dish_logs = pd.DataFrame([dl.to_dict() for dl in dish_log_records])

    with exp_col2:
        st.markdown("**Dish Logs Export**")
        st.caption(f"{len(df_exp_dish_logs)} dish log records.")
        if not df_exp_dish_logs.empty:
            csv_dish_logs = df_exp_dish_logs.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Dish Logs (CSV)",
                data=csv_dish_logs,
                file_name=f"messwise_dish_logs_{'synthetic' if export_env else 'pilot'}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_dish_logs_csv",
            )
        else:
            st.button("No Dish Logs Available", disabled=True, use_container_width=True, key="btn_no_dish_logs")

    # 3. Audit Trail Export
    audit_records = session.execute(
        select(AuditLog).order_by(AuditLog.id.desc())
    ).scalars().all()
    df_exp_audit = pd.DataFrame([a.to_dict() for a in audit_records])

    with exp_col3:
        st.markdown("**Audit Trail Export**")
        st.caption(f"{len(df_exp_audit)} system audit logs.")
        if not df_exp_audit.empty:
            csv_audit = df_exp_audit.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Audit Log (CSV)",
                data=csv_audit,
                file_name=f"messwise_audit_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_audit_csv",
            )
        else:
            st.button("No Audit Logs Available", disabled=True, use_container_width=True, key="btn_no_audit")

finally:
    session.close()
