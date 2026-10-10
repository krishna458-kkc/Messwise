"""Tests for In-App Operational Notifications (Module I: I9)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from messwise.db import Dish, DishLog, Meal, Prediction, SurplusEvent, init_db, get_or_create_dish
from messwise.notifications import get_active_notifications


@pytest.fixture
def memory_db():
    """Provides isolated in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_notifications_empty_state(memory_db):
    """Verify empty database produces 0 notifications without errors."""
    notifs = get_active_notifications(memory_db, is_synthetic=1)
    assert notifs == []


def test_notifications_forecast_uncertainty(memory_db):
    """Verify prediction with wide conformal band triggers forecast_risk alert."""
    pred = Prediction(
        meal_date="2026-10-15",
        meal_type="lunch",
        h_hat=300,
        h_lo=240,
        h_hi=360,  # Spread 120 >= 50
        is_synthetic=1,
    )
    memory_db.add(pred)
    memory_db.commit()

    notifs = get_active_notifications(memory_db, is_synthetic=1)
    assert len(notifs) >= 1
    fc_notif = next(n for n in notifs if n.category == "forecast_risk")
    assert fc_notif.severity == "medium"
    assert "uncertainty" in fc_notif.title.lower()


def test_notifications_surplus_expired(memory_db):
    """Verify expired surplus event triggers high-severity safety_clock notification."""
    d = get_or_create_dish(memory_db, name="Dal", unit="L", category="main")
    m = Meal(date="2026-10-10", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
    memory_db.add(m)
    memory_db.flush()

    se = SurplusEvent(
        meal_id=m.id,
        meal_date="2026-10-10",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=12.0,
        eligibility_status="blocked_expired",
        blocking_reason="Exceeded 90-minute safety window at ambient temperature",
        is_synthetic=1,
    )
    memory_db.add(se)
    memory_db.commit()

    notifs = get_active_notifications(memory_db, is_synthetic=1)
    safety_notif = next(n for n in notifs if n.category == "safety_clock")
    assert safety_notif.severity == "high"
    assert "safety clock expired" in safety_notif.title.lower()


def test_notifications_deduplication(memory_db):
    """Verify notification IDs are deduplicated."""
    pred = Prediction(
        meal_date="2026-10-16",
        meal_type="dinner",
        h_hat=320,
        h_lo=260,
        h_hi=380,
        is_synthetic=1,
    )
    memory_db.add(pred)
    memory_db.commit()

    notifs = get_active_notifications(memory_db, is_synthetic=1)
    ids = [n.notification_id for n in notifs]
    assert len(ids) == len(set(ids))
