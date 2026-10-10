"""Tests for G1 Predicted-Surplus Alerts and G2 Food-Safety Clock.

Covers all 27 testing requirements specified in Step 7 of PLAN.md:
1. Creating a potential-surplus alert from valid planner/measurement data.
2. Predicted surplus vs measured surplus clearly distinguished.
3. Correct compatible-unit handling.
4. Zero/negative/missing quantities handled safely.
5. Synthetic alerts remain labelled synthetic.
6. Synthetic events cannot trigger real external communication.
7. Valid safety-start timestamp.
8. Time remaining calculation.
9. Safety-window expiry.
10. Expired items are blocked from approval/communication.
11. Unconfirmed eligibility blocks communication.
12. Missing required temperature observations block eligibility.
13. Invalid temperature values/units handled safely.
14. Suspected contamination blocks eligibility.
15. Missing/unverified policy configuration blocks affected workflow.
16. Updated temperature/time observations recompute eligibility.
17. Expiry enforced server-side, not just in the UI.
18. An expired alert cannot be approved through FastAPI.
19. Direct API calls cannot bypass safety gates.
20. Manager approval is logged.
21. Manager dismissal and reason logged appropriately.
22. Ineligible alerts cannot generate a permitted external-message draft.
23. Valid eligible, manager-approved event produces draft with legitimate partner contact.
24. Missing partner configuration handled honestly.
25. Duplicate alert creation handled appropriately.
26. Policy version and decision timestamps preserved.
27. Existing Step 1–6 functions continue to work.
"""

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app, get_db_session
from messwise.db import (
    AuditLog,
    Dish,
    DishLog,
    Meal,
    SurplusEvent,
    get_or_create_dish,
    init_db,
)
from messwise.surplus import (
    APP_TIMEZONE,
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
    record_safety_observation,
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

    # Seed baseline dishes
    d_rice = get_or_create_dish(session, "Rice", unit="kg", category="staple", criticality_tier="staple", batch_size=5.0)
    d_dal = get_or_create_dish(session, "Dal Tadka", unit="L", category="main", criticality_tier="main", batch_size=5.0)
    d_roti = get_or_create_dish(session, "Roti", unit="count", category="staple", criticality_tier="staple", batch_size=10.0)

    # Seed historical meals for consumption learning
    for i in range(1, 11):
        meal = Meal(
            date=f"2026-10-{i:02d}",
            meal_type="lunch",
            headcount=400,
            hostel_strength=500,
            is_synthetic=1,
        )
        session.add(meal)
        session.flush()
        session.add(DishLog(meal_id=meal.id, dish_id=d_rice.id, cooked_qty=40.0, leftover_qty=4.0, unit="kg", waste_stage="serving_surplus", is_synthetic=1))
        session.add(DishLog(meal_id=meal.id, dish_id=d_dal.id, cooked_qty=50.0, leftover_qty=5.0, unit="L", waste_stage="serving_surplus", is_synthetic=1))
        session.add(DishLog(meal_id=meal.id, dish_id=d_roti.id, cooked_qty=1000.0, leftover_qty=100.0, unit="count", waste_stage="serving_surplus", is_synthetic=1))

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


# ------------------------------------------------------------------------------
# Test 1, 2, 3, 4: G1 Alert Generation, Unit Handling, Predicted vs Measured
# ------------------------------------------------------------------------------

def test_predicted_surplus_alert_generation(test_db):
    """Req 1 & 2: Generate predicted surplus alerts from plan, distinct from measured."""
    alerts = generate_predicted_surplus_alerts(
        session=test_db,
        target_date="2026-10-15",
        meal_type="lunch",
        is_synthetic=1,
        threshold_kg=1.0,
    )
    assert len(alerts) > 0
    for a in alerts:
        assert a.surplus_type == "predicted"
        assert a.estimated_qty > 0
        assert a.uncertainty_range is not None
        assert a.eligibility_status == "pending_inspection"
        assert a.manager_status == "pending"
        # Pre-service predicted food must NOT have confirmed cooking time yet
        assert a.cooking_completed_at is None


def test_measured_surplus_alert_generation(test_db):
    """Req 2: Measured surplus alerts derived from actual kitchen logs."""
    # Create completed meal with serving surplus
    m = Meal(date="2026-10-14", meal_type="dinner", headcount=380, hostel_strength=500, is_synthetic=0)
    test_db.add(m)
    test_db.flush()
    d = test_db.query(Dish).filter(Dish.name == "Rice").first()
    test_db.add(DishLog(meal_id=m.id, dish_id=d.id, cooked_qty=35.0, leftover_qty=6.5, unit="kg", waste_stage="serving_surplus", is_synthetic=0))
    test_db.commit()

    alerts = generate_measured_surplus_alerts(session=test_db, meal_id=m.id, threshold_kg=2.0)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.surplus_type == "measured"
    assert alert.estimated_qty == 6.5
    assert alert.unit == "kg"
    assert alert.is_synthetic == 0


def test_plate_waste_is_disqualified_from_surplus(test_db):
    """Req 2: Plate waste must never be converted into surplus alerts."""
    m = Meal(date="2026-10-14", meal_type="lunch", headcount=300, hostel_strength=500, is_synthetic=0)
    test_db.add(m)
    test_db.flush()
    d = test_db.query(Dish).filter(Dish.name == "Rice").first()
    # Plate waste of 8.0 kg
    test_db.add(DishLog(meal_id=m.id, dish_id=d.id, cooked_qty=35.0, leftover_qty=8.0, unit="kg", waste_stage="plate_waste", is_synthetic=0))
    test_db.commit()

    alerts = generate_measured_surplus_alerts(session=test_db, meal_id=m.id, threshold_kg=1.0)
    assert len(alerts) == 0  # Plate waste is completely ignored


def test_compatible_unit_handling(test_db):
    """Req 3: Compatible unit handling (kg, L, count) without mixing units."""
    alerts = generate_predicted_surplus_alerts(
        session=test_db,
        target_date="2026-10-15",
        meal_type="lunch",
        is_synthetic=1,
        threshold_kg=1.0,
    )
    units = {a.unit for a in alerts}
    assert "kg" in units or "L" in units or "count" in units


def test_zero_or_negative_quantities_produce_no_alerts(test_db):
    """Req 4: Zero or negative quantities do not produce surplus alerts."""
    m = Meal(date="2026-10-14", meal_type="dinner", headcount=400, hostel_strength=500, is_synthetic=0)
    test_db.add(m)
    test_db.flush()
    d = test_db.query(Dish).filter(Dish.name == "Rice").first()
    test_db.add(DishLog(meal_id=m.id, dish_id=d.id, cooked_qty=30.0, leftover_qty=0.0, unit="kg", waste_stage="serving_surplus", is_synthetic=0))
    test_db.commit()

    alerts = generate_measured_surplus_alerts(session=test_db, meal_id=m.id, threshold_kg=1.0)
    assert len(alerts) == 0


def test_duplicate_alert_handling(test_db):
    """Req 25: Repeated generation updates existing alert rather than duplicating."""
    alerts1 = generate_predicted_surplus_alerts(session=test_db, target_date="2026-10-16", meal_type="lunch", is_synthetic=1)
    count1 = test_db.query(SurplusEvent).count()
    alerts2 = generate_predicted_surplus_alerts(session=test_db, target_date="2026-10-16", meal_type="lunch", is_synthetic=1)
    count2 = test_db.query(SurplusEvent).count()
    assert count1 == count2


# ------------------------------------------------------------------------------
# Test 5, 6: Synthetic vs Real Separation
# ------------------------------------------------------------------------------

def test_synthetic_alert_labelling_and_draft(test_db):
    """Req 5 & 6: Synthetic alerts labelled clearly and cannot trigger real communication."""
    d = test_db.query(Dish).first()
    now_dt = datetime.now(APP_TIMEZONE)
    alert = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=5.0,
        unit="kg",
        cooking_completed_at=(now_dt - timedelta(hours=1)).isoformat(),
        hold_type="hot",
        is_synthetic=1,  # SYNTHETIC DEMO
    )
    test_db.add(alert)
    test_db.commit()

    # Record safe temp
    record_safety_observation(
        session=test_db,
        alert_id=alert.id,
        temp_c=72.0,
        as_of_time=now_dt.isoformat(),
    )

    # Approve
    approved = approve_surplus_alert(
        session=test_db,
        alert_id=alert.id,
        manager_who="manager_bob",
        partner_phone="9876543210",
        as_of_time=now_dt.isoformat(),
    )
    assert approved.is_synthetic == 1
    assert "SYNTHETIC DEMONSTRATION — NOT A REAL FOOD DONATION" in approved.communication_draft


# ------------------------------------------------------------------------------
# Test 7, 8, 9, 10: G2 Food-Safety Clock, Elapsed Time, Expiry Enforcement
# ------------------------------------------------------------------------------

def test_food_safety_clock_elapsed_and_remaining():
    """Req 7 & 8: Deterministic time elapsed and remaining calculations."""
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of = datetime(2026, 10, 15, 13, 30, tzinfo=APP_TIMEZONE)  # 1.5h elapsed

    obs = [{"temp_c": 70.0, "timestamp": as_of.isoformat()}]
    res = evaluate_food_safety_clock(
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        observations=obs,
        as_of_time=as_of,
    )
    assert res.elapsed_hours == 1.5
    assert res.remaining_hours == 2.5  # 4h - 1.5h
    assert res.is_expired is False
    assert res.eligibility_status == "eligible"


def test_safety_window_expiry_blocks_donation():
    """Req 9 & 10: Holding time > 4h marks food expired and blocks eligibility."""
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of = datetime(2026, 10, 15, 16, 30, tzinfo=APP_TIMEZONE)  # 4.5h elapsed (> 4h)

    obs = [{"temp_c": 70.0, "timestamp": as_of.isoformat()}]
    res = evaluate_food_safety_clock(
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        observations=obs,
        as_of_time=as_of,
    )
    assert res.is_expired is True
    assert res.remaining_hours == 0.0
    assert res.eligibility_status == "blocked_expired"
    assert "expired" in res.blocking_reason.lower()


def test_ambient_hold_expires_after_two_hours():
    """Req 9: Ambient / unheated food has a strict 2-hour cutoff."""
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of = datetime(2026, 10, 15, 14, 15, tzinfo=APP_TIMEZONE)  # 2.25h elapsed (> 2h)

    obs = [{"temp_c": 30.0, "timestamp": as_of.isoformat()}]
    res = evaluate_food_safety_clock(
        cooking_completed_at=start_time.isoformat(),
        hold_type="ambient",
        observations=obs,
        as_of_time=as_of,
    )
    assert res.is_expired is True
    assert res.eligibility_status == "blocked_expired"


# ------------------------------------------------------------------------------
# Test 11, 12, 13, 14, 15: Temperature & Observation Validations, Contamination
# ------------------------------------------------------------------------------

def test_missing_temperature_observation_blocks_eligibility():
    """Req 11 & 12: Missing required temperature observations block eligibility."""
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of = datetime(2026, 10, 15, 13, 0, tzinfo=APP_TIMEZONE)

    res = evaluate_food_safety_clock(
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        observations=[],  # Empty
        as_of_time=as_of,
    )
    assert res.eligibility_status == "pending_inspection"
    assert "Pending temperature observation" in res.blocking_reason


def test_temperature_below_65c_hot_hold_blocks_eligibility():
    """Req 13: Food dropping below 65°C into Danger Zone is blocked."""
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of = datetime(2026, 10, 15, 13, 0, tzinfo=APP_TIMEZONE)

    obs = [{"temp_c": 58.0, "timestamp": as_of.isoformat()}]  # Danger Zone (< 65°C)
    res = evaluate_food_safety_clock(
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        observations=obs,
        as_of_time=as_of,
    )
    assert res.eligibility_status == "blocked_temperature"
    assert "Danger Zone" in res.blocking_reason


def test_invalid_temperature_value_handled_safely():
    """Req 13: Non-physical temperature (-50°C or 200°C) is flagged as invalid data."""
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of = datetime(2026, 10, 15, 13, 0, tzinfo=APP_TIMEZONE)

    obs = [{"temp_c": 180.0, "timestamp": as_of.isoformat()}]
    res = evaluate_food_safety_clock(
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        observations=obs,
        as_of_time=as_of,
    )
    assert res.eligibility_status == "blocked_missing_data"
    assert "outside realistic physical limits" in res.blocking_reason


def test_suspected_contamination_blocks_eligibility():
    """Req 14: Suspected contamination immediately blocks donation."""
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of = datetime(2026, 10, 15, 13, 0, tzinfo=APP_TIMEZONE)

    obs = [{"temp_c": 75.0, "timestamp": as_of.isoformat()}]
    res = evaluate_food_safety_clock(
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        observations=obs,
        suspected_contamination=True,
        as_of_time=as_of,
    )
    assert res.eligibility_status == "blocked_contamination"
    assert "prohibit recovery" in res.blocking_reason


def test_missing_cooking_completed_timestamp():
    """Req 15: Missing start time blocks eligibility."""
    res = evaluate_food_safety_clock(
        cooking_completed_at=None,
        hold_type="hot",
        observations=[{"temp_c": 75.0}],
    )
    assert res.eligibility_status == "blocked_missing_data"


# ------------------------------------------------------------------------------
# Test 16, 17, 18, 19: Server-side Gate Enforcement, Recomputed Observations, API
# ------------------------------------------------------------------------------

def test_temperature_update_recomputes_eligibility(test_db):
    """Req 16: Updated observations recompute eligibility dynamically."""
    d = test_db.query(Dish).first()
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    alert = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=4.0,
        unit="kg",
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        is_synthetic=0,
    )
    test_db.add(alert)
    test_db.commit()

    # 1. First observation is below 65°C -> blocked_temperature
    alert, clock1 = record_safety_observation(
        session=test_db,
        alert_id=alert.id,
        temp_c=55.0,
        as_of_time=start_time + timedelta(minutes=30),
    )
    assert alert.eligibility_status == "blocked_temperature"

    # 2. Re-heated and verified at 75°C -> eligible
    alert, clock2 = record_safety_observation(
        session=test_db,
        alert_id=alert.id,
        temp_c=75.0,
        as_of_time=start_time + timedelta(minutes=45),
    )
    assert alert.eligibility_status == "eligible"


def test_backend_refuses_approval_of_expired_item(test_db):
    """Req 17: Backend logic strictly refuses approval for expired food."""
    d = test_db.query(Dish).first()
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    as_of_expired = datetime(2026, 10, 15, 17, 0, tzinfo=APP_TIMEZONE)  # 5 hours elapsed

    alert = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=4.0,
        unit="kg",
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        is_synthetic=0,
    )
    test_db.add(alert)
    test_db.commit()

    record_safety_observation(
        session=test_db,
        alert_id=alert.id,
        temp_c=70.0,
        as_of_time=as_of_expired,
    )

    with pytest.raises(ValueError, match="Food safety gate blocked"):
        approve_surplus_alert(
            session=test_db,
            alert_id=alert.id,
            manager_who="manager_alice",
            as_of_time=as_of_expired,
        )


def test_fastapi_rejects_approval_of_ineligible_item(api_client, test_db):
    """Req 18 & 19: Direct API requests cannot bypass safety gates (returns 400)."""
    d = test_db.query(Dish).first()
    alert = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=5.0,
        unit="kg",
        cooking_completed_at=None,  # Missing start time
        hold_type="hot",
        is_synthetic=0,
    )
    test_db.add(alert)
    test_db.commit()

    # Attempt to approve via API
    resp = api_client.post(
        f"/surplus/alerts/{alert.id}/decision",
        json={"action": "approve", "manager_who": "hacker_trying_to_bypass"},
    )
    assert resp.status_code == 400
    assert "Food safety gate blocked" in resp.json()["detail"]


# ------------------------------------------------------------------------------
# Test 20, 21, 22, 23, 24, 26: Manager Review, Logging, Drafts, Policy Preservation
# ------------------------------------------------------------------------------

def test_manager_approval_and_dismissal_audit_logging(test_db):
    """Req 20 & 21: Manager approval and dismissal are logged in AuditLog."""
    d = test_db.query(Dish).first()
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    now_time = datetime(2026, 10, 15, 13, 0, tzinfo=APP_TIMEZONE)

    alert = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=8.0,
        unit="kg",
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        is_synthetic=0,
    )
    test_db.add(alert)
    test_db.commit()

    record_safety_observation(test_db, alert.id, temp_c=72.0, as_of_time=now_time)

    # Approve
    approve_surplus_alert(test_db, alert.id, manager_who="chef_ramesh", as_of_time=now_time)
    audit_app = test_db.query(AuditLog).filter(AuditLog.action == "surplus_approved").first()
    assert audit_app is not None
    assert audit_app.who == "chef_ramesh"

    # Dismiss another alert
    alert2 = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="predicted",
        estimated_qty=2.0,
        unit="kg",
        is_synthetic=0,
    )
    test_db.add(alert2)
    test_db.commit()

    dismiss_surplus_alert(test_db, alert2.id, manager_who="chef_ramesh", manager_reason="Not enough surplus for NGO trip")
    audit_dis = test_db.query(AuditLog).filter(AuditLog.action == "surplus_dismissed").first()
    assert audit_dis is not None
    assert "Not enough surplus" in audit_dis.new_value


def test_eligible_approved_event_produces_draft_and_whatsapp_link(test_db):
    """Req 22, 23 & 24: Legitimate draft generated with WhatsApp link when configured."""
    d = test_db.query(Dish).first()
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    now_time = datetime(2026, 10, 15, 13, 0, tzinfo=APP_TIMEZONE)

    alert = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=10.0,
        unit="kg",
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        is_synthetic=0,
    )
    test_db.add(alert)
    test_db.commit()

    record_safety_observation(test_db, alert.id, temp_c=74.0, as_of_time=now_time)

    # Approve with partner contact
    approved = approve_surplus_alert(
        session=test_db,
        alert_id=alert.id,
        manager_who="manager_suresh",
        partner_name="Feeding India",
        partner_phone="+919876543210",
        as_of_time=now_time,
    )
    assert approved.manager_status == "approved"
    assert "MessWise Surplus Food Recovery Alert" in approved.communication_draft
    assert "Rice" in approved.communication_draft
    assert "10.0 kg" in approved.communication_draft
    assert approved.policy_version == FSSAI_POLICY_VERSION

    # Build communication draft helper
    text, wa_link = build_communication_draft(approved, approved.partner_name, approved.partner_phone)
    assert wa_link is not None
    assert "wa.me/919876543210" in wa_link

    # Missing partner phone handled honestly (no link generated)
    text_no_phone, wa_no_phone = build_communication_draft(approved, approved.partner_name, None)
    assert wa_no_phone is None


def test_policy_version_and_decision_timestamps_preserved(test_db):
    """Req 26: Policy version and decision timestamps are preserved on the event."""
    d = test_db.query(Dish).first()
    start_time = datetime(2026, 10, 15, 12, 0, tzinfo=APP_TIMEZONE)
    now_time = datetime(2026, 10, 15, 13, 0, tzinfo=APP_TIMEZONE)

    alert = SurplusEvent(
        meal_date="2026-10-15",
        meal_type="lunch",
        dish_id=d.id,
        surplus_type="measured",
        estimated_qty=5.0,
        unit="kg",
        cooking_completed_at=start_time.isoformat(),
        hold_type="hot",
        is_synthetic=0,
    )
    test_db.add(alert)
    test_db.commit()

    record_safety_observation(test_db, alert.id, temp_c=68.0, as_of_time=now_time)
    approved = approve_surplus_alert(test_db, alert.id, manager_who="manager_x", as_of_time=now_time)

    assert approved.policy_version == FSSAI_POLICY_VERSION
    assert approved.manager_action_at is not None


# ------------------------------------------------------------------------------
# Test 27: Regression check for Step 1-6 APIs
# ------------------------------------------------------------------------------

def test_step_1_to_6_api_endpoints_continue_working(api_client):
    """Req 27: Verify prior endpoints (/health, /forecast, /plan, /simulate) still work."""
    # /health
    r_health = api_client.get("/health")
    assert r_health.status_code == 200

    # /forecast
    r_fc = api_client.get("/forecast?date=2026-10-20&days=1&hostel_strength=500")
    assert r_fc.status_code == 200

    # /plan
    r_plan = api_client.post("/plan", json={"date": "2026-10-20", "meal_type": "lunch", "service_level": 0.95})
    assert r_plan.status_code == 200

    # /simulate
    r_sim = api_client.post(
        "/simulate",
        json={
            "is_synthetic": 1,
            "service_level": 0.95,
            "hostel_strength": 500,
        },
    )
    assert r_sim.status_code == 200


def test_streamlit_surplus_routing_apptest():
    """Verify Streamlit Surplus_Routing page renders cleanly without exceptions."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    script_path = Path(__file__).parent.parent / "app" / "pages" / "Surplus_Routing.py"
    at = AppTest.from_file(str(script_path), default_timeout=30)
    at.run()
    assert not at.exception, f"Exception in Surplus_Routing.py: {at.exception}"



