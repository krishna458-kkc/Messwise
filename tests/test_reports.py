"""Tests for MessWise Pilot Evidence & Reports Engine (Module E: E2).

Verifies:
- E2: Matched weekday x meal comparisons between baseline and pilot
- Event-day separation (exams, events, holidays excluded from matched pairs)
- Nonparametric bootstrap 95% confidence intervals with fixed seed 42
- Zero-real-records detection and honesty guard
- No false claims of real-world effectiveness
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from messwise.db import Dish, DishLog, Meal, get_or_create_dish, init_db
from messwise.reports import compute_pilot_evidence_report


@pytest.fixture
def memory_db():
    """Provides isolated in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_e2_zero_real_records_honesty_guard(memory_db):
    """Verify that when 0 real pilot records exist, E2 honestly refuses to fabricate results."""
    report = compute_pilot_evidence_report(
        session=memory_db,
        baseline_start="2026-10-01",
        baseline_end="2026-10-04",
        pilot_start="2026-10-05",
        pilot_end="2026-10-07",
        is_synthetic=0,
    )

    assert report.has_sufficient_data is False
    assert "Insufficient Real Pilot Data" in report.status_message
    assert report.mean_waste_avoided_kg_per_meal is None
    assert report.percentage_waste_reduction is None
    assert report.bootstrap_ci_95_lower_kg is None
    assert report.matched_pairs_count == 0


def test_e2_matched_weekday_meal_comparison(memory_db):
    """Verify matched weekday x meal pairing and waste reduction calculation."""
    d = get_or_create_dish(memory_db, name="Rice", unit="kg", category="staple")

    # Baseline week: Mon 2026-10-05 Lunch (30 kg leftover) and Tue 2026-10-06 Dinner (20 kg leftover)
    m_b1 = Meal(date="2026-10-05", meal_type="lunch", headcount=400, hostel_strength=500, is_synthetic=1)
    m_b2 = Meal(date="2026-10-06", meal_type="dinner", headcount=400, hostel_strength=500, is_synthetic=1)
    memory_db.add_all([m_b1, m_b2])
    memory_db.flush()
    memory_db.add(DishLog(meal_id=m_b1.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=30.0, unit="kg", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_b2.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=20.0, unit="kg", is_synthetic=1))

    # Pilot week: Mon 2026-10-12 Lunch (10 kg leftover) and Tue 2026-10-13 Dinner (10 kg leftover)
    m_p1 = Meal(date="2026-10-12", meal_type="lunch", headcount=400, hostel_strength=500, is_synthetic=1)
    m_p2 = Meal(date="2026-10-13", meal_type="dinner", headcount=400, hostel_strength=500, is_synthetic=1)
    memory_db.add_all([m_p1, m_p2])
    memory_db.flush()
    memory_db.add(DishLog(meal_id=m_p1.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=10.0, unit="kg", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_p2.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=10.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    report = compute_pilot_evidence_report(
        session=memory_db,
        baseline_start="2026-10-05",
        baseline_end="2026-10-07",
        pilot_start="2026-10-12",
        pilot_end="2026-10-14",
        is_synthetic=1,
        random_seed=42,
    )

    assert report.has_sufficient_data is True
    assert report.matched_pairs_count == 2
    # Pair 1: 30 - 10 = +20 kg avoided
    # Pair 2: 20 - 10 = +10 kg avoided
    # Mean avoided = (20 + 10) / 2 = 15.0 kg
    assert report.mean_waste_avoided_kg_per_meal == 15.0
    # Average baseline = 25.0 kg. % reduction = (15 / 25) * 100 = 60.0%
    assert report.percentage_waste_reduction == 60.0
    # Bootstrap CI bounds exist
    assert report.bootstrap_ci_95_lower_kg is not None
    assert report.bootstrap_ci_95_upper_kg is not None
    assert report.bootstrap_ci_95_lower_kg <= report.mean_waste_avoided_kg_per_meal <= report.bootstrap_ci_95_upper_kg


def test_e2_event_days_excluded(memory_db):
    """Verify that event, exam, and holiday meals are separated and excluded from matched pairs."""
    d = get_or_create_dish(memory_db, name="Dal", unit="L", category="main")

    # Baseline Mon (Normal)
    m_b1 = Meal(date="2026-10-05", meal_type="lunch", headcount=400, hostel_strength=500, event_flag=0, is_synthetic=1)
    # Baseline Tue (Event day! e.g. fest)
    m_b2 = Meal(date="2026-10-06", meal_type="lunch", headcount=400, hostel_strength=500, event_flag=1, is_synthetic=1)
    memory_db.add_all([m_b1, m_b2])
    memory_db.flush()
    memory_db.add(DishLog(meal_id=m_b1.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=10.0, unit="L", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_b2.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=30.0, unit="L", is_synthetic=1))

    # Pilot Mon (Normal)
    m_p1 = Meal(date="2026-10-12", meal_type="lunch", headcount=400, hostel_strength=500, event_flag=0, is_synthetic=1)
    # Pilot Tue (Normal)
    m_p2 = Meal(date="2026-10-13", meal_type="lunch", headcount=400, hostel_strength=500, event_flag=0, is_synthetic=1)
    memory_db.add_all([m_p1, m_p2])
    memory_db.flush()
    memory_db.add(DishLog(meal_id=m_p1.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=5.0, unit="L", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_p2.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=5.0, unit="L", is_synthetic=1))
    memory_db.commit()

    report = compute_pilot_evidence_report(
        session=memory_db,
        baseline_start="2026-10-05",
        baseline_end="2026-10-07",
        pilot_start="2026-10-12",
        pilot_end="2026-10-14",
        is_synthetic=1,
    )

    assert report.has_sufficient_data is True
    assert report.event_days_excluded_count >= 1
    # Only Monday was matched because Tuesday baseline was an event day
    assert report.matched_pairs_count == 1
    assert report.matched_pairs[0]["weekday_name"] == "Monday"


def test_e2_bootstrap_reproducibility(memory_db):
    """Verify that bootstrap confidence intervals are 100% reproducible with fixed seed."""
    d = get_or_create_dish(memory_db, name="Rice", unit="kg", category="staple")

    m_b1 = Meal(date="2026-10-05", meal_type="lunch", headcount=400, hostel_strength=500, is_synthetic=1)
    m_b2 = Meal(date="2026-10-06", meal_type="dinner", headcount=400, hostel_strength=500, is_synthetic=1)
    m_p1 = Meal(date="2026-10-12", meal_type="lunch", headcount=400, hostel_strength=500, is_synthetic=1)
    m_p2 = Meal(date="2026-10-13", meal_type="dinner", headcount=400, hostel_strength=500, is_synthetic=1)
    memory_db.add_all([m_b1, m_b2, m_p1, m_p2])
    memory_db.flush()

    memory_db.add(DishLog(meal_id=m_b1.id, dish_id=d.id, cooked_qty=40.0, leftover_qty=15.0, unit="kg", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_b2.id, dish_id=d.id, cooked_qty=40.0, leftover_qty=10.0, unit="kg", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_p1.id, dish_id=d.id, cooked_qty=40.0, leftover_qty=8.0, unit="kg", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_p2.id, dish_id=d.id, cooked_qty=40.0, leftover_qty=5.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    rep1 = compute_pilot_evidence_report(
        session=memory_db,
        baseline_start="2026-10-05",
        baseline_end="2026-10-07",
        pilot_start="2026-10-12",
        pilot_end="2026-10-14",
        is_synthetic=1,
        random_seed=42,
    )
    rep2 = compute_pilot_evidence_report(
        session=memory_db,
        baseline_start="2026-10-05",
        baseline_end="2026-10-07",
        pilot_start="2026-10-12",
        pilot_end="2026-10-14",
        is_synthetic=1,
        random_seed=42,
    )

    assert rep1.bootstrap_ci_95_lower_kg == rep2.bootstrap_ci_95_lower_kg
    assert rep1.bootstrap_ci_95_upper_kg == rep2.bootstrap_ci_95_upper_kg
