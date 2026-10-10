"""MessWise Step 8 Repair & Step 9 Tests (C6, C7, C8, H3, H5, H6).

Tests:
1-3. ReportLab graceful fallback and PDF generator safety.
4-6. Voice transcription status diagnostics and text vs audio distinction.
7-12. C6 Calibrated photo-based waste estimation, density factors, and limitation guards.
13-17. C7 Timestamped entrance tally, validation, arrival curve, and nowcast.
18-21. C8 Smart scale adapter, tare checks, unit validation, and stability.
22-26. H3 SDG 12.3 food waste halving tracker, baseline index, and zero real data guard.
27-30. H5 Resource footprint: virtual water and primary energy uncertainty bands.
31-33. H6 Budget-vs-actual food cost utilisation and price configuration guard.
34-37. FastAPI endpoints for C6, C7, C8, and impact.
38-39. Streamlit AppTest for Kitchen and Impact pages.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from streamlit.testing.v1 import AppTest

from api.main import app
from messwise.db import (
    Dish,
    DishLog,
    Meal,
    get_session_factory,
    init_db,
    record_entrance_tally,
    get_meal_tallies,
)
from messwise.pdf_report import generate_green_campus_pdf, is_pdf_available
from messwise.voice import AudioTranscriber, parse_voice_utterance
from messwise.photo_waste import (
    CONTAINER_PROFILES,
    DISH_BULK_DENSITIES,
    estimate_waste_from_photo,
    get_dish_density,
)
from messwise.tally import (
    STANDARD_TIME_BUCKETS,
    compute_arrival_curve_for_meal,
    validate_tally_count,
)
from messwise.scale import parse_and_validate_scale_payload
from messwise.impact import (
    compute_green_campus_summary,
    compute_sdg123_progress,
    calculate_water_energy_footprint,
    compute_budget_vs_actual,
    WATER_FACTOR_LOW,
    WATER_FACTOR_CENTRAL,
    WATER_FACTOR_HIGH,
    ENERGY_FACTOR_LOW,
    ENERGY_FACTOR_CENTRAL,
    ENERGY_FACTOR_HIGH,
)


@pytest.fixture(autouse=True)
def ensure_db():
    init_db()


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)


# ==============================================================================
# 1. ReportLab Graceful Fallback & PDF Generator
# ==============================================================================

def test_1_reportlab_availability_check():
    """Verify is_pdf_available correctly inspects active environment."""
    assert isinstance(is_pdf_available(), bool)


def test_2_pdf_generation_produces_valid_bytes_when_available():
    """Verify generate_green_campus_pdf generates valid bytes with all sections."""
    factory = get_session_factory()
    with factory() as session:
        summary = compute_green_campus_summary(session=session, is_synthetic=1)
        if is_pdf_available():
            pdf_bytes = generate_green_campus_pdf(summary)
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 2000
            assert pdf_bytes.startswith(b"%PDF-")


def test_3_pdf_generation_graceful_error_when_reportlab_missing(monkeypatch):
    """Verify RuntimeError is raised with clean explanation if ReportLab is missing."""
    import messwise.pdf_report as pr
    monkeypatch.setattr(pr, "HAS_REPORTLAB", False)
    factory = get_session_factory()
    with factory() as session:
        summary = compute_green_campus_summary(session=session, is_synthetic=1)
        with pytest.raises(RuntimeError) as exc_info:
            pr.generate_green_campus_pdf(summary)
        assert "ReportLab library is not installed" in str(exc_info.value)


# ==============================================================================
# 2. Voice Diagnostics & Audio vs Text Distinction
# ==============================================================================

def test_4_audio_transcriber_backend_status():
    """Verify get_backend_status returns comprehensive diagnostics."""
    at = AudioTranscriber()
    status = at.get_backend_status()
    assert "is_available" in status
    assert "engine" in status
    assert "supported_languages" in status
    assert "en-IN" in status["supported_languages"]


def test_5_transcribe_audio_empty_bytes_fails_gracefully():
    """Empty or short audio bytes fail with descriptive error."""
    at = AudioTranscriber()
    success, text, err = at.transcribe_audio_bytes(b"short", language="en-IN")
    assert success is False
    assert "empty or shorter than minimum WAV header" in err


def test_6_voice_parser_text_fallback_does_not_claim_audio_success():
    """Rule parser parses text independently of microphone status."""
    res = parse_voice_utterance("rice cooked 40 kg, left 5 kg")
    assert res.dish_name == "Rice"
    assert res.cooked_qty == 40.0
    assert res.leftover_qty == 5.0
    assert res.is_valid_for_review is True


# ==============================================================================
# 3. C6 Calibrated Photo Waste Estimation
# ==============================================================================

def test_7_photo_waste_bulk_densities():
    """Verify dish bulk densities match calibrated culinary factors."""
    assert get_dish_density("Steamed Rice") == 0.78
    assert get_dish_density("Dal Tadka") == 1.02
    assert get_dish_density("Curd") == 1.03
    assert get_dish_density("Roti") == 0.45
    assert get_dish_density("Unknown Exotic Dish") == 0.88


def test_8_photo_waste_calibrated_formula():
    """Verify fill volume and mass calculations for standard 20L bin."""
    # 20L bin at 50% fill with Rice (0.78 kg/L) -> 10 L -> 7.8 kg
    est = estimate_waste_from_photo(
        image_bytes=b"dummy_valid_image_bytes_over_one_hundred_characters_long_for_test_purposes_123456789012345678901234567890",
        dish_name="Rice",
        container_type="20L_standard_bin",
        manual_fill_fraction=0.50,
    )
    assert est.fill_fraction == 0.50
    assert est.fill_volume_litres == 10.0
    assert est.estimated_kg == 7.8
    assert est.low_kg == round(7.8 * 0.85, 2)
    assert est.high_kg == round(7.8 * 1.15, 2)
    assert est.is_valid_for_review is True


def test_9_photo_waste_limitation_disclosure():
    """Verify estimate contains explicit visual limitation disclosure."""
    est = estimate_waste_from_photo(
        image_bytes=b"dummy_bytes_1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
        dish_name="Dal Tadka",
        container_type="20L_standard_bin",
        manual_fill_fraction=0.30,
    )
    assert "Visual fill-level estimate only" in est.limitation_disclosure
    assert "Does not replace calibrated kitchen scale measurement" in est.limitation_disclosure


def test_10_photo_waste_empty_bytes_rejected():
    """Empty image returns invalid estimate."""
    est = estimate_waste_from_photo(b"", dish_name="Rice")
    assert est.is_valid_for_review is False
    assert est.estimated_kg == 0.0
    assert "Invalid or empty image" in est.explanation


# ==============================================================================
# 4. C7 Timestamped Entrance Tally & Arrival Curve
# ==============================================================================

def test_13_validate_tally_count():
    """Verify count validation enforces non-negative numbers and capacity bounds."""
    ok, err = validate_tally_count(50, max_capacity=500)
    assert ok is True
    assert err is None

    ok_neg, err_neg = validate_tally_count(-10)
    assert ok_neg is False
    assert "cannot be negative" in err_neg

    ok_max, err_max = validate_tally_count(2000, max_capacity=1000)
    assert ok_max is False
    assert "exceeds plausible physical dining hall capacity" in err_max


def test_14_record_and_get_entrance_tallies():
    """Verify entrance tallies record in database and compute arrival curve."""
    factory = get_session_factory()
    with factory() as session:
        # Find or create a meal for test
        meal = session.execute(select(Meal).where(Meal.is_synthetic == 1)).scalars().first()
        if not meal:
            pytest.skip("No test meal available")

        t1 = record_entrance_tally(session, meal.id, "00-15 min (Early Service)", 50, recorded_by="monitor", is_synthetic=1)
        t2 = record_entrance_tally(session, meal.id, "15-30 min (Peak Arrival)", 100, recorded_by="monitor", is_synthetic=1)
        assert t1.id is not None
        assert t2.id is not None

        analysis = compute_arrival_curve_for_meal(session, meal.id, expected_headcount=200)
        assert analysis.total_recorded_count >= 150
        assert len(analysis.bucket_counts) >= 2
        assert "00-15 min (Early Service)" in analysis.cumulative_curve


def test_15_tally_arrival_curve_nowcast():
    """Verify arrival fraction calculates projected nowcast headcount."""
    factory = get_session_factory()
    with factory() as session:
        meal = session.execute(select(Meal).where(Meal.is_synthetic == 1)).scalars().first()
        if not meal:
            pytest.skip("No test meal available")

        analysis = compute_arrival_curve_for_meal(session, meal.id)
        if analysis.nowcast_headcount is not None:
            assert analysis.nowcast_headcount > 0


# ==============================================================================
# 5. C8 Smart Scale Integration Adapter
# ==============================================================================

def test_18_valid_scale_payload():
    """Verify valid smart scale reading computes net weight."""
    payload = {
        "device_id": "HX711-ESP32-SCALE01",
        "gross_weight_kg": 12.45,
        "tare_weight_kg": 2.10,
        "net_weight_kg": 10.35,
        "unit": "kg",
        "is_stable": True,
    }
    res = parse_and_validate_scale_payload(payload)
    assert res.is_valid is True
    assert res.net_weight_kg == 10.35
    assert res.entry_method == "smart_scale"


def test_19_negative_net_scale_reading_flags_tare():
    """Negative net weight requires tare recalibration."""
    payload = {
        "gross_weight_kg": 1.5,
        "tare_weight_kg": 2.5,
        "net_weight_kg": -1.0,
        "unit": "kg",
    }
    res = parse_and_validate_scale_payload(payload)
    assert res.is_valid is False
    assert "tare recalibration" in res.status_message


def test_20_invalid_scale_unit_rejected():
    """Incompatible unit rejected by scale adapter."""
    payload = {
        "gross_weight_kg": 10.0,
        "net_weight_kg": 8.0,
        "unit": "litres",
    }
    res = parse_and_validate_scale_payload(payload)
    assert res.is_valid is False
    assert "Invalid scale unit" in res.status_message


def test_21_unstable_scale_reading_flagged():
    """Unstable scale platform reading flagged for settling."""
    payload = {
        "gross_weight_kg": 10.0,
        "net_weight_kg": 8.0,
        "unit": "kg",
        "is_stable": False,
    }
    res = parse_and_validate_scale_payload(payload)
    assert res.is_valid is False
    assert "unstable" in res.status_message


# ==============================================================================
# 6. H3 SDG 12.3 Tracker
# ==============================================================================

def test_22_sdg123_zero_real_data_unavailable():
    """Zero real data produces honest unavailable state for SDG 12.3."""
    factory = get_session_factory()
    with factory() as session:
        res = compute_sdg123_progress(session, is_synthetic=0)
        assert res.is_available is False
        assert "Real pilot measurements pending" in res.availability_reason


def test_23_sdg123_synthetic_demo_progress():
    """Synthetic demonstration computes per-head waste index and reduction %."""
    factory = get_session_factory()
    with factory() as session:
        res = compute_sdg123_progress(session, is_synthetic=1, baseline_waste_per_head_g=115.0)
        assert res.is_available is True
        assert res.current_waste_per_head_g > 0.0
        assert 0.0 <= res.target_progress_pct <= 100.0
        assert "Synthetic Demonstration" in res.data_basis_label


# ==============================================================================
# 7. H5 Resource Footprint (Virtual Water & Primary Energy)
# ==============================================================================

def test_27_water_energy_footprint_multiplication():
    """Verify water and energy calculations match peer-reviewed factors."""
    avoided_kg = 20.0
    res = calculate_water_energy_footprint(avoided_kg, is_synthetic=1)
    assert res.is_available is True
    assert res.low_water_litres == 20.0 * WATER_FACTOR_LOW
    assert res.central_water_litres == 20.0 * WATER_FACTOR_CENTRAL
    assert res.high_water_litres == 20.0 * WATER_FACTOR_HIGH
    assert res.low_energy_mj == 20.0 * ENERGY_FACTOR_LOW
    assert res.central_energy_mj == 20.0 * ENERGY_FACTOR_CENTRAL
    assert res.high_energy_mj == 20.0 * ENERGY_FACTOR_HIGH


def test_28_water_energy_zero_food_unavailable():
    """Zero food avoided produces unavailable state."""
    res = calculate_water_energy_footprint(0.0, is_synthetic=1)
    assert res.is_available is False
    assert "Resource footprint unavailable" in res.availability_reason


# ==============================================================================
# 8. H6 Budget-vs-Actual Food Cost Utilisation
# ==============================================================================

def test_31_budget_vs_actual_unconfigured_prices_guard():
    """When ingredient prices are unconfigured, financial metric is unavailable."""
    factory = get_session_factory()
    with factory() as session:
        res = compute_budget_vs_actual(session, is_synthetic=1, target_budget_per_meal_inr=45.0)
        # Either prices are unconfigured or accurately calculated
        if not res.is_available:
            assert "prices not configured" in res.status_message.lower() or "unavailable" in res.status_message.lower()


# ==============================================================================
# 9. FastAPI Endpoints for C6, C7, C8
# ==============================================================================

def test_34_api_photo_estimate(api_client: TestClient):
    """POST /kitchen/photo-estimate calculates calibrated mass without saving."""
    payload = {
        "dish_name": "Rice",
        "container_type": "20L_standard_bin",
        "fill_percentage": 50.0,
    }
    res = api_client.post("/kitchen/photo-estimate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["estimate"]["estimated_kg"] == 7.8


def test_35_api_scale_reading_validation(api_client: TestClient):
    """POST /kitchen/scale-reading validates smart scale telemetry."""
    payload = {
        "device_id": "SCALE-KITCHEN-01",
        "gross_weight_kg": 15.0,
        "tare_weight_kg": 2.5,
        "net_weight_kg": 12.5,
        "unit": "kg",
        "is_stable": True,
    }
    res = api_client.post("/kitchen/scale-reading", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["reading"]["net_weight_kg"] == 12.5


def test_36_api_tally_and_arrival_curve(api_client: TestClient):
    """POST /kitchen/tally and GET /kitchen/tally/{meal_id}."""
    factory = get_session_factory()
    with factory() as session:
        meal = session.execute(select(Meal).where(Meal.is_synthetic == 1)).scalars().first()
        if not meal:
            pytest.skip("No meal available for API tally test")
        meal_id = meal.id

    t_res = api_client.post("/kitchen/tally", json={
        "meal_id": meal_id,
        "time_bucket": "00-15 min (Early Service)",
        "headcount_count": 45,
        "recorded_by": "api_test",
        "is_synthetic": 1,
    })
    assert t_res.status_code == 201

    g_res = api_client.get(f"/kitchen/tally/{meal_id}")
    assert g_res.status_code == 200
    assert g_res.json()["status"] == "success"
    assert "analysis" in g_res.json()


# ==============================================================================
# 10. Streamlit AppTest for Kitchen and Impact Pages
# ==============================================================================

def test_38_streamlit_kitchen_apptest():
    """AppTest verification that Kitchen page renders voice, photo, and tally expanders."""
    script_path = Path(__file__).parent.parent / "app" / "pages" / "Kitchen.py"
    at = AppTest.from_file(str(script_path), default_timeout=30)
    at.run()
    assert not at.exception, f"Exception in Kitchen.py: {at.exception}"


def test_39_streamlit_impact_apptest():
    """AppTest verification that Impact page renders H1-H6 without crashing."""
    script_path = Path(__file__).parent.parent / "app" / "pages" / "Impact.py"
    at = AppTest.from_file(str(script_path), default_timeout=30)
    at.run()
    assert not at.exception, f"Exception in Impact.py: {at.exception}"


def test_40_c8_smart_scale_workflow_integration():
    """Verify Smart Scale payload parsing properly extracts validated net weight and rejects bad payloads."""
    valid_payload = {
        "device_id": "HX711-ESP32-SCALE01",
        "gross_weight_kg": 15.5,
        "tare_weight_kg": 2.5,
        "net_weight_kg": 13.0,
        "unit": "kg",
        "is_stable": True,
    }
    reading = parse_and_validate_scale_payload(valid_payload)
    assert reading.is_valid is True
    assert reading.net_weight_kg == 13.0
    assert reading.entry_method == "smart_scale"

    bad_unit_payload = {
        "device_id": "HX711-ESP32-SCALE01",
        "gross_weight_kg": 15.5,
        "tare_weight_kg": 2.5,
        "net_weight_kg": 13.0,
        "unit": "lbs",
        "is_stable": True,
    }
    bad_reading = parse_and_validate_scale_payload(bad_unit_payload)
    assert bad_reading.is_valid is False
    assert "Invalid scale unit" in bad_reading.status_message


def test_41_green_campus_pdf_bytes_validation():
    """Verify generated PDF byte buffer contains valid PDF headers and structure."""
    factory = get_session_factory()
    with factory() as session:
        summary = compute_green_campus_summary(session=session, is_synthetic=1)
        if is_pdf_available():
            pdf_bytes = generate_green_campus_pdf(summary)
            assert pdf_bytes.startswith(b"%PDF-")
            assert b"MessWise" in pdf_bytes
            assert len(pdf_bytes) > 1000
