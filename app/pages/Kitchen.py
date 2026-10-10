"""MessWise - Kitchen Measurement & Data Entry.

Phase 1 Functional Data Entry Screen.
Allows kitchen staff to record meal attendance context, cooked quantities,
leftovers, run-outs, and waste reasons.
Strictly validates inputs using shared validation logic before saving to SQLite.
Clearly separates real pilot data from synthetic development data.
"""

import sys
from datetime import date
from pathlib import Path

# Ensure root directory is on Python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import pandas as pd
from sqlalchemy import select

from messwise.db import (
    Dish,
    DishLog,
    Meal,
    create_dish_log_record,
    create_meal_record,
    get_or_create_dish,
    get_session_factory,
    init_db,
    list_meals_query,
)
from messwise.validation import (
    DishLogCreate,
    MealCreate,
    VALID_MEAL_TYPES,
    VALID_REASON_TAGS,
    VALID_UNITS,
    VALID_WASTE_STAGES,
    validate_dish_log_dict,
    validate_meal_dict,
)
from messwise.voice import (
    AudioTranscriber,
    parse_voice_utterance,
    VoiceParseResult,
    HAS_SPEECH_RECOGNITION,
)
from messwise.photo_waste import CONTAINER_PROFILES, estimate_waste_from_photo
from messwise.tally import STANDARD_TIME_BUCKETS, compute_arrival_curve_for_meal
from messwise.scale import parse_and_validate_scale_payload
from messwise.csv_import import preview_register_csv, import_register_csv
from messwise.db import record_entrance_tally, get_meal_tallies


st.set_page_config(page_title="MessWise | Kitchen Mode", page_icon="🍳", layout="wide")
init_db()

st.title("🍳 Kitchen Data Entry")
st.caption("Measure Cooked and Leftover Food per Meal (PLAN.md Module C)")

# Session state initialization for dish list
if "dish_rows" not in st.session_state:
    st.session_state.dish_rows = [
        {
            "dish_name": "Steamed Rice",
            "cooked_qty": 45.0,
            "leftover_qty": 4.5,
            "unit": "kg",
            "ran_out": False,
            "waste_stage": "serving_surplus",
            "reason_tag": "overproduction",
        }
    ]

# Data Type Banner
col_mode1, col_mode2 = st.columns([2, 1])
with col_mode1:
    is_synth_selection = st.radio(
        "Select Data Mode:",
        options=[0, 1],
        format_func=lambda x: "🟢 Real Pilot Data (Kitchen Measurement)" if x == 0 else "🧪 Synthetic / Demo Data (Development Only)",
        index=0,
        horizontal=True,
        help="Real and synthetic records are stored with distinct is_synthetic flags and never conflated."
    )

with col_mode2:
    if is_synth_selection == 0:
        st.success("Target: **Real Pilot Record** (`is_synthetic = 0`)")
    else:
        st.warning("Target: **Synthetic Demo Record** (`is_synthetic = 1`)")

st.markdown("---")

# Section 1: Meal Context
st.subheader("1. Meal Context & Attendance")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    meal_date = st.date_input("Meal Date", value=date.today())
with col_m2:
    meal_type = st.selectbox("Meal Type", options=list(VALID_MEAL_TYPES), index=1)
with col_m3:
    headcount = st.number_input("Headcount (Students Served)", min_value=0, value=420, step=1)
with col_m4:
    hostel_strength = st.number_input("Hostel Strength (Total Capacity)", min_value=0, value=500, step=1)

col_f1, col_f2, col_f3, col_w1, col_w2 = st.columns(5)
with col_f1:
    event_flag = st.checkbox("Event / Fest Day", value=False)
with col_f2:
    exam_flag = st.checkbox("Exam Period", value=False)
with col_f3:
    holiday_flag = st.checkbox("Holiday / Weekend", value=False)
with col_w1:
    temp_c = st.number_input("Temperature (°C) [Optional]", min_value=0.0, max_value=50.0, value=28.0, step=0.5)
with col_w2:
    rain_mm = st.number_input("Rainfall (mm) [Optional]", min_value=0.0, max_value=200.0, value=0.0, step=0.5)

# ==============================================================================
# Module C4: Historical Register & Headcount CSV Import
# ==============================================================================
with st.expander("📥 Register & Headcount CSV Import (C4 — Historical Attendance Onboarding)", expanded=False):
    st.markdown(
        "Upload mess attendance registers or billing records to seed forecasting and baseline metrics.<br/>"
        "• *Validation Guard*: Enforces date format, meal slot normalisation, non-negative counts, and capacity limits.<br/>"
        "• *Duplicate Protection*: Detects and rejects duplicate dates/meals already in database or within the file.",
        unsafe_allow_html=True,
    )
    uploaded_csv = st.file_uploader(
        "Select Attendance Register CSV:",
        type=["csv"],
        key="c4_csv_upload",
        help="Upload CSV with date, meal_type, and headcount columns",
    )
    if uploaded_csv is not None:
        csv_bytes = uploaded_csv.getvalue()
        preview = preview_register_csv(csv_bytes)
        if preview.total_rows == 0:
            st.error(f"Error reading CSV: {preview.status_message}")
        else:
            st.info(f"📊 **File Preview**: Found {preview.total_rows} rows with headers: `{', '.join(preview.headers)}`")
            c4_c1, c4_c2, c4_c3 = st.columns(3)
            with c4_c1:
                date_opts = preview.headers
                date_idx = date_opts.index(preview.suggested_mapping["date"]) if preview.suggested_mapping.get("date") in date_opts else 0
                c4_date_col = st.selectbox("Date Column:", options=date_opts, index=date_idx, key="c4_map_date")
            with c4_c2:
                meal_opts = preview.headers
                meal_idx = meal_opts.index(preview.suggested_mapping["meal_type"]) if preview.suggested_mapping.get("meal_type") in meal_opts else min(1, len(meal_opts)-1)
                c4_meal_col = st.selectbox("Meal Type Column:", options=meal_opts, index=meal_idx, key="c4_map_meal")
            with c4_c3:
                head_opts = preview.headers
                head_idx = head_opts.index(preview.suggested_mapping["headcount"]) if preview.suggested_mapping.get("headcount") in head_opts else min(2, len(head_opts)-1)
                c4_head_col = st.selectbox("Headcount Column:", options=head_opts, index=head_idx, key="c4_map_head")

            c4_map = {
                "date": c4_date_col,
                "meal_type": c4_meal_col,
                "headcount": c4_head_col,
            }
            if preview.suggested_mapping.get("hostel_strength") in preview.headers:
                c4_map["hostel_strength"] = preview.suggested_mapping["hostel_strength"]

            st.markdown("**Sample Rows from Upload:**")
            st.dataframe(pd.DataFrame(preview.sample_rows), use_container_width=True)

            env_label = "Synthetic Demo" if is_synth_selection == 1 else "Real Pilot"
            st.warning(f"Target Environment: **{env_label}** (`is_synthetic = {is_synth_selection}`). Records will be tagged with `source='register_csv'`.")

            if st.button(f"Confirm & Import {preview.total_rows} Records to {env_label}", key="c4_btn_import", type="primary"):
                session_factory = get_session_factory()
                with session_factory() as s:
                    res = import_register_csv(
                        session=s,
                        csv_content=csv_bytes,
                        column_mapping=c4_map,
                        is_synthetic=is_synth_selection,
                        who="kitchen_operator",
                        default_hostel_strength=int(hostel_strength),
                    )
                    if res.accepted_rows > 0:
                        st.success(f"🎉 **Import Complete**: {res.accepted_rows} meals imported successfully.")
                    if res.rejected_rows > 0:
                        st.warning(f"⚠️ **{res.rejected_rows} rows were rejected** due to duplicate or validation errors.")
                        if res.rejected_csv_bytes:
                            st.download_button(
                                label="📥 Download Rejection Error Report (CSV)",
                                data=res.rejected_csv_bytes,
                                file_name="rejected_import_rows.csv",
                                mime="text/csv",
                                key="c4_btn_download_errors",
                            )
                st.rerun()

st.markdown("---")

# Section 2: Dish-level Measurements
st.subheader("2. Dish Measurements (Cooked vs Leftover)")

# ==============================================================================
# C5: Multilingual Voice Logging (English, Hindi, Telugu transliteration)
# ==============================================================================
with st.expander("🎙️ Voice-Assisted Dish Entry (C5 — English, Hindi, Telugu)", expanded=False):
    st.markdown(
        "Speak meal measurements using natural language. Examples:<br/>"
        "• *English*: `rice cooked 40 kg, left 6 kg`<br/>"
        "• *Hindi*: `chawal 40 kilo bana, 6 kilo bacha`<br/>"
        "• *Telugu*: `annam 40 kilolu vandamu, 6 kilolu migilindi`",
        unsafe_allow_html=True,
    )

    v_c1, v_c2 = st.columns([1, 2])
    with v_c1:
        speech_lang = st.selectbox(
            "Speech Language:",
            options=["en-IN", "hi-IN", "te-IN"],
            format_func=lambda l: {"en-IN": "English (India)", "hi-IN": "Hindi (हिन्दी)", "te-IN": "Telugu (తెలుగు)"}.get(l, l),
            key="v_speech_lang",
        )
    with v_c2:
        st.caption("Microphone recording processes temporary in-memory audio and discards it immediately for privacy.")

    # Diagnostic Voice Status Indicator (Prompt Requirement 2.B)
    transcriber = AudioTranscriber()
    backend_status = transcriber.get_backend_status()
    st_c1, st_c2 = st.columns([1, 1])
    with st_c1:
        st.info("🎙️ **Recording Status:** Available (Browser Microphone)")
    with st_c2:
        if backend_status["is_available"]:
            st.success("⚙️ **Backend Status:** Transcription Backend Configured")
        else:
            st.warning("⚙️ **Backend Status:** Transcription Unavailable (Manual Fallback Active)")

    # Audio recording widget & text fallback
    voice_audio = st.audio_input("Record Voice Measurement (Microphone):", key="v_audio_mic")
    voice_text_input = st.text_input(
        "Or Type Spoken Utterance (Manual / Testing Fallback):",
        placeholder="e.g. rice cooked 40 kg, left 6 kg",
        key="v_text_input",
    )

    if st.button("Transcribe & Parse Speech", key="v_btn_parse"):
        raw_transcript = ""
        transcribe_error = None
        voice_mode = None

        if voice_audio is not None:
            if transcriber.is_available:
                audio_bytes = voice_audio.getvalue()
                success, t_text, err = transcriber.transcribe_audio_bytes(audio_bytes, language=speech_lang)
                if success:
                    raw_transcript = t_text
                    voice_mode = "audio_success"
                else:
                    transcribe_error = err
                    voice_mode = "audio_failed"
            else:
                transcribe_error = "Speech recognition library unavailable in running Python environment."
                voice_mode = "audio_failed"

        # Fallback to text input if audio was not provided or failed
        if not raw_transcript and voice_text_input.strip():
            raw_transcript = voice_text_input.strip()
            if voice_mode == "audio_failed":
                voice_mode = "audio_failed_text_fallback"
            else:
                voice_mode = "manual_text"

        st.session_state.voice_mode = voice_mode
        st.session_state.voice_transcribe_error = transcribe_error

        if transcribe_error and not raw_transcript:
            st.error(f"🔴 **Transcription Unavailable:** {transcribe_error}")
        elif not raw_transcript:
            st.warning("Please record audio with the microphone or type an utterance into the fallback field.")
        else:
            # Parse utterance with C5 rule-based parser
            parse_res = parse_voice_utterance(raw_transcript, language_hint=speech_lang)
            st.session_state.voice_parsed_dish = parse_res

    # Display Status Banner based on Parse Result Source
    if "voice_mode" in st.session_state and st.session_state.voice_mode:
        v_mode = st.session_state.voice_mode
        if v_mode == "audio_success":
            st.success("🟢 **Transcription Succeeded:** Speech recognized and transcribed from genuine microphone audio.")
        elif v_mode == "audio_failed_text_fallback":
            st.warning(
                f"⚠️ **Transcription Unavailable:** {st.session_state.get('voice_transcribe_error')}\n\n"
                "👉 **Manual Fallback Active:** Parsed text from manual entry field."
            )
        elif v_mode == "manual_text":
            st.info("ℹ️ **Manual Fallback Active:** Parsed typed utterance text. *(No audio transcription performed)*")

    # Display Pre-filled Review & Confirmation Card if parsed
    if "voice_parsed_dish" in st.session_state and st.session_state.voice_parsed_dish:
        vres: VoiceParseResult = st.session_state.voice_parsed_dish
        st.markdown("---")
        st.markdown(f"#### 📝 Review Parsed Measurements: *\"{vres.raw_transcript}\"*")

        if vres.confidence_status == "high":
            st.success("🟢 **High Confidence Parsing** — All measurement slots identified.")
        elif vres.confidence_status == "moderate":
            st.info("🟡 **Moderate Confidence** — Please verify the dish name or unit.")
        else:
            st.warning(f"🔴 **Review Required**: {vres.explanation}")

        # Editable Review Form
        with st.form("form_voice_confirm"):
            rv_col1, rv_col2, rv_col3, rv_col4, rv_col5 = st.columns([2, 1.5, 1.5, 1, 1])
            with rv_col1:
                rev_dish = st.text_input("Dish Name:", value=vres.dish_name or "Rice", key="rev_dish_name")
            with rv_col2:
                rev_cooked = st.number_input("Cooked Qty:", min_value=0.0, value=float(vres.cooked_qty or 0.0), step=0.5, key="rev_cooked_qty")
            with rv_col3:
                rev_leftover = st.number_input("Leftover Qty:", min_value=0.0, value=float(vres.leftover_qty or 0.0), step=0.5, key="rev_leftover_qty")
            with rv_col4:
                u_opts = list(VALID_UNITS)
                u_idx = u_opts.index(vres.cooked_unit) if vres.cooked_unit in u_opts else 0
                rev_unit = st.selectbox("Unit:", options=u_opts, index=u_idx, key="rev_unit")
            with rv_col5:
                rev_ranout = st.checkbox("Ran Out", value=bool(vres.ran_out), key="rev_ranout")

            submit_v_apply = st.form_submit_button("Confirm & Apply to Meal Dish Rows", type="primary")
            if submit_v_apply:
                if rev_leftover > rev_cooked and rev_cooked > 0:
                    st.error("Validation Error: Leftover quantity cannot exceed cooked quantity.")
                else:
                    # Append or update dish row
                    new_entry = {
                        "dish_name": rev_dish.strip(),
                        "cooked_qty": float(rev_cooked),
                        "leftover_qty": float(rev_leftover),
                        "unit": rev_unit,
                        "ran_out": rev_ranout,
                        "waste_stage": "serving_surplus",
                        "reason_tag": "overproduction" if rev_leftover > 0 else "none",
                    }
                    # Replace first placeholder if empty, else append
                    if len(st.session_state.dish_rows) == 1 and not st.session_state.dish_rows[0].get("dish_name"):
                        st.session_state.dish_rows[0] = new_entry
                    else:
                        st.session_state.dish_rows.append(new_entry)
                    st.session_state.voice_parsed_dish = None
                    st.success(f"Confirmed! Added **{rev_dish}** ({rev_cooked} {rev_unit} cooked, {rev_leftover} {rev_unit} leftover) to meal log.")
                    st.rerun()

# ==============================================================================
# Module C6: Calibrated Photo-Based Waste Estimation
# ==============================================================================
with st.expander("📸 Calibrated Photo Waste Estimation (C6 — Bin / Pan Visual Assistant)", expanded=False):
    st.markdown(
        "Estimate leftover mass from collection bin or serving pan photos using a scale-calibrated curve.<br/>"
        "• *Container*: Known geometry with reference level markers.<br/>"
        "• *Limitation*: Visual estimate only. Does not replace physical kitchen scales. Staff must verify and confirm.",
        unsafe_allow_html=True,
    )
    p_c1, p_c2 = st.columns([1, 1])
    with p_c1:
        p_container = st.selectbox(
            "Collection Container:",
            options=list(CONTAINER_PROFILES.keys()),
            format_func=lambda k: CONTAINER_PROFILES[k]["name"],
            key="p_container_sel",
        )
        p_dish = st.selectbox(
            "Food / Dish Type in Container:",
            options=["Rice", "Dal Tadka", "Mixed Veg Curry", "Curd", "Roti", "default"],
            key="p_dish_sel",
        )
        p_marker = st.slider(
            "Container Visual Fill Graduation Line (% fill):",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            key="p_marker_slider",
            help="Adjust to match the physical container graduation level seen in the photo",
        )
    with p_c2:
        p_file = st.file_uploader(
            "Upload Bin / Pan Photograph (In-Memory Processing):",
            type=["jpg", "jpeg", "png"],
            key="p_file_upload",
        )
        st.caption("🔒 Image processed in-memory and discarded. Zero faces or personal data stored.")

    if st.button("Analyze Bin Fill & Estimate Weight", key="p_btn_analyze"):
        img_bytes = p_file.getvalue() if p_file is not None else b"simulated_container_image"
        p_est = estimate_waste_from_photo(
            image_bytes=img_bytes,
            dish_name=p_dish,
            container_type=p_container,
            manual_fill_fraction=p_marker / 100.0,
        )
        st.session_state.photo_estimate_res = p_est

    if "photo_estimate_res" in st.session_state and st.session_state.photo_estimate_res:
        pest = st.session_state.photo_estimate_res
        st.markdown("---")
        st.markdown(f"#### 🔍 Calibrated Photo Estimate: **{pest.dish_name}**")
        
        pe_c1, pe_c2, pe_c3 = st.columns(3)
        with pe_c1:
            st.metric("Estimated Leftover Mass", f"{pest.estimated_kg:.2f} kg", help="Scale-calibrated point estimate")
        with pe_c2:
            st.metric("Uncertainty Range", f"{pest.low_kg:.2f} – {pest.high_kg:.2f} kg", help="±15% container fill uncertainty band")
        with pe_c3:
            st.metric("Volume Proxy", f"{pest.fill_volume_litres:.1f} Litres", f"{pest.confidence_label} Confidence")

        st.warning(f"⚠️ **Limitation Notice**: {pest.limitation_disclosure}")

        if st.button(f"Confirm & Apply {pest.estimated_kg:.2f} kg to Meal Dish Rows", key="p_btn_apply", type="primary"):
            new_entry = {
                "dish_name": pest.dish_name if pest.dish_name != "default" else "Rice",
                "cooked_qty": float(round(pest.estimated_kg * 1.5, 1)),
                "leftover_qty": float(pest.estimated_kg),
                "unit": "kg",
                "ran_out": False,
                "waste_stage": "serving_surplus",
                "reason_tag": "overproduction",
            }
            if len(st.session_state.dish_rows) == 1 and not st.session_state.dish_rows[0].get("dish_name"):
                st.session_state.dish_rows[0] = new_entry
            else:
                st.session_state.dish_rows.append(new_entry)
            st.session_state.photo_estimate_res = None
            st.success(f"Applied {pest.estimated_kg:.2f} kg leftover to dish log rows. Please review and submit meal.")
            st.rerun()

# ==============================================================================
# Module C7: Timestamped Entrance Attendance Tally
# ==============================================================================
with st.expander("⏱️ Timestamped Entrance Attendance Tally (C7 — 15-Minute Arrival Curve)", expanded=False):
    st.markdown(
        "Record aggregate arrivals in 15-minute service checkpoints to train the empirical arrival curve a(τ) "
        "and calculate last-minute headcount nowcasts.<br/>"
        "• *Privacy Rule*: Aggregate headcounts only. Never records student names, IDs, or biometrics.",
        unsafe_allow_html=True,
    )
    t_c1, t_c2, t_c3 = st.columns([1.5, 1.5, 1])
    with t_c1:
        t_bucket = st.selectbox(
            "Service Time Checkpoint:",
            options=STANDARD_TIME_BUCKETS,
            key="t_bucket_sel",
        )
    with t_c2:
        t_count = st.number_input(
            "Headcount Arrivals in this 15-min Bucket:",
            min_value=0,
            max_value=1500,
            value=65,
            step=5,
            key="t_count_input",
        )
    with t_c3:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("Log Tally Bucket", key="t_btn_log", type="primary"):
            session_factory = get_session_factory()
            with session_factory() as s:
                recent_meal = s.execute(
                    select(Meal).where(Meal.date == str(meal_date), Meal.meal_type == meal_type, Meal.is_synthetic == is_synthetic)
                ).scalars().first()
                if recent_meal:
                    record_entrance_tally(
                        session=s,
                        meal_id=recent_meal.id,
                        time_bucket=t_bucket,
                        headcount_count=int(t_count),
                        recorded_by="dining_monitor",
                        is_synthetic=is_synth_selection,
                    )
                    st.success(f"Recorded {t_count} arrivals for bucket '{t_bucket}' on Meal #{recent_meal.id}.")
                else:
                    st.info(f"Buffered {t_count} arrivals for '{t_bucket}'. Save the meal below to permanently associate records.")
            st.rerun()

    session_factory = get_session_factory()
    with session_factory() as s:
        recent_m = s.execute(
            select(Meal).where(Meal.date == str(meal_date), Meal.meal_type == meal_type, Meal.is_synthetic == is_synth_selection)
        ).scalars().first()
        if recent_m:
            analysis = compute_arrival_curve_for_meal(s, recent_m.id, expected_headcount=int(headcount))
            if analysis.bucket_counts:
                st.markdown(f"**Arrival Curve a(τ) for Today's {meal_type} (Meal #{recent_m.id})**: Total Logged: **{analysis.total_recorded_count} diners**")
                df_tally = pd.DataFrame(analysis.bucket_counts)[["time_bucket", "count", "cumulative_count", "arrival_fraction"]]
                df_tally.columns = ["Time Bucket", "Arrivals", "Cumulative Diners", "Arrival Fraction a(τ)"]
                st.dataframe(df_tally, use_container_width=True, hide_index=True)
                if analysis.nowcast_headcount:
                    st.info(f"🔮 **Live Nowcast Checkpoint**: Based on current arrival fraction, projected final meal headcount is **{analysis.nowcast_headcount} attendees** (Baseline Plan: {headcount}).")

# ==============================================================================
# Module C8: Smart Scale Integration Adapter (ESP32 + HX711 Load Cell Platform)
# ==============================================================================
with st.expander("⚖️ Smart-Scale Load-Cell Platform (C8 — Digital Scale Telemetry)", expanded=False):
    st.markdown(
        "Digital load-cell adapter interface for institutional mess weighing platforms (ESP32 + HX711).<br/>"
        "• *Hardware Status*: Physical ESP32 scale platform disconnected / awaiting hardware pairing. "
        "Manual measurement remains authoritative fallback.<br/>"
        "• *Validation Guard*: Enforces tare calibration, stable readings, and strict metric units (kg). "
        "Staff must explicitly verify and apply readings before persisting.",
        unsafe_allow_html=True,
    )
    sc_c1, sc_c2 = st.columns([1, 1])
    with sc_c1:
        sc_device_id = st.text_input("Device ID / Serial:", value="HX711-ESP32-SCALE01", key="sc_device_id")
        sc_gross = st.number_input("Gross Weight (kg):", min_value=0.0, value=12.45, step=0.05, format="%.2f", key="sc_gross")
        sc_tare = st.number_input("Tare / Container Weight (kg):", min_value=0.0, value=2.10, step=0.05, format="%.2f", key="sc_tare")
    with sc_c2:
        sc_unit = st.selectbox("Scale Telemetry Unit:", options=["kg", "litres", "lbs"], index=0, key="sc_unit")
        sc_stable = st.checkbox("Scale Platform Settled / Stable", value=True, key="sc_stable")
        sc_dish = st.selectbox("Assign Weight to Dish:", options=["Rice", "Dal Tadka", "Mixed Veg Curry", "Curd", "Roti"], key="sc_dish_sel")

    if st.button("Validate Scale Reading", key="sc_btn_validate"):
        reading_payload = {
            "device_id": sc_device_id,
            "gross_weight_kg": sc_gross,
            "tare_weight_kg": sc_tare,
            "net_weight_kg": sc_gross - sc_tare,
            "unit": sc_unit,
            "is_stable": sc_stable,
        }
        scale_res = parse_and_validate_scale_payload(reading_payload)
        st.session_state.scale_reading_res = scale_res

    if "scale_reading_res" in st.session_state and st.session_state.scale_reading_res:
        sres = st.session_state.scale_reading_res
        st.markdown("---")
        if sres.is_valid:
            st.success(f"🟢 **Scale Reading Validated ({sres.device_id})**: Net Weight = **{sres.net_weight_kg:.2f} kg**")
            st.caption(f"Status: {sres.status_message} | Provenance: entry_method='{sres.entry_method}'")
            if st.button(f"Confirm & Apply {sres.net_weight_kg:.2f} kg to Meal Dish Rows", key="sc_btn_apply", type="primary"):
                new_entry = {
                    "dish_name": sc_dish,
                    "cooked_qty": float(round(sres.net_weight_kg * 1.5, 1)),
                    "leftover_qty": float(sres.net_weight_kg),
                    "unit": "kg",
                    "ran_out": False,
                    "waste_stage": "serving_surplus",
                    "reason_tag": "overproduction",
                }
                if len(st.session_state.dish_rows) == 1 and not st.session_state.dish_rows[0].get("dish_name"):
                    st.session_state.dish_rows[0] = new_entry
                else:
                    st.session_state.dish_rows.append(new_entry)
                st.session_state.scale_reading_res = None
                st.success(f"Applied smart-scale reading of {sres.net_weight_kg:.2f} kg to dish rows. Review and submit.")
                st.rerun()
        else:
            st.error(f"🔴 **Scale Reading Rejected**: {sres.status_message}")
            st.warning("Please tare scale platform or use manual weight entry fallback.")

st.markdown("---")

# Controls to add/remove dish rows
c_btn1, c_btn2, _ = st.columns([1, 1, 4])

with c_btn1:
    if st.button("➕ Add Another Dish"):
        st.session_state.dish_rows.append(
            {
                "dish_name": "",
                "cooked_qty": 0.0,
                "leftover_qty": 0.0,
                "unit": "kg",
                "ran_out": False,
                "waste_stage": "serving_surplus",
                "reason_tag": "none",
            }
        )
        st.rerun()

with c_btn2:
    if len(st.session_state.dish_rows) > 1 and st.button("➖ Remove Last Dish"):
        st.session_state.dish_rows.pop()
        st.rerun()

# Render each dish row
updated_dishes = []
for idx, d in enumerate(st.session_state.dish_rows):
    st.markdown(f"**Dish #{idx + 1}**")
    d_col1, d_col2, d_col3, d_col4, d_col5, d_col6, d_col7 = st.columns([2, 1.2, 1.2, 1, 1, 1.5, 1.5])

    with d_col1:
        dish_name = st.text_input(f"Dish Name #{idx+1}", value=d.get("dish_name", ""), key=f"d_name_{idx}")
    with d_col2:
        cooked_qty = st.number_input(f"Cooked Qty #{idx+1}", min_value=0.0, value=float(d.get("cooked_qty", 0.0)), step=0.5, key=f"d_cooked_{idx}")
    with d_col3:
        leftover_qty = st.number_input(f"Leftover Qty #{idx+1}", min_value=0.0, value=float(d.get("leftover_qty", 0.0)), step=0.5, key=f"d_left_{idx}")
    with d_col4:
        unit = st.selectbox(f"Unit #{idx+1}", options=list(VALID_UNITS), index=list(VALID_UNITS).index(d.get("unit", "kg")), key=f"d_unit_{idx}")
    with d_col5:
        ran_out = st.checkbox(f"Ran Out #{idx+1}", value=bool(d.get("ran_out", False)), key=f"d_ranout_{idx}")
    with d_col6:
        waste_stage = st.selectbox(f"Stage #{idx+1}", options=list(VALID_WASTE_STAGES), index=list(VALID_WASTE_STAGES).index(d.get("waste_stage", "serving_surplus")), key=f"d_stage_{idx}")
    with d_col7:
        reason_tag = st.selectbox(f"Reason #{idx+1}", options=list(VALID_REASON_TAGS), index=list(VALID_REASON_TAGS).index(d.get("reason_tag", "none")), key=f"d_reason_{idx}")

    updated_dishes.append({
        "dish_name": dish_name,
        "cooked_qty": cooked_qty,
        "leftover_qty": leftover_qty,
        "unit": unit,
        "ran_out": ran_out,
        "waste_stage": waste_stage,
        "reason_tag": reason_tag,
    })

st.session_state.dish_rows = updated_dishes

st.markdown("---")

# Submit Button and Action
if st.button("💾 Validate & Save Meal Record", type="primary", use_container_width=True):
    # Prepare meal payload
    meal_dict = {
        "date": meal_date.strftime("%Y-%m-%d"),
        "meal_type": meal_type,
        "headcount": int(headcount),
        "hostel_strength": int(hostel_strength),
        "event_flag": 1 if event_flag else 0,
        "exam_flag": 1 if exam_flag else 0,
        "holiday_flag": 1 if holiday_flag else 0,
        "temp_c": float(temp_c),
        "rain_mm": float(rain_mm),
        "source": "manual",
        "is_synthetic": is_synth_selection,
    }

    # Validate Meal
    is_meal_valid, meal_errors = validate_meal_dict(meal_dict)

    # Validate Dishes
    dish_errors = []
    if not updated_dishes:
        dish_errors.append("At least one dish record is required.")

    for idx, d_data in enumerate(updated_dishes):
        is_d_valid, d_errs = validate_dish_log_dict(d_data)
        for err in d_errs:
            dish_errors.append(f"Dish #{idx + 1} ({d_data.get('dish_name') or 'Unnamed'}): {err}")

    # Combine errors
    all_errors = meal_errors + dish_errors

    if all_errors:
        st.error("❌ Validation Failed. Please correct the following errors before saving:")
        for err in all_errors:
            st.markdown(f"- ⚠️ {err}")
    else:
        # Save atomically into database
        session_factory = get_session_factory()
        with session_factory() as session:
            try:
                # 1. Create Meal record
                meal_pydantic = MealCreate(**meal_dict)
                meal_record = create_meal_record(session=session, meal_data=meal_pydantic)
                session.flush()

                # 2. Register Dishes and Dish Logs
                created_logs = []
                for d_data in updated_dishes:
                    dish_obj = get_or_create_dish(
                        session=session,
                        name=d_data["dish_name"],
                        unit=d_data["unit"],
                        is_synthetic=is_synth_selection,
                    )
                    session.flush()

                    dish_log_pydantic = DishLogCreate(
                        meal_id=meal_record.id,
                        dish_id=dish_obj.id,
                        cooked_qty=d_data["cooked_qty"],
                        leftover_qty=d_data["leftover_qty"],
                        unit=d_data["unit"],
                        ran_out=1 if d_data["ran_out"] else 0,
                        waste_stage=d_data["waste_stage"],
                        reason_tag=d_data["reason_tag"],
                        entry_method="form",
                        is_synthetic=is_synth_selection,
                    )
                    dish_log_record = create_dish_log_record(session=session, dish_log_data=dish_log_pydantic)
                    created_logs.append((dish_obj.name, dish_log_record))

                session.commit()

                # Show Success Confirmation
                st.success(f"✅ Successfully saved Meal #{meal_record.id} with {len(created_logs)} dish measurements!")
                
                # Show Stored Record Details
                label_badge = "🟢 REAL PILOT DATA" if is_synth_selection == 0 else "🧪 SYNTHETIC DEMO DATA"
                st.markdown(f"### Stored Meal Record [ID: {meal_record.id}] — {label_badge}")
                
                meal_summary_df = pd.DataFrame([
                    {
                        "Meal ID": meal_record.id,
                        "Date": meal_record.date,
                        "Type": meal_record.meal_type.title(),
                        "Headcount": meal_record.headcount,
                        "Hostel Strength": meal_record.hostel_strength,
                        "Flags": f"Event: {meal_record.event_flag}, Exam: {meal_record.exam_flag}, Hol: {meal_record.holiday_flag}",
                        "Weather": f"{meal_record.temp_c}°C / {meal_record.rain_mm} mm",
                        "Data Mode": "Real Pilot" if meal_record.is_synthetic == 0 else "Synthetic",
                    }
                ])
                st.dataframe(meal_summary_df, use_container_width=True, hide_index=True)

                dishes_summary = [
                    {
                        "Dish Name": name,
                        "Cooked Qty": dl.cooked_qty,
                        "Leftover Qty": dl.leftover_qty,
                        "Unit": dl.unit,
                        "Ran Out": "Yes" if dl.ran_out == 1 else "No",
                        "Waste Stage": dl.waste_stage,
                        "Reason": dl.reason_tag,
                    }
                    for name, dl in created_logs
                ]
                st.dataframe(pd.DataFrame(dishes_summary), use_container_width=True, hide_index=True)

            except Exception as e:
                session.rollback()
                st.error(f"❌ Database error while saving: {str(e)}")

st.markdown("---")

# Section 3: Recent Logged Records Viewer
st.subheader("📋 Recent Kitchen Logs")

filter_choice = st.selectbox(
    "Filter Stored Records:",
    options=["All", "Real Pilot Data Only", "Synthetic Demo Data Only"],
    index=0
)

synth_filter = None
if filter_choice == "Real Pilot Data Only":
    synth_filter = 0
elif filter_choice == "Synthetic Demo Data Only":
    synth_filter = 1

session_factory = get_session_factory()
with session_factory() as session:
    meals = list_meals_query(session=session, is_synthetic=synth_filter, limit=15)
    if not meals:
        st.info("No meal records found for the selected filter.")
    else:
        table_rows = []
        for m in meals:
            table_rows.append({
                "Meal ID": m.id,
                "Date": m.date,
                "Meal Type": m.meal_type.title(),
                "Headcount": m.headcount,
                "Hostel Strength": m.hostel_strength,
                "Mode": "Real Pilot" if m.is_synthetic == 0 else "Synthetic",
                "Dishes Logged": len(m.dish_logs),
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        with st.expander("🔍 View Dish Breakdown of Latest Logged Meals"):
            for m in meals[:5]:
                mode_tag = "🟢 Real" if m.is_synthetic == 0 else "🧪 Synthetic"
                st.markdown(f"**Meal #{m.id} ({m.date} - {m.meal_type.title()})** [{mode_tag}]")
                if m.dish_logs:
                    d_breakdown = [
                        {
                            "Dish": dl.dish.name if dl.dish else f"ID {dl.dish_id}",
                            "Cooked": dl.cooked_qty,
                            "Leftover": dl.leftover_qty,
                            "Unit": dl.unit,
                            "Ran Out": "Yes" if dl.ran_out else "No",
                            "Stage": dl.waste_stage,
                            "Reason": dl.reason_tag,
                        }
                        for dl in m.dish_logs
                    ]
                    st.dataframe(pd.DataFrame(d_breakdown), use_container_width=True, hide_index=True)
                else:
                    st.caption("No dish logs attached.")
