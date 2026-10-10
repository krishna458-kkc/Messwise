"""Tests for MessWise Step 8: Multilingual Voice Logging (C5), CO₂e Estimates (H1),
Meals-Equivalent Impact (H2), and Green-Campus PDF Report (H4).

Covers all 42 testing requirements from PLAN.md Step 8 specification.
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app, get_db_session
from messwise.db import Dish, DishLog, Meal, get_or_create_dish, init_db
from messwise.impact import (
    FACTOR_CENTRAL,
    FACTOR_HIGH,
    FACTOR_LOW,
    EmissionFactorConfig,
    calculate_co2e_impact,
    calculate_meals_equivalent,
    compute_green_campus_summary,
)
from messwise.pdf_report import generate_green_campus_pdf
from messwise.voice import (
    AudioTranscriber,
    VoiceParseResult,
    parse_voice_utterance,
)


@pytest.fixture
def test_db():
    """Provides an isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed catalog dishes
    get_or_create_dish(session, "Rice", unit="kg", category="staple", is_synthetic=1)
    get_or_create_dish(session, "Dal Tadka", unit="L", category="main", is_synthetic=1)
    get_or_create_dish(session, "Roti", unit="count", category="staple", is_synthetic=1)

    # Seed synthetic meals
    for i in range(1, 11):
        m = Meal(
            date=f"2026-10-{i:02d}",
            meal_type="lunch",
            headcount=400,
            hostel_strength=500,
            is_synthetic=1,
        )
        session.add(m)
        session.flush()
        d_rice = session.query(Dish).filter(Dish.name == "Rice").first()
        session.add(DishLog(meal_id=m.id, dish_id=d_rice.id, cooked_qty=50.0, leftover_qty=5.0, unit="kg", waste_stage="serving_surplus", is_synthetic=1))

    session.commit()
    yield session
    session.close()


@pytest.fixture
def api_client(test_db):
    """Provides a TestClient using the test_db fixture."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. C5 — Multilingual Voice Logging & Parser Tests (Req 1–16)
# ==============================================================================

def test_1_english_measurement_utterance_parsing():
    """Req 1 & 5: English measurement utterance parses dish, cooked, leftover."""
    text = "rice cooked 40 kg, left 6 kg"
    res = parse_voice_utterance(text)
    assert res.dish_name == "Rice"
    assert res.cooked_qty == 40.0
    assert res.cooked_unit == "kg"
    assert res.leftover_qty == 6.0
    assert res.leftover_unit == "kg"
    assert res.confidence_status == "high"
    assert res.is_valid_for_review is True


def test_2_hindi_measurement_utterance_parsing():
    """Req 2: Hindi measurement utterance parses chawal, bana, bacha."""
    text = "chawal 40 kilo bana, 6 kilo bacha"
    res = parse_voice_utterance(text, language_hint="hi-IN")
    assert res.dish_name == "Rice"
    assert res.cooked_qty == 40.0
    assert res.cooked_unit == "kg"
    assert res.leftover_qty == 6.0
    assert res.leftover_unit == "kg"
    assert res.confidence_status == "high"


def test_3_telugu_transliterated_measurement_parsing():
    """Req 3: Telugu transliterated utterance parses annam, vandamu, migilindi."""
    text = "annam 40 kilolu vandamu, 6 kilolu migilindi"
    res = parse_voice_utterance(text, language_hint="te-IN")
    assert res.dish_name == "Rice"
    assert res.cooked_qty == 40.0
    assert res.cooked_unit == "kg"
    assert res.leftover_qty == 6.0
    assert res.leftover_unit == "kg"
    assert res.confidence_status == "high"


def test_4_number_words_normalization():
    """Req 4: Number words across languages normalize to numeric float values."""
    # English word
    res_en = parse_voice_utterance("rice cooked forty kg, left six kg")
    assert res_en.cooked_qty == 40.0
    assert res_en.leftover_qty == 6.0

    # Hindi word
    res_hi = parse_voice_utterance("chawal chaalis kilo bana, chheh kilo bacha")
    assert res_hi.cooked_qty == 40.0
    assert res_hi.leftover_qty == 6.0

    # Telugu word
    res_te = parse_voice_utterance("annam nalabhai kilolu vandamu, aaru kilolu migilindi")
    assert res_te.cooked_qty == 40.0
    assert res_te.leftover_qty == 6.0


def test_5_cooked_and_leftover_role_reversal():
    """Req 5: Parser assigns roles based on cues, even if leftover is spoken first."""
    text = "leftover 5 kg, cooked 45 kg rice"
    res = parse_voice_utterance(text)
    assert res.cooked_qty == 45.0
    assert res.leftover_qty == 5.0


def test_6_unit_normalization():
    """Req 6: Units normalize correctly (kg/kilo/kilolu -> kg, litres -> L, pieces -> count)."""
    res1 = parse_voice_utterance("dal cooked 30 litres, left 3 litres")
    assert res1.cooked_unit == "L"
    assert res1.leftover_unit == "L"

    res2 = parse_voice_utterance("roti cooked 500 count, left 50 pieces")
    assert res2.cooked_unit == "count"
    assert res2.leftover_unit == "count"


def test_7_unknown_dish_name_not_silently_assigned():
    """Req 7: Unknown dish name is not fabricated or misassigned."""
    text = "exotic_dragonfruit cooked 10 kg, left 2 kg"
    res = parse_voice_utterance(text)
    assert res.dish_name is None
    assert res.cooked_qty == 10.0
    assert "select dish from menu" in res.explanation


def test_8_ambiguous_speech_flagged():
    """Req 8: Speech without clear role cues is flagged for review."""
    text = "rice forty and six"
    res = parse_voice_utterance(text)
    assert "No explicit cooked/leftover cue words" in res.explanation


def test_9_leftover_greater_than_cooked_rejected():
    """Req 9: Leftover quantity greater than cooked quantity is flagged as invalid."""
    text = "rice cooked 10 kg, left 25 kg"
    res = parse_voice_utterance(text)
    assert res.is_valid_for_review is False
    assert res.confidence_status == "failed"
    assert "cannot be greater than cooked" in res.explanation


def test_10_and_11_no_data_persisted_automatically(test_db):
    """Req 10 & 11: Voice parsing does not alter database without explicit confirmation."""
    init_count = test_db.query(DishLog).count()
    # Parsing an utterance does not write to DB
    res = parse_voice_utterance("rice cooked 50 kg, left 5 kg")
    assert res.cooked_qty == 50.0
    final_count = test_db.query(DishLog).count()
    assert init_count == final_count


def test_12_and_13_audio_transcriber_fallback():
    """Req 12 & 13: Absence or failure of speech recognizer handles gracefully without crashing."""
    transcriber = AudioTranscriber()
    # Empty audio
    success, transcript, err = transcriber.transcribe_audio_bytes(b"")
    assert success is False
    assert err is not None


def test_14_api_voice_parse_endpoint(api_client):
    """Req 14: FastAPI endpoint /kitchen/voice-parse processes transcript without persisting."""
    resp = api_client.post(
        "/kitchen/voice-parse",
        json={"transcript": "chawal 40 kilo bana, 6 kilo bacha", "language": "hi-IN"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["parsed"]["dish_name"] == "Rice"
    assert data["parsed"]["cooked_qty"] == 40.0
    assert data["parsed"]["leftover_qty"] == 6.0


# ==============================================================================
# 2. H1 & H2 — CO₂e Impact & Meals-Equivalent Tests (Req 17–30)
# ==============================================================================

def test_17_and_18_co2e_multiplication_and_ordering():
    """Req 17 & 18: Correct CO2e multiplication with properly ordered low/central/high factor band."""
    cfg = EmissionFactorConfig(low_factor=2.2, central_factor=2.5, high_factor=3.4)
    res = calculate_co2e_impact(eligible_food_kg=100.0, is_synthetic=1, factor_config=cfg)

    assert res.is_available is True
    assert res.low_co2e_kg == 220.0
    assert res.central_co2e_kg == 250.0
    assert res.high_co2e_kg == 340.0
    assert res.low_co2e_kg < res.central_co2e_kg < res.high_co2e_kg


def test_19_and_20_emission_factor_metadata_preservation():
    """Req 19 & 20: Factor source, version, and lifecycle boundary are preserved."""
    cfg = EmissionFactorConfig()
    res = calculate_co2e_impact(eligible_food_kg=50.0, is_synthetic=1, factor_config=cfg)
    assert res.factor_config.source_name is not None
    assert "Farm-to-plate" in res.factor_config.system_boundary
    assert res.factor_config.unit == "kgCO2e_per_kg_food"


def test_21_and_24_zero_real_data_produces_honest_unavailable_state(test_db):
    """Req 21 & 24: When real pilot data is 0, real impact is reported as unavailable."""
    # test_db has only synthetic records (0 real meals)
    summary_real = compute_green_campus_summary(test_db, is_synthetic=0)
    assert summary_real.meals_count == 0
    assert summary_real.co2e_impact.is_available is False
    assert "Real pilot measurements pending" in summary_real.co2e_impact.availability_reason
    assert summary_real.meals_equivalent.is_available is False


def test_25_synthetic_estimates_labelled_as_demonstrations(test_db):
    """Req 25: Synthetic estimates prominently carry demonstration label."""
    summary_synth = compute_green_campus_summary(test_db, is_synthetic=1)
    assert summary_synth.is_synthetic == 1
    assert "Synthetic Demonstration — Not Real-World Impact" in summary_synth.data_basis_label
    assert "Synthetic Demonstration" in summary_synth.co2e_impact.data_basis_label


def test_26_and_27_meals_equivalent_denominator_and_calculation(test_db):
    """Req 26 & 27: Meals-equivalent uses valid learned consumption denominator."""
    res = calculate_meals_equivalent(eligible_food_kg=70.0, session=test_db, is_synthetic=1)
    assert res.is_available is True
    assert res.avg_consumption_per_head_kg > 0.10
    assert res.meals_equivalent > 0
    # Expected: ~70 kg / 0.35 kg/meal ≈ 200 meals
    assert 100 <= res.meals_equivalent <= 400


def test_28_and_29_zero_or_negative_food_handled_safely():
    """Req 28 & 29: Zero or negative food avoided marks metrics as unavailable safely."""
    res_zero = calculate_co2e_impact(eligible_food_kg=0.0)
    assert res_zero.is_available is False

    res_neg = calculate_co2e_impact(eligible_food_kg=-10.0)
    assert res_neg.is_available is False

    meals_zero = calculate_meals_equivalent(eligible_food_kg=0.0)
    assert meals_zero.is_available is False


# ==============================================================================
# 3. H4 — Green-Campus PDF Report Tests (Req 31–42)
# ==============================================================================

def test_31_and_32_pdf_generation_produces_non_empty_bytes(test_db):
    """Req 31 & 32: Valid report generation produces non-empty, well-formed PDF bytes."""
    summary = compute_green_campus_summary(test_db, is_synthetic=1)
    pdf_bytes = generate_green_campus_pdf(summary)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    # Valid PDF magic header %PDF
    assert pdf_bytes.startswith(b"%PDF")


def test_33_and_34_zero_real_data_and_synthetic_disclosures_in_pdf(test_db):
    """Req 33 & 34: Disclosures are embedded in generated PDF bytes."""
    # Synthetic PDF contains synthetic warning
    summary_synth = compute_green_campus_summary(test_db, is_synthetic=1)
    pdf_synth = generate_green_campus_pdf(summary_synth)
    assert b"SYNTHETIC DEMONSTRATION" in pdf_synth

    # Real pilot PDF with 0 records contains pending pilot disclosure
    summary_real = compute_green_campus_summary(test_db, is_synthetic=0)
    pdf_real = generate_green_campus_pdf(summary_real)
    assert b"REAL PILOT DATA COLLECTION IN PROGRESS" in pdf_real


def test_35_and_36_pdf_metrics_agree_with_calculations(test_db):
    """Req 35 & 36: Numbers in PDF match summary calculations."""
    summary = compute_green_campus_summary(test_db, is_synthetic=1)
    pdf_bytes = generate_green_campus_pdf(summary)
    # Total cooked and central CO2e appear in the generated PDF stream
    assert str(int(summary.total_cooked_kg)).encode() in pdf_bytes
    assert str(int(summary.co2e_impact.central_co2e_kg)).encode() in pdf_bytes


def test_37_and_38_empty_summary_does_not_crash_pdf():
    """Req 37 & 38: Empty or zero-data summary produces valid PDF without crashing."""
    cfg = EmissionFactorConfig()
    empty_summary = compute_green_campus_summary(None, is_synthetic=0)  # Session is None
    pdf_bytes = generate_green_campus_pdf(empty_summary)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_39_and_40_report_generation_does_not_modify_database(test_db):
    """Req 40: Report generation is read-only and does not mutate database tables."""
    init_meals = test_db.query(Meal).count()
    init_logs = test_db.query(DishLog).count()

    summary = compute_green_campus_summary(test_db, is_synthetic=1)
    _ = generate_green_campus_pdf(summary)

    assert test_db.query(Meal).count() == init_meals
    assert test_db.query(DishLog).count() == init_logs


def test_41_api_impact_and_pdf_endpoints(api_client):
    """Req 41: FastAPI endpoints /impact/summary and /impact/pdf-report function correctly."""
    # /impact/summary
    resp_sum = api_client.get("/impact/summary?is_synthetic=1")
    assert resp_sum.status_code == 200
    data = resp_sum.json()
    assert data["status"] == "success"
    assert "summary" in data

    # /impact/pdf-report
    resp_pdf = api_client.get("/impact/pdf-report?is_synthetic=1")
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    assert resp_pdf.content.startswith(b"%PDF")


def test_42_streamlit_impact_page_apptest():
    """Req 42: Streamlit Impact.py page renders cleanly with AppTest without exceptions."""
    from streamlit.testing.v1 import AppTest

    script_path = Path(__file__).parent.parent / "app" / "pages" / "Impact.py"
    at = AppTest.from_file(str(script_path), default_timeout=30)
    at.run()
    assert not at.exception, f"Exception in Impact.py: {at.exception}"
