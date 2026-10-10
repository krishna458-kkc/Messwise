"""MessWise - Home / Application Entry Point.

AI food-operations intelligence platform for institutional kitchens.
Predict -> Plan -> Cook -> Measure -> Learn
"""

import sys
from pathlib import Path

# Ensure root directory is on Python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from messwise.db import get_data_environment_summary, init_db

# Page config
st.set_page_config(
    page_title="MessWise | Kitchen Intelligence",
    page_icon="🍲",
    layout="wide",
)

# Ensure DB initialized
init_db()

# Title and Header
st.title("🍲 MessWise")
st.subheader("AI Food-Operations Intelligence for Institutional Kitchens")
st.caption("Predict  •  Plan  •  Cook  •  Measure  •  Learn  •  Save")

st.markdown("---")

# Operational Metrics from SQLite
env_summary = get_data_environment_summary()
real_meals_count = env_summary["real_meals_count"]
synth_meals_count = env_summary["synthetic_meals_count"]
dishes_count = env_summary["registered_dishes_count"]
dish_logs_count = env_summary["total_dish_logs_count"]

# Sidebar Governance & Personalization (I5 & I8)
st.sidebar.markdown("### 👤 User & Governance")
active_role = st.sidebar.selectbox(
    "Active Operational Role (I5):",
    options=["Mess Manager", "Cook / Kitchen Staff", "Hostel Warden", "Auditor"],
    index=0,
    help="Role-based views and authority context across MessWise modules.",
    key="app_active_role",
)
st.session_state["user_role"] = active_role

active_lang = st.sidebar.selectbox(
    "Kitchen Language (I8):",
    options=["English", "తెలుగు (Telugu)", "हिन्दी (Hindi)"],
    index=0,
    help="Centralized translations for kitchen-facing labels and cues.",
    key="app_kitchen_lang",
)
st.session_state["kitchen_lang"] = "te" if "తెలుగు" in active_lang else ("hi" if "हिन्दी" in active_lang else "en")

st.sidebar.caption(f"Role: **{active_role}** | Language: **{active_lang}**")

# Active Operational Notifications Banner (I9)
from messwise.db import get_session_factory
from messwise.notifications import get_active_notifications

with get_session_factory()() as notif_session:
    active_notifs = get_active_notifications(notif_session, is_synthetic=1)

if active_notifs:
    with st.expander(f"🔔 Operational Notifications & System Alerts ({len(active_notifs)} active)", expanded=True):
        for n in active_notifs:
            if n.severity == "high":
                st.error(f"**[{n.category.upper()}] {n.title}**: {n.message} — *Suggested Action:* {n.action_hint}")
            elif n.severity == "medium":
                st.warning(f"**[{n.category.upper()}] {n.title}**: {n.message} — *Suggested Action:* {n.action_hint}")
            else:
                st.info(f"**[{n.category.upper()}] {n.title}**: {n.message} — *Suggested Action:* {n.action_hint}")

# Build Ladder Status Banner
st.info(
    "📌 **MessWise Core Features Integrated & Verified**: "
    "Implemented modules: **Forecasting (A1–A6 + E1)**, "
    "**Quantity Planning & Joint Monte-Carlo (B1–B6)**, **Waste Intelligence & Root Causes (D1–D7 + E2)**, "
    "**Savings Simulator & Blind Reveal (E3–E4)**, **Surplus Routing & Safety Clock (G1–G2)**, "
    "**Register CSV Import (C4)**, **Voice (C5)**, **Photo Geometry (C6)**, **Tally (C7)**, **Scale Adapter (C8)**, "
    "and **Sustainability & Financial Governance (H1–H6, I5–I9)**. "
    f"Current database state: **{real_meals_count} real pilot meals**, **{synth_meals_count} synthetic demonstration meals**."
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Real Pilot Meals Logged", real_meals_count, help="Recorded operational data from kitchen")
col2.metric("Synthetic Demo Meals", synth_meals_count, help="Clearly labelled development & demo records")
col3.metric("Registered Dishes", dishes_count, help="Unique dishes in kitchen catalog")
col4.metric("Total Dish Measurements", dish_logs_count, help="Cooked vs leftover data points")

st.markdown("---")

# Architectural Overview
st.subheader("System Architecture & Roadmap (PLAN.md)")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
    ### 🔄 The Closed Decision Loop
    1. **Predict**: Meal-wise headcount forecast with conformal uncertainty intervals.
    2. **Plan**: Dish quantities at manager-controlled service levels (Newsvendor logic).
    3. **Cook**: Kitchen staff cooks to plan or logs human overrides with reasons.
    4. **Measure**: Leftovers and shortages recorded via Kitchen Mode (form / voice / photo).
    5. **Learn**: Shortage-aware (Kaplan-Meier) appetite learning updates models continuously.
    6. **Safe Route (Exception)**: FSSAI-compliant surplus recovery alerts when excess occurs.
    """)

with col_right:
    st.markdown("""
    ### 🛡️ Core Operational Principles
    - **Prevention First**: Prevent surplus before cooking; surplus donation is an exception path.
    - **Zero Leftover Re-serving**: Cooked leftovers are never re-served to students.
    - **Privacy by Design**: No student names, personal IDs, or biometric data stored.
    - **Data Integrity**: Real pilot data and synthetic demo data are never mixed.
    - **Food-Safety Gate**: Software blocks donation when safe window expires or data is missing.
    """)

st.markdown("---")

st.subheader("🧭 Navigation")
st.markdown("""
Use the sidebar to navigate between operational modules:
- 👉 **Kitchen**: **[Active]** Operational logging for meal context, cooked quantities, leftovers, and run-outs.
- 📋 **Planner**: **[Active - B1-B5]** Cooking quantity recommendations, Newsvendor cost-awareness, and service-level slider.
- 🔬 **Forecast Lab**: **[Active - A1-A6]** Headcount forecasting engine, honest baselines, and prediction log.
- 🛡️ **Surplus Routing**: **[Active - G1-G2]** Predicted-surplus alerts, FSSAI Food-Safety Clock, and manager review.
- 🎮 **Simulator**: **[Active - E3-E4]** Counterfactual savings simulator and blind-reveal replay.
- 📊 **Waste Intelligence**: **[Active - D1-D3]** Dish-wise waste rankings and root-cause analysis.
- 🌱 **Impact**: *(Phase 4)* Measured kilograms, rupees, and CO₂e saved.
- 📑 **Reports & Governance**: **[Active]** Audit log, prediction ledger, and institutional exports.
""")

