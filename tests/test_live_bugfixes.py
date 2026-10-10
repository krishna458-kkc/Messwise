"""Tests for Live-Test Bug Fix Sprint: Waste Intelligence, API Startup & Data Provenance.

Verifies:
1. compute_kpi_summary() calculates MAE and WAPE correctly when predictions and actual outcomes exist.
2. compute_kpi_summary() gracefully handles predictions missing actual_headcount or empty prediction sets without AttributeError.
3. get_data_environment_summary() strictly segregates unverified manual test entries from verified pilot measurements.
4. Unverified test entries (verification_status='unverified_test') cannot produce false pilot evidence or verified carbon savings claims.
5. AppTest verification that Waste_Intelligence renders cleanly with non-synthetic test records.
"""

from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from streamlit.testing.v1 import AppTest

from messwise.db import (
    Base,
    Dish,
    DishLog,
    Meal,
    Prediction,
    get_data_environment_summary,
    init_db,
)
from messwise.impact import compute_green_campus_summary
from messwise.intelligence import compute_kpi_summary
from messwise.reports import compute_pilot_evidence_report

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def memory_session():
    """In-memory SQLite session with full MessWise schema."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    d = Dish(id=1, name="Dal Tadka", category="main", unit="kg", standard_portion=0.15, mess_id="default_mess")
    session.add(d)
    session.commit()

    yield session
    session.close()


def test_compute_kpi_summary_predictions_with_actuals(memory_session):
    """Test compute_kpi_summary when evaluated predictions exist in the database."""
    # Meal
    m = Meal(id=1, date="2026-10-05", meal_type="lunch", headcount=420, hostel_strength=500, is_synthetic=1)
    memory_session.add(m)

    # Dish log
    dl = DishLog(meal_id=1, dish_id=1, cooked_qty=60.0, leftover_qty=5.0, unit="kg", is_synthetic=1)
    memory_session.add(dl)

    # Prediction evaluated with actual_headcount = 420, forecast h_hat = 400 (error = 20)
    p = Prediction(
        meal_date="2026-10-05",
        meal_type="lunch",
        h_hat=400.0,
        h_lo=380.0,
        h_hi=420.0,
        actual_headcount=420,
        abs_error=20.0,
        status="evaluated",
        is_synthetic=1,
    )
    memory_session.add(p)
    memory_session.commit()

    kpi = compute_kpi_summary(session=memory_session, is_synthetic=1)
    assert kpi.forecast_eval_count == 1
    assert kpi.forecast_mae == pytest.approx(20.0, 0.01)
    assert kpi.forecast_wape == pytest.approx(round(20.0 / 420.0, 3), 0.001)


def test_compute_kpi_summary_predictions_without_abs_error_attribute(memory_session):
    """Test compute_kpi_summary calculates |actual - h_hat| when abs_error is None."""
    m = Meal(id=2, date="2026-10-06", meal_type="lunch", headcount=430, hostel_strength=500, is_synthetic=1)
    memory_session.add(m)

    p = Prediction(
        meal_date="2026-10-06",
        meal_type="lunch",
        h_hat=450.0,
        h_lo=420.0,
        h_hi=480.0,
        actual_headcount=430,
        abs_error=None,  # No stored abs_error
        status="evaluated",
        is_synthetic=1,
    )
    memory_session.add(p)
    memory_session.commit()

    kpi = compute_kpi_summary(session=memory_session, is_synthetic=1)
    assert kpi.forecast_eval_count == 1
    # |430 - 450| = 20.0
    assert kpi.forecast_mae == pytest.approx(20.0, 0.01)


def test_compute_kpi_summary_predictions_with_missing_actuals(memory_session):
    """Test compute_kpi_summary ignores pending predictions without actual headcount."""
    m = Meal(id=3, date="2026-10-07", meal_type="lunch", headcount=430, hostel_strength=500, is_synthetic=1)
    memory_session.add(m)

    p_pending = Prediction(
        meal_date="2026-10-07",
        meal_type="lunch",
        h_hat=450.0,
        h_lo=420.0,
        h_hi=480.0,
        actual_headcount=None,  # Not yet evaluated
        status="pending",
        is_synthetic=1,
    )
    memory_session.add(p_pending)
    memory_session.commit()

    kpi = compute_kpi_summary(session=memory_session, is_synthetic=1)
    assert kpi.forecast_eval_count == 0
    assert kpi.forecast_mae is None
    assert kpi.forecast_wape is None


def test_data_environment_summary_distinguishes_unverified_test_entries(memory_session):
    """Verify that get_data_environment_summary correctly distinguishes unverified test records."""
    # Add unverified test meal
    m_test = Meal(
        id=29,
        date="2026-10-10",
        meal_type="lunch",
        headcount=420,
        hostel_strength=500,
        source="manual",
        is_synthetic=0,
        verification_status="unverified_test",
    )
    memory_session.add(m_test)
    memory_session.commit()

    env = get_data_environment_summary(memory_session)
    assert env["real_meals_count"] == 1
    assert env["verified_pilot_meals_count"] == 0
    assert env["unverified_test_meals_count"] == 1
    assert env["has_real_data"] is True
    assert env["has_verified_pilot_data"] is False
    assert env["is_verified_pilot"] is False
    assert "Unverified Test Entries" in env["real_env_label"]
    assert "badge-unverified" in env["real_env_badge_class"]


def test_unverified_records_cannot_generate_pilot_savings_or_evidence(memory_session):
    """Verify honesty guards: unverified entries cannot qualify as pilot evidence or verified green campus impact."""
    m_test = Meal(
        id=30,
        date="2026-10-10",
        meal_type="lunch",
        headcount=420,
        hostel_strength=500,
        source="manual",
        is_synthetic=0,
        verification_status="unverified_test",
    )
    memory_session.add(m_test)
    memory_session.commit()

    # E2 Pilot Evidence Report
    e2 = compute_pilot_evidence_report(
        session=memory_session,
        baseline_start="2026-10-01",
        baseline_end="2026-10-04",
        pilot_start="2026-10-05",
        pilot_end="2026-10-10",
        is_synthetic=0,
    )
    assert not e2.has_sufficient_data
    assert "unverified test entries" in e2.status_message.lower()

    # H1-H4 Green Campus Impact
    impact = compute_green_campus_summary(
        session=memory_session,
        is_synthetic=0,
        reporting_period="pilot_period",
    )
    assert impact.meals_count == 0
    assert not impact.co2e_impact.is_available


def test_waste_intelligence_page_runs_cleanly():
    """Verify Waste_Intelligence.py Streamlit page executes without any AttributeError or uncaught exception."""
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Waste_Intelligence.py")
    at.run(timeout=15)
    assert not at.exception, f"Waste Intelligence page crashed: {at.exception}"
