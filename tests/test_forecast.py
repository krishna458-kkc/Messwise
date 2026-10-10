"""Comprehensive test suite for MessWise Demand Forecasting Engine & Prediction Log.

Tests all required criteria per PLAN.md Module A + E1:
1. Baseline calculation
2. Same-meal same-weekday baseline (Baseline 1)
3. Trailing weekday x meal baseline (Baseline 2)
4. Participation-rate calculation (A3)
5. Zero hostel strength handling
6. Feature construction (A4)
7. Time-ordered validation (no leakage)
8. Forecast output structure (A1)
9. Uncertainty interval validity (A6)
10. Explanation generation (A5)
11. Synthetic vs real separation
12. Prediction logging (E1)
13. Prediction stored before outcome
14. Later outcome association
15. Forecast error calculation
16. Invalid input rejection
17. API /forecast endpoint
18. Insufficient-data behavior
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app, get_db_session
from messwise.db import (
    Base,
    Meal,
    Prediction,
    create_meal_record,
    init_db,
    link_actual_to_predictions,
)
from messwise.forecast import (
    HeadcountForecaster,
    compute_baseline_last_week,
    compute_baseline_trailing_avg,
    extract_features,
    fetch_historical_meals,
    forecast_upcoming_meals,
    get_prediction_log_history,
    get_trained_forecaster,
    log_forecast_prediction,
)
from messwise.validation import MealCreate


@pytest.fixture
def forecast_db():
    """Provides an isolated in-memory SQLite database populated with multi-week meals."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create 14 days of historical meals (starts 2026-10-01)
    base_date = datetime.strptime("2026-10-01", "%Y-%m-%d").date()
    for day in range(14):
        curr_d = (base_date + timedelta(days=day)).strftime("%Y-%m-%d")
        for m_type in ["breakfast", "lunch", "snacks", "dinner"]:
            rates = {"breakfast": 0.65, "lunch": 0.80, "snacks": 0.50, "dinner": 0.85}
            hc = int(round(rates[m_type] * 500))
            m = Meal(
                date=curr_d,
                meal_type=m_type,
                headcount=hc,
                hostel_strength=500,
                event_flag=1 if day == 5 else 0,
                exam_flag=1 if 6 <= day <= 8 else 0,
                holiday_flag=1 if day in (3, 10) else 0,
                temp_c=28.0,
                rain_mm=10.0 if day == 4 else 0.0,
                source="manual",
                is_synthetic=0,
            )
            session.add(m)
    session.commit()
    yield session
    session.close()


def test_participation_rate_calculation(forecast_db):
    """Test 4: Verify participation rate = headcount / hostel_strength."""
    df = fetch_historical_meals(forecast_db, is_synthetic=0)
    assert not df.empty
    sample_row = df.iloc[0]
    expected_rate = sample_row["headcount"] / sample_row["hostel_strength"]
    assert sample_row["participation_rate"] == pytest.approx(expected_rate, rel=1e-4)


def test_zero_hostel_strength_handling(forecast_db):
    """Test 5: Handle zero or missing hostel strength safely without crashing."""
    # Insert meal with zero strength
    bad_meal = Meal(
        date="2026-10-20",
        meal_type="lunch",
        headcount=400,
        hostel_strength=0,
        is_synthetic=0,
    )
    forecast_db.add(bad_meal)
    forecast_db.commit()

    df = fetch_historical_meals(forecast_db, is_synthetic=0)
    assert not df.empty
    zero_row = df[df["date"] == "2026-10-20"].iloc[0]
    # Should safely fallback to default strength
    assert zero_row["hostel_strength"] > 0

    forecaster = HeadcountForecaster()
    forecaster.fit(df)
    res = forecaster.predict_slot(df, "2026-10-21", "lunch", hostel_strength=0)
    assert res.h_hat > 0
    assert res.hostel_strength > 0


def test_baseline_same_meal_last_week(forecast_db):
    """Test 1 & 2: Baseline 1 (same meal, same weekday last week)."""
    df = fetch_historical_meals(forecast_db, is_synthetic=0)
    # Target date: 2026-10-10. Lag 7 date: 2026-10-03.
    b1 = compute_baseline_last_week(df, "2026-10-10", "lunch")
    assert b1 is not None

    expected_record = df[(df["date"] == "2026-10-03") & (df["meal_type"] == "lunch")].iloc[0]
    assert b1 == expected_record["headcount"]

    # Target date with no lag-7 history
    b1_missing = compute_baseline_last_week(df, "2026-10-02", "lunch")
    assert b1_missing is None


def test_baseline_trailing_avg(forecast_db):
    """Test 3: Baseline 2 (trailing weekday x meal average)."""
    df = fetch_historical_meals(forecast_db, is_synthetic=0)
    # Target: 2026-10-15 (Thursday, same as 2026-10-01 and 2026-10-08)
    b2 = compute_baseline_trailing_avg(df, "2026-10-15", "lunch", current_strength=500)
    assert b2 is not None
    assert 350 <= b2 <= 450


def test_feature_construction():
    """Test 6: Feature construction vector length and normalization."""
    row = pd.Series({
        "meal_type": "lunch",
        "weekday": 2,  # Wednesday
        "event_flag": 1,
        "exam_flag": 0,
        "holiday_flag": 0,
        "temp_c": 30.0,
        "rain_mm": 15.0,
    })
    vec = extract_features(row)
    assert len(vec) == 16
    assert vec[1] == 1.0   # lunch
    assert vec[6] == 1.0   # wednesday (4 + 2)
    assert vec[11] == 1.0  # event
    assert vec[14] == pytest.approx((30.0 - 25.0) / 10.0)
    assert vec[15] == pytest.approx(15.0 / 20.0)


def test_time_ordered_validation(forecast_db):
    """Test 7: Expanding-origin validation without look-ahead leakage."""
    df = fetch_historical_meals(forecast_db, is_synthetic=0)
    forecaster = HeadcountForecaster()
    forecaster.fit(df)

    assert "model_mae" in forecaster.validation_metrics
    assert "model_wape" in forecaster.validation_metrics
    assert forecaster.validation_metrics["evaluation_samples"] > 0
    assert forecaster.validation_metrics["model_mae"] >= 0.0


def test_forecast_output_structure_and_uncertainty(forecast_db):
    """Test 8 & 9: Forecast output structure and 80% uncertainty interval validity."""
    forecaster, df = get_trained_forecaster(forecast_db, is_synthetic=0)
    res = forecaster.predict_slot(df, "2026-10-15", "dinner", hostel_strength=500)

    # Output structure
    assert res.target_date == "2026-10-15"
    assert res.meal_type == "dinner"
    assert res.h_hat > 0
    assert res.hostel_strength == 500

    # Uncertainty interval validity (h_lo <= h_hat <= h_hi)
    assert res.h_lo <= res.h_hat <= res.h_hi
    assert res.h_lo >= 0
    assert res.h_hi <= 500


def test_explanation_and_drivers(forecast_db):
    """Test 10: Explanation text generation and drivers."""
    forecaster, df = get_trained_forecaster(forecast_db, is_synthetic=0)
    res = forecaster.predict_slot(
        df,
        "2026-10-15",
        "lunch",
        hostel_strength=500,
        context_flags={"event_flag": 1},
        weather={"temp_c": 28.0, "rain_mm": 25.0},
    )
    assert res.explanation != ""
    assert isinstance(res.explanation, str)
    assert "lunch" in res.explanation.lower() or "predicted" in res.explanation.lower()
    assert isinstance(res.top_drivers, list)


def test_synthetic_vs_real_separation(forecast_db):
    """Test 11: Real and synthetic forecasters train on distinct datasets."""
    # Add synthetic meals with very different headcount pattern
    for i in range(10):
        synth_m = Meal(
            date=f"2026-10-{i+1:02d}",
            meal_type="lunch",
            headcount=100,  # deliberately low
            hostel_strength=500,
            is_synthetic=1,
        )
        forecast_db.add(synth_m)
    forecast_db.commit()

    f_real, df_real = get_trained_forecaster(forecast_db, is_synthetic=0)
    f_synth, df_synth = get_trained_forecaster(forecast_db, is_synthetic=1)

    assert len(df_real) == 56  # 14 days * 4 meals
    assert len(df_synth) == 10

    res_real = f_real.predict_slot(df_real, "2026-10-15", "lunch", hostel_strength=500)
    res_synth = f_synth.predict_slot(df_synth, "2026-10-15", "lunch", hostel_strength=500)

    # Real and synthetic predictions must reflect their respective populations
    assert res_real.h_hat > res_synth.h_hat


def test_prediction_logging_before_outcome(forecast_db):
    """Test 12 & 13: Live forecast frozen in Prediction table before outcome."""
    forecaster, df = get_trained_forecaster(forecast_db, is_synthetic=0)
    f_res = forecaster.predict_slot(df, "2026-10-20", "lunch", hostel_strength=500)

    pred = log_forecast_prediction(forecast_db, f_res)
    forecast_db.commit()

    assert pred.id is not None
    assert pred.status == "pending"
    assert pred.actual_headcount is None
    assert pred.forecast_error is None
    assert pred.h_hat == float(f_res.h_hat)


def test_outcome_association_and_error_calculation(forecast_db):
    """Test 14 & 15: Associate actual logged meal with prior prediction and compute error."""
    # 1. Log a prediction in advance
    forecaster, df = get_trained_forecaster(forecast_db, is_synthetic=0)
    f_res = forecaster.predict_slot(df, "2026-10-25", "dinner", hostel_strength=500)
    pred = log_forecast_prediction(forecast_db, f_res)
    forecast_db.commit()

    assert pred.status == "pending"
    predicted_val = pred.h_hat

    # 2. Kitchen logs actual meal on that date
    meal_data = MealCreate(
        date="2026-10-25",
        meal_type="dinner",
        headcount=430,
        hostel_strength=500,
        is_synthetic=0,
    )
    meal = create_meal_record(forecast_db, meal_data)
    forecast_db.commit()

    # 3. Verify prediction was updated with actual outcome and error
    forecast_db.refresh(pred)
    assert pred.status == "evaluated"
    assert pred.actual_headcount == 430
    assert pred.forecast_error == pytest.approx(430.0 - predicted_val)
    assert pred.abs_error == pytest.approx(abs(430.0 - predicted_val))


def test_insufficient_data_behavior():
    """Test 18: Forecaster gracefully handles empty/cold-start history."""
    empty_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(empty_engine)
    Session = sessionmaker(bind=empty_engine)
    session = Session()

    forecaster, df_empty = get_trained_forecaster(session, is_synthetic=0)
    assert df_empty.empty
    assert forecaster.model is None

    res = forecaster.predict_slot(df_empty, "2026-10-01", "lunch", hostel_strength=500)
    assert res.low_confidence_flag is True
    assert res.confidence_status == "low"
    assert res.h_hat > 0
    assert res.h_lo <= res.h_hat <= res.h_hi
    session.close()


def test_api_forecast_and_invalid_input(forecast_db):
    """Test 16 & 17: FastAPI /forecast endpoint, parameter parsing, and invalid input rejection."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=forecast_db.get_bind())

    def override_get_db_session():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as client:
        # Valid request
        resp = client.get("/forecast?date=2026-10-16&meal_type=lunch&days=1&hostel_strength=500")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["forecasts"]) == 1
        f0 = data["forecasts"][0]
        assert f0["meal_type"] == "lunch"
        assert f0["h_hat"] > 0
        assert f0["h_lo"] <= f0["h_hat"] <= f0["h_hi"]

        # Prediction log endpoint
        resp_log = client.get("/prediction-log")
        assert resp_log.status_code == 200
        assert "prediction_log" in resp_log.json()

        # Invalid meal type rejection (Test 16)
        resp_bad_meal = client.get("/forecast?date=2026-10-16&meal_type=midnight_snack")
        assert resp_bad_meal.status_code == 400

        # Invalid date rejection (Test 16)
        resp_bad_date = client.get("/forecast?date=not-a-date")
        assert resp_bad_date.status_code == 400

    app.dependency_overrides.clear()
