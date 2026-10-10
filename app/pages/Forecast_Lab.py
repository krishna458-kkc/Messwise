"""MessWise - Forecast Lab (Module A + E1 Prediction Log).

Operational intelligence interface for meal-wise headcount forecasting.
Implements:
- A1: Meal-wise headcount predictions (1–7 days).
- A2: Honest baseline comparisons (last week & trailing average).
- A3: Participation-rate modeling.
- A4: Context features (calendar flags, weather, lags).
- A5: Transparent drivers and comparable past meals.
- A6: 80% conformal uncertainty bands.
- E1: Frozen prediction log inspection.
"""

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

from messwise.db import get_data_environment_summary, get_session_factory, init_db
from messwise.forecast import (
    MEAL_TYPES,
    ForecastResult,
    get_prediction_log_history,
    get_trained_forecaster,
    log_forecast_prediction,
)

st.set_page_config(
    page_title="MessWise | Forecast Lab",
    page_icon="🔬",
    layout="wide",
)
init_db()

# Custom CSS for high-legibility operational dashboard
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.85rem;
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

# Page Header
st.title("🔬 Forecast Lab")
st.caption("Demand Forecasting Engine — Honest Baselines, Conformal Bands & Prediction Log (PLAN.md Module A + E1)")

# Inspect database for actual record counts before rendering controls
session_factory = get_session_factory()
with session_factory() as check_session:
    env_summary = get_data_environment_summary(check_session)

real_meals_count = env_summary["real_meals_count"]
synth_meals_count = env_summary["synthetic_meals_count"]
has_real_records = env_summary["has_real_data"]

# Environment Mode Selection & Truthfulness Guard
if not has_real_records:
    env_choice = 1  # Strictly enforce Synthetic Demo Data
    st.warning(
        f"🧪 **Synthetic Development Data — Demonstration Only**\n\n"
        f"• **Real pilot records: 0** (Real pilot mode is disabled until kitchen staff record operational meals via Kitchen mode).\n"
        f"• Using **{synth_meals_count} synthetic demonstration meals** to illustrate model fitting, honest baselines, and conformal uncertainty bands."
    )
    col_env1, col_env2 = st.columns([2, 1])
    with col_env1:
        st.markdown(
            f"<div style='margin-top: 4px;'><strong>Active Data Environment:</strong> "
            f"<span class='badge-synth'>Synthetic Demo Dataset ({synth_meals_count} records)</span></div>",
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
            "Data Environment:",
            options=[0, 1],
            format_func=lambda x: (
                env_summary["real_env_label"]
                if x == 0
                else f"🧪 Synthetic Demo Data ({synth_meals_count} demonstration meals)"
            ),
            index=0,
            horizontal=True,
        )
    with col_env2:
        if env_choice == 0:
            badge_cls = env_summary["real_env_badge_class"]
            badge_text = env_summary["real_env_badge"]
            st.markdown(
                f'<div style="text-align:right; margin-top: 14px;"><span class="{badge_cls}">'
                f'{badge_text}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="text-align:right; margin-top: 14px;"><span class="badge-synth">'
                f'▲ Active Environment: Synthetic Demo Data ({synth_meals_count} records)</span></div>',
                unsafe_allow_html=True,
            )

    if env_choice == 0 and not env_summary["is_verified_pilot"]:
        unv = env_summary["unverified_test_meals_count"]
        st.warning(
            f"⚠️ **Unverified Manual Test Entries — Not Verified Pilot Data**\n\n"
            f"• Currently **{unv} non-synthetic meals** exist in the database with status `verification_status: unverified_test`.\n"
            f"• These entries were logged during development/manual testing and have **not** been operator-confirmed as live pilot measurements.\n"
            f"• Forecast training below reflects these test logs only."
        )

st.markdown("---")

# Session & Data Loading
with session_factory() as session:
    forecaster, df_history = get_trained_forecaster(session=session, is_synthetic=env_choice)

# Informational banner on dataset size and validation honesty
sample_count = len(df_history)
if env_choice == 1:
    st.info(
        f"📊 **Demonstration Model Trained & Validated (Synthetic Demo Dataset)**: {sample_count} demonstration meals analyzed.\n\n"
        f"• Validation MAE: **{forecaster.validation_metrics.get('model_mae', 'N/A')} heads** "
        f"(vs Last Week: {forecaster.validation_metrics.get('baseline_last_week_mae', 'N/A')}, "
        f"Trailing Avg: {forecaster.validation_metrics.get('baseline_trailing_avg_mae', 'N/A')}).\n\n"
        f"⚠️ *Honesty Notice: These validation figures evaluate model fitting on synthetic development data. They do NOT represent verified real-world pilot accuracy.*"
    )
elif sample_count < 6:
    st.info(
        f"ℹ️ **Limited Historical Data** ({sample_count} real meal records found). "
        "The forecaster operates in cautious cold-start mode: prediction intervals are wider and "
        "predictions lean heavily on trailing baselines. Log more meals via Kitchen Mode to refine accuracy."
    )
else:
    st.success(
        f"📊 **Real Pilot Model Trained & Validated**: {sample_count} operational kitchen meals analyzed. "
        f"Validation MAE: **{forecaster.validation_metrics.get('model_mae', 'N/A')} heads** "
        f"(vs Last Week: {forecaster.validation_metrics.get('baseline_last_week_mae', 'N/A')}, "
        f"Trailing Avg: {forecaster.validation_metrics.get('baseline_trailing_avg_mae', 'N/A')})."
    )

# Control Bar
st.subheader("1. Forecast Parameters")
c1, c2, c3, c4 = st.columns([1.5, 1, 1.2, 1.2])

with c1:
    forecast_date = st.date_input("Forecast Start Date", value=date.today() + timedelta(days=1))
with c2:
    days_ahead = st.slider("Horizon (Days Ahead)", min_value=1, max_value=7, value=1)
with c3:
    meal_filter = st.selectbox("Meal Filter", options=["All Meals"] + [m.title() for m in MEAL_TYPES], index=0)
with c4:
    hostel_strength = st.number_input("Hostel Strength", min_value=50, max_value=2000, value=500, step=10)

# Optional Context Overrides for Target Date
with st.expander("⚙️ Optional Context Overrides (Events, Weather, Exams)"):
    ec1, ec2, ec3, ec4, ec5 = st.columns(5)
    with ec1:
        f_event = st.checkbox("Campus Event / Fest", value=False)
    with ec2:
        f_exam = st.checkbox("Exam Period", value=False)
    with ec3:
        f_hol = st.checkbox("Holiday / Vacation", value=False)
    with ec4:
        f_temp = st.number_input("Forecast Temp (°C)", min_value=10.0, max_value=48.0, value=28.0, step=0.5)
    with ec5:
        f_rain = st.number_input("Expected Rain (mm)", min_value=0.0, max_value=150.0, value=0.0, step=1.0)

context_flags = {"event_flag": int(f_event), "exam_flag": int(f_exam), "holiday_flag": int(f_hol)}
weather_data = {"temp_c": f_temp, "rain_mm": f_rain}

# Generate Forecasts
target_date_str = forecast_date.strftime("%Y-%m-%d")
meals_to_eval = [meal_filter.lower()] if meal_filter != "All Meals" else list(MEAL_TYPES)

forecast_results: list[ForecastResult] = []
with session_factory() as session:
    for day_idx in range(days_ahead):
        t_str = (forecast_date + timedelta(days=day_idx)).strftime("%Y-%m-%d")
        for m in meals_to_eval:
            res = forecaster.predict_slot(
                df_history=df_history,
                target_date_str=t_str,
                meal_type=m,
                hostel_strength=int(hostel_strength),
                context_flags=context_flags,
                weather=weather_data,
                is_synthetic=env_choice,
            )
            # Log to Prediction Log (E1)
            log_forecast_prediction(session, res)
            forecast_results.append(res)
    session.commit()

st.markdown("---")

# Section 2: Primary Forecast Summary & Comparison Cards
st.subheader("2. Headcount Predictions & Honest Baselines")

if forecast_results:
    # Display cards for first day's slots
    first_day_results = [r for r in forecast_results if r.target_date == target_date_str]
    cols = st.columns(len(first_day_results))
    for idx, r in enumerate(first_day_results):
        with cols[idx]:
            conf_color = "#16a34a" if r.confidence_status == "high" else ("#ca8a04" if r.confidence_status == "moderate" else "#dc2626")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{r.meal_type.title()} • {r.target_date}</div>
                <div class="metric-value">{r.h_hat} <span style="font-size:0.9rem; font-weight:normal; color:#64748b;">students</span></div>
                <div class="metric-sub">
                    <b>80% Range:</b> {r.h_lo} – {r.h_hi} heads<br>
                    <b>Participation:</b> {r.predicted_participation_rate:.1%}<br>
                    <b>Baseline 1 (Last Wk):</b> {r.baseline_last_week if r.baseline_last_week is not None else 'N/A'}<br>
                    <b>Baseline 2 (Trailing):</b> {r.baseline_trailing_avg if r.baseline_trailing_avg is not None else 'N/A'}<br>
                    <span style="color:{conf_color}; font-weight:600;">● Confidence: {r.confidence_status.title()}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Section 3: Interactive Plotly Visualizations
st.markdown("---")
st.subheader("3. Forecast Comparison & Uncertainty Bands")

tab1, tab2 = st.tabs(["📊 Forecast vs Baselines & 80% Band", "📈 Historical Attendance Context"])

with tab1:
    # Plotly Chart: Forecast vs Baselines with Interval Band
    fig = go.Figure()

    labels = [f"{r.target_date}<br>{r.meal_type.title()}" for r in forecast_results]
    h_hats = [r.h_hat for r in forecast_results]
    h_los = [r.h_lo for r in forecast_results]
    h_his = [r.h_hi for r in forecast_results]
    b1_vals = [r.baseline_last_week for r in forecast_results]
    b2_vals = [r.baseline_trailing_avg for r in forecast_results]

    # Upper/Lower bound error bar calculation
    err_plus = [h_his[i] - h_hats[i] for i in range(len(h_hats))]
    err_minus = [h_hats[i] - h_los[i] for i in range(len(h_hats))]

    # Model Forecast Bar / Marker
    fig.add_trace(go.Bar(
        x=labels,
        y=h_hats,
        name="MessWise Forecast",
        marker_color="#2563eb",
        error_y=dict(
            type='data',
            symmetric=False,
            array=err_plus,
            arrayminus=err_minus,
            color="#1e293b",
            thickness=2,
            width=6,
        ),
        hovertemplate="<b>%{x}</b><br>Forecast: %{y}<br>Range: [%{customdata[0]}, %{customdata[1]}]<extra></extra>",
        customdata=list(zip(h_los, h_his)),
    ))

    # Baseline 1 Markers
    valid_b1_x = [labels[i] for i, b in enumerate(b1_vals) if b is not None]
    valid_b1_y = [b for b in b1_vals if b is not None]
    if valid_b1_y:
        fig.add_trace(go.Scatter(
            x=valid_b1_x,
            y=valid_b1_y,
            mode="markers",
            name="Baseline 1 (Last Week)",
            marker=dict(symbol="diamond", size=11, color="#ea580c"),
            hovertemplate="Baseline 1 (Last Week): %{y}<extra></extra>",
        ))

    # Baseline 2 Markers
    valid_b2_x = [labels[i] for i, b in enumerate(b2_vals) if b is not None]
    valid_b2_y = [b for b in b2_vals if b is not None]
    if valid_b2_y:
        fig.add_trace(go.Scatter(
            x=valid_b2_x,
            y=valid_b2_y,
            mode="markers",
            name="Baseline 2 (Trailing Avg)",
            marker=dict(symbol="circle", size=10, color="#16a34a"),
            hovertemplate="Baseline 2 (Trailing Avg): %{y}<extra></extra>",
        ))

    fig.update_layout(
        title="Meal Headcount Forecast vs Honest Baselines with 80% Uncertainty Band",
        yaxis_title="Headcount (Students)",
        xaxis_title="Target Slot",
        barmode="group",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if not df_history.empty:
        fig_hist = go.Figure()
        recent_df = df_history.tail(35)
        for m_type in MEAL_TYPES:
            sub = recent_df[recent_df["meal_type"] == m_type]
            if not sub.empty:
                fig_hist.add_trace(go.Scatter(
                    x=sub["date"],
                    y=sub["headcount"],
                    mode="lines+markers",
                    name=m_type.title(),
                    hovertemplate="%{x} " + m_type.title() + ": %{y} heads<extra></extra>",
                ))
        fig_hist.update_layout(
            title="Recent Historical Headcount Trend (Operational Context)",
            yaxis_title="Actual Headcount",
            xaxis_title="Date",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=60, b=40),
            height=380,
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No historical meal records available to plot trends.")

# Section 4: Explainability & Top Contributing Drivers (A5)
st.markdown("---")
st.subheader("4. Explainability & Contributing Drivers (PLAN.md A5)")

col_exp1, col_exp2 = st.columns([1.4, 1])

with col_exp1:
    st.markdown("##### 🔍 Why is MessWise predicting this number?")
    for r in first_day_results:
        with st.expander(f"**{r.meal_type.title()} ({r.target_date})**: {r.h_hat} heads", expanded=True):
            st.info(r.explanation)
            if r.top_drivers:
                df_drivers = pd.DataFrame([
                    {
                        "Driver Feature": d["feature"],
                        "Effect (Heads)": d["effect"],
                        "Operational Description": d["description"],
                    }
                    for d in r.top_drivers
                ])
                st.dataframe(df_drivers, use_container_width=True, hide_index=True)
            else:
                st.caption("No significant single-feature deviations; prediction aligns with core baseline.")

with col_exp2:
    st.markdown("##### 🕒 Recent Comparable Historical Meals")
    primary_res = first_day_results[0] if first_day_results else None
    if primary_res and primary_res.similar_meals:
        st.caption(f"Last 3 similar {primary_res.meal_type.title()} meals on record:")
        st.dataframe(pd.DataFrame(primary_res.similar_meals), use_container_width=True, hide_index=True)
    else:
        st.caption("No past comparable meals found in current dataset.")

# Section 5: Immutable Prediction Log (E1)
st.markdown("---")
st.subheader("5. Prediction Log (PLAN.md E1)")
st.caption(
    "Every live forecast is frozen here with a timestamp BEFORE service to prevent hindsight claims. "
    "When kitchen staff log actual meals, outcomes are linked automatically to compute forecast error."
)

with session_factory() as session:
    pred_logs = get_prediction_log_history(session=session, is_synthetic=env_choice, limit=20)

if pred_logs:
    df_pred_log = pd.DataFrame([
        {
            "ID": pl["id"],
            "Timestamp": pl["created_at"][:19],
            "Meal Date": pl["meal_date"],
            "Meal": pl["meal_type"].title(),
            "Predicted": int(pl["h_hat"]),
            "80% Interval": f"{int(pl['h_lo'])} – {int(pl['h_hi'])}",
            "Baseline 1": f"{int(pl['baseline_last_week'])}" if pl["baseline_last_week"] is not None else "—",
            "Baseline 2": f"{int(pl['baseline_trailing_avg'])}" if pl["baseline_trailing_avg"] is not None else "—",
            "Actual": str(pl["actual_headcount"]) if pl["actual_headcount"] is not None else "Pending Service",
            "Error (Actual - Pred)": f"{pl['forecast_error']:+.0f}" if pl["forecast_error"] is not None else "—",
            "Status": "🟢 Evaluated" if pl["status"] == "evaluated" else "⏳ Pending",
        }
        for pl in pred_logs
    ])
    st.dataframe(df_pred_log, use_container_width=True, hide_index=True)
else:
    st.info("No prediction logs recorded yet for this mode.")
