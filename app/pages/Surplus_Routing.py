"""MessWise - Food-Safe Surplus Routing & Safety Clock (Module G: G1 & G2).

Streamlit interface for:
- G1: Predicted-surplus alerts (pre-service estimates) vs measured-surplus alerts (kitchen scale weigh-ins).
- G2: Food-Safety Clock with holding-time cutoffs and temperature observation log.
- FSSAI 2019 regulatory compliance gates and auditable manager review.
- Pre-filled WhatsApp click-to-chat draft (MVP delivery) for verified eligible surplus.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import streamlit as st
from sqlalchemy import desc, select

from messwise.db import (
    AuditLog,
    Dish,
    DishLog,
    Meal,
    SurplusEvent,
    get_data_environment_summary,
    get_session_factory,
    init_db,
)
from messwise.surplus import (
    APP_TIMEZONE,
    DANGER_ZONE_MAX_C,
    DANGER_ZONE_MIN_C,
    FSSAI_AMBIENT_MAX_HOURS,
    FSSAI_HOT_HOLD_MAX_HOURS,
    FSSAI_HOT_HOLD_MIN_TEMP_C,
    FSSAI_POLICY_NAME,
    FSSAI_POLICY_VERSION,
    approve_surplus_alert,
    build_communication_draft,
    dismiss_surplus_alert,
    evaluate_food_safety_clock,
    generate_measured_surplus_alerts,
    generate_predicted_surplus_alerts,
    list_surplus_alerts_query,
    parse_iso_dt,
    record_safety_observation,
)

# Page configuration
st.set_page_config(
    page_title="MessWise | Surplus Routing & Safety Clock",
    page_icon="🛡️",
    layout="wide",
)

init_db()

# Page Title & Tagline
st.title("🛡️ Surplus Routing & Food-Safety Clock")
st.caption("Module G: G1 Predicted-Surplus Alerts  •  G2 Food-Safety Clock (FSSAI 2019 Compliant)")

st.markdown("---")

# Environment Summary & Controls
env_summary = get_data_environment_summary()
has_real = env_summary["has_real_data"]

col_env1, col_env2 = st.columns([2, 3])
with col_env1:
    env_choice = st.radio(
        "Data Environment:",
        options=["Synthetic Demonstration", env_summary["real_env_label"]],
        index=0 if not env_summary["has_verified_pilot_data"] else 1,
        horizontal=True,
        help="MessWise strictly isolates synthetic demonstration data from real pilot records.",
    )
    is_synthetic = 1 if env_choice == "Synthetic Demonstration" else 0

with col_env2:
    if is_synthetic == 1:
        st.warning(
            "⚠️ **Synthetic Demonstration — Not a Real Food Donation**\n\n"
            "Alerts and timestamps displayed below are simulated records for testing "
            "the safety clock and manager review workflow. No real food is available for pickup."
        )
    else:
        if env_summary["has_verified_pilot_data"]:
            st.success(
                f"🟢 **Verified Pilot Environment Active** — Showing authentic kitchen surplus records. "
                f"({env_summary['verified_pilot_meals_count']} verified meals logged)"
            )
        else:
            st.warning(
                f"⚠️ **Unverified Test Entries Active** — Showing test kitchen surplus records. "
                f"({env_summary['unverified_test_meals_count']} unverified test meals logged)"
            )

st.markdown("---")

# Tabs for Surplus Routing
tab_active, tab_generator, tab_governance = st.tabs([
    "📋 Active Alerts & Food-Safety Clock",
    "⚙️ Generate Alerts (G1)",
    "📜 FSSAI Safety Standards & Audit Log",
])

# ==============================================================================
# TAB 1: Active Alerts & Food-Safety Clock (G1 & G2)
# ==============================================================================
with tab_active:
    session_factory = get_session_factory()
    with session_factory() as session:
        # Filter controls
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            status_filter = st.selectbox(
                "Filter by Manager Status:",
                options=["All", "pending", "approved", "dismissed"],
                index=0,
            )
        with c_f2:
            type_filter = st.selectbox(
                "Filter by Surplus Type:",
                options=["All", "predicted", "measured"],
                index=0,
            )
        with c_f3:
            elig_filter = st.selectbox(
                "Filter by Safety Eligibility:",
                options=["All", "eligible", "pending_inspection", "blocked_expired", "blocked_temperature", "blocked_missing_data", "blocked_contamination"],
                index=0,
            )

        # Query alerts
        mgr_arg = None if status_filter == "All" else status_filter
        type_arg = None if type_filter == "All" else type_filter
        elig_arg = None if elig_filter == "All" else elig_filter

        alerts = list_surplus_alerts_query(
            session=session,
            is_synthetic=is_synthetic,
            surplus_type=type_arg,
            manager_status=mgr_arg,
            eligibility_status=elig_arg,
            limit=50,
        )

        if not alerts:
            if is_synthetic == 0 and not has_real:
                st.info(
                    "ℹ️ **No real pilot surplus alerts recorded yet.**\n\n"
                    "As real meals and serving surplus are logged in the Kitchen module, "
                    "measured surplus records will appear here for food-safety evaluation."
                )
            else:
                st.info(
                    "ℹ️ No surplus alerts match the current filter criteria. "
                    "Use the 'Generate Alerts (G1)' tab to create predicted or measured surplus alerts."
                )
        else:
            st.markdown(f"### Found {len(alerts)} Surplus Alert(s)")

            for alert in alerts:
                dish_name = alert.dish.name if alert.dish else f"Dish #{alert.dish_id}"
                
                # Evaluate live safety clock
                obs_list = []
                if alert.temp_log_json:
                    try:
                        obs_list = json.loads(alert.temp_log_json)
                    except Exception:
                        obs_list = []

                clock = evaluate_food_safety_clock(
                    cooking_completed_at=alert.cooking_completed_at,
                    hold_type=alert.hold_type,
                    observations=obs_list,
                    suspected_contamination=bool(alert.suspected_contamination),
                    policy_version=alert.policy_version,
                )

                # Card container
                with st.container():
                    st.markdown("---")
                    col_head1, col_head2 = st.columns([3, 2])
                    
                    with col_head1:
                        # Dish title & surplus type
                        type_label = "🔮 Predicted Surplus (Pre-service Estimate)" if alert.surplus_type == "predicted" else "⚖️ Measured Surplus (Post-service Weigh-in)"
                        st.subheader(f"{dish_name} — {alert.estimated_qty} {alert.unit}")
                        st.caption(f"**Type**: {type_label}  |  **Meal**: {alert.meal_date} ({alert.meal_type.title()})")
                        if alert.uncertainty_range:
                            st.caption(f"**Uncertainty / Range**: {alert.uncertainty_range}")

                    with col_head2:
                        # Eligibility badge
                        if clock.eligibility_status == "eligible":
                            st.success("🟢 **ELIGIBLE FOR RECOVERY**\n\nAll FSSAI 2019 checks passed.")
                        elif clock.eligibility_status == "pending_inspection":
                            st.warning("🟡 **PENDING INSPECTION**\n\nTemperature or holding observation required.")
                        elif clock.eligibility_status == "blocked_expired":
                            st.error("🔴 **BLOCKED: SAFE WINDOW EXPIRED**\n\nDonation strictly prohibited.")
                        elif clock.eligibility_status == "blocked_temperature":
                            st.error("🔴 **BLOCKED: TEMPERATURE VIOLATION**\n\nTemperature in Danger Zone.")
                        elif clock.eligibility_status == "blocked_contamination":
                            st.error("🔴 **BLOCKED: CONTAMINATION FLAGGED**\n\nQuestionable food cannot be recovered.")
                        elif clock.eligibility_status == "dismissed":
                            st.info("⚪ **DISMISSED BY MANAGER**")
                        else:
                            st.error(f"🔴 **BLOCKED: {clock.eligibility_status.upper()}**")

                    # Safety Clock metrics
                    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                    
                    # Start time display
                    start_str = "Not recorded"
                    if alert.cooking_completed_at:
                        p_dt = parse_iso_dt(alert.cooking_completed_at)
                        if p_dt:
                            start_str = p_dt.strftime("%I:%M %p")
                    c_m1.metric("Cooking / Hold Start", start_str)

                    # Temperature display
                    temp_str = f"{alert.current_temp_c:.1f}°C" if alert.current_temp_c is not None else "Pending"
                    c_m2.metric("Latest Temperature", temp_str, help="FSSAI minimum hot holding: 65.0°C")

                    # Elapsed / Remaining
                    elapsed_str = f"{clock.elapsed_hours:.1f}h" if clock.elapsed_hours is not None else "—"
                    remaining_str = f"{clock.remaining_hours:.1f}h" if clock.remaining_hours is not None else "—"
                    
                    if clock.is_expired:
                        c_m3.metric("Time Elapsed", elapsed_str)
                        c_m4.metric("Safe Time Remaining", "0.0h (EXPIRED)", delta="-Expired", delta_color="inverse")
                    else:
                        c_m3.metric("Time Elapsed", elapsed_str)
                        c_m4.metric("Safe Time Remaining", remaining_str)

                    # Blocking reason callout
                    if clock.blocking_reason:
                        st.markdown(f"**Safety Rule Status**: `{clock.blocking_reason}`")

                    # Expandable details: observations & actions
                    with st.expander(f"⚙️ Temperature History & Manager Review for {dish_name} (Alert #{alert.id})"):
                        col_obs, col_mgr = st.columns(2)

                        with col_obs:
                            st.markdown("#### 🌡️ Temperature & Holding Observation Log")
                            if obs_list:
                                for idx, o in enumerate(obs_list):
                                    t_str = parse_iso_dt(o.get('timestamp')).strftime('%I:%M:%S %p') if parse_iso_dt(o.get('timestamp')) else o.get('timestamp')
                                    st.write(f"• **{t_str}**: {o.get('temp_c')}°C ({o.get('hold_type', 'hot').upper()}) by `{o.get('observed_by', 'cook')}` {('— ' + o.get('notes')) if o.get('notes') else ''}")
                            else:
                                st.caption("No temperature observations recorded yet.")

                            st.markdown("##### Add Safety Observation")
                            with st.form(f"form_obs_{alert.id}"):
                                in_temp = st.number_input("Recorded Temperature (°C):", value=70.0, min_value=-20.0, max_value=120.0, step=0.5, key=f"temp_{alert.id}")
                                in_hold = st.selectbox("Holding Type:", options=["hot", "ambient", "cold"], index=0, key=f"hold_{alert.id}")
                                in_start = st.text_input(
                                    "Cooking Finished Time (ISO or HH:MM):",
                                    value=alert.cooking_completed_at or datetime.now(APP_TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
                                    key=f"start_{alert.id}",
                                    help="Sets or updates the holding start time for elapsed calculation.",
                                )
                                in_contam = st.checkbox("Flag suspected contamination or sensory issue", value=False, key=f"contam_{alert.id}")
                                in_notes = st.text_input("Observation Notes:", value="Verified hot holding steam table", key=f"notes_{alert.id}")
                                
                                submit_obs = st.form_submit_button("Record Observation")
                                if submit_obs:
                                    try:
                                        record_safety_observation(
                                            session=session,
                                            alert_id=alert.id,
                                            temp_c=in_temp,
                                            hold_type=in_hold,
                                            cooking_completed_at=in_start,
                                            suspected_contamination=in_contam,
                                            notes=in_notes,
                                        )
                                        st.success("Observation recorded and safety clock updated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error recording observation: {str(e)}")

                        with col_mgr:
                            st.markdown("#### 🛡️ Manager Review & Surplus Action")
                            st.write(f"**Current Review Status**: `{alert.manager_status.upper()}`")
                            if alert.manager_who:
                                st.write(f"**Manager**: `{alert.manager_who}` at `{alert.manager_action_at}`")

                            if alert.manager_status == "approved":
                                st.success("✅ **Alert Approved for Recovery Communication**")
                                if alert.communication_draft:
                                    st.text_area("Generated Communication Draft:", value=alert.communication_draft, height=140, key=f"draft_{alert.id}")
                                    _, wa_link = build_communication_draft(alert, alert.partner_name, alert.partner_phone)
                                    if wa_link:
                                        st.markdown(f"[📱 **Open WhatsApp Click-to-Chat Draft**]({wa_link})")
                                    else:
                                        st.caption("ℹ️ No partner NGO phone configured. Draft text is ready for manual distribution.")
                            elif alert.manager_status == "dismissed":
                                st.info(f"Dismissed reason: {alert.manager_reason}")
                            else:
                                # Pending review
                                if clock.eligibility_status != "eligible":
                                    st.error(
                                        "⛔ **Approval Blocked by Food-Safety Gate**\n\n"
                                        f"Reason: {clock.blocking_reason}\n\n"
                                        "Per MessWise core principles and FSSAI 2019 regulations, managers "
                                        "cannot approve surplus donation when safety eligibility is unconfirmed or expired."
                                    )
                                else:
                                    st.success("🟢 Food-safety verified! Ready for manager approval.")
                                    with st.form(f"form_approve_{alert.id}"):
                                        mgr_name = st.text_input("Manager Name:", value="Mess Supervisor", key=f"mgr_{alert.id}")
                                        partner_n = st.text_input("Partner NGO Name (optional):", value="Robin Hood Army / Feeding India", key=f"pn_{alert.id}")
                                        partner_p = st.text_input("Partner Contact Phone (optional):", value="+919876543210", key=f"pp_{alert.id}")
                                        app_reason = st.text_input("Approval Remarks:", value="Safe surplus verified from lunch service", key=f"rem_{alert.id}")
                                        
                                        submit_app = st.form_submit_button("Approve for Partner Communication")
                                        if submit_app:
                                            try:
                                                approve_surplus_alert(
                                                    session=session,
                                                    alert_id=alert.id,
                                                    manager_who=mgr_name,
                                                    manager_reason=app_reason,
                                                    partner_name=partner_n,
                                                    partner_phone=partner_p,
                                                )
                                                st.success("Surplus alert approved!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Approval failed: {str(e)}")

                                # Dismissal form (always allowed with reason)
                                with st.form(f"form_dismiss_{alert.id}"):
                                    d_mgr = st.text_input("Manager Name:", value="Mess Supervisor", key=f"dmgr_{alert.id}")
                                    d_reason = st.text_input("Reason for Dismissal:", value="Quantity insufficient for collection", key=f"dreas_{alert.id}")
                                    submit_dis = st.form_submit_button("Dismiss Alert")
                                    if submit_dis:
                                        try:
                                            dismiss_surplus_alert(
                                                session=session,
                                                alert_id=alert.id,
                                                manager_who=d_mgr,
                                                manager_reason=d_reason,
                                            )
                                            st.info("Surplus alert dismissed.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Dismissal failed: {str(e)}")


# ==============================================================================
# TAB 2: Generate Alerts (G1)
# ==============================================================================
with tab_generator:
    st.subheader("⚙️ Generate Surplus Alerts (G1)")
    st.markdown(
        "MessWise distinguishes between **Predicted Surplus** (derived from pre-service planning) "
        "and **Measured Surplus** (derived from post-service kitchen weigh-in)."
    )

    col_gen_p, col_gen_m = st.columns(2)

    with col_gen_p:
        st.markdown("### 🔮 Predicted Surplus from Plan")
        st.caption("Forecast-based estimate to prepare recovery partners ahead of service.")

        with st.form("form_gen_predicted"):
            p_date = st.date_input("Target Meal Date:", value=datetime.now(APP_TIMEZONE).date() + timedelta(days=1))
            p_meal = st.selectbox("Meal Type:", options=["lunch", "dinner", "breakfast", "snacks"], index=0)
            p_sl = st.slider("Service Level for Planning:", min_value=0.50, max_value=0.99, value=0.95, step=0.01)
            p_thresh = st.number_input("Surplus Alert Threshold (kg/L):", value=2.0, min_value=0.5, max_value=20.0, step=0.5)

            submit_pred = st.form_submit_button("Generate Predicted Alerts")
            if submit_pred:
                session_factory = get_session_factory()
                with session_factory() as s:
                    try:
                        p_alerts = generate_predicted_surplus_alerts(
                            session=s,
                            target_date=str(p_date),
                            meal_type=p_meal,
                            is_synthetic=is_synthetic,
                            threshold_kg=p_thresh,
                            service_level=p_sl,
                        )
                        st.success(f"Generated/updated {len(p_alerts)} predicted surplus alert(s)!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate predicted alerts: {str(e)}")

    with col_gen_m:
        st.markdown("### ⚖️ Measured Surplus from Kitchen Log")
        st.caption("Actual unserved surplus weighed at the end of service on kitchen scales.")

        session_factory = get_session_factory()
        with session_factory() as s:
            meals = s.execute(
                select(Meal).where(Meal.is_synthetic == is_synthetic).order_by(Meal.date.desc(), Meal.id.desc()).limit(15)
            ).scalars().all()

            if not meals:
                st.info("No meals available to scan in this data environment.")
            else:
                with st.form("form_gen_measured"):
                    meal_options = {f"#{m.id} | {m.date} {m.meal_type.title()} (Headcount: {m.headcount})": m.id for m in meals}
                    sel_meal_str = st.selectbox("Select Logged Meal:", options=list(meal_options.keys()))
                    sel_meal_id = meal_options[sel_meal_str]
                    m_thresh = st.number_input("Leftover Alert Threshold (kg/L):", value=1.0, min_value=0.5, max_value=20.0, step=0.5)
                    m_start = st.text_input(
                        "Cooking Completed Time (ISO format):",
                        value=datetime.now(APP_TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
                        help="Sets initial start time for the Food-Safety Clock.",
                    )

                    submit_meas = st.form_submit_button("Scan Meal & Create Measured Alerts")
                    if submit_meas:
                        try:
                            m_alerts = generate_measured_surplus_alerts(
                                session=s,
                                meal_id=sel_meal_id,
                                threshold_kg=m_thresh,
                                cooking_completed_at=m_start,
                            )
                            st.success(f"Generated/updated {len(m_alerts)} measured surplus alert(s)!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to generate measured alerts: {str(e)}")


# ==============================================================================
# TAB 3: Regulatory Standards & Audit Governance
# ==============================================================================
with tab_governance:
    st.subheader("📜 Food Safety Standards & Regulatory Compliance (FSSAI 2019)")
    st.markdown(f"**Governing Authority & Regulation**: *{FSSAI_POLICY_NAME}* (`{FSSAI_POLICY_VERSION}`)")

    col_std1, col_std2 = st.columns(2)
    with col_std1:
        st.markdown(r"""
        ### 🌡️ Mandated Operational Thresholds
        - **Hot Holding**: Maintained strictly at or above **65.0°C** (149°F).
        - **Hot Safe Window**: Maximum **4.0 hours** from completion of cooking to distribution/consumption.
        - **Ambient / Uncontrolled Holding**: Maximum **2.0 hours** if food is not maintained at $\ge 65^\circ\text{C}$ or $\le 5^\circ\text{C}$.
        - **Cold Holding**: Maintained at or below **5.0°C** (41°F). Safe window up to 24 hours under continuous refrigeration.
        - **Temperature Danger Zone**: **5.0°C to 65.0°C** — rapid bacterial growth occurs within this band.
        """)


    with col_std2:
        st.markdown("""
        ### 🛡️ Non-Negotiable Safety Disqualifiers
        - **Re-serving Prohibition**: MessWise **never** recommends re-serving cooked leftovers in the mess.
        - **Plate Waste Disqualification**: Food that has been served onto student trays is 100% disqualified. Only unserved batch / counter surplus is eligible.
        - **Expired Safe Window**: Software strictly refuses approval once the safe window expires ($> 4$h hot, $> 2$h ambient).
        - **Unconfirmed History / Missing Observations**: Food without recorded start time or temperature history cannot be approved.
        - **Suspected Contamination**: Any sensory flaw, off-odour, pest contact, or foreign matter permanently blocks recovery.
        """)

    st.markdown("---")
    st.subheader("📑 Surplus Routing Audit Trail")
    session_factory = get_session_factory()
    with session_factory() as s:
        audit_records = s.execute(
            select(AuditLog).where(
                AuditLog.action.in_([
                    "surplus_predicted_alert",
                    "surplus_measured_alert",
                    "safety_observation_recorded",
                    "surplus_approved",
                    "surplus_dismissed",
                ])
            ).order_by(desc(AuditLog.id)).limit(30)
        ).scalars().all()

        if not audit_records:
            st.caption("No surplus routing audit entries recorded yet.")
        else:
            table_rows = []
            for rec in audit_records:
                table_rows.append({
                    "Timestamp": rec.ts,
                    "Operator / Role": rec.who,
                    "Action": rec.action,
                    "Details": rec.new_value,
                })
            st.dataframe(table_rows, use_container_width=True)
