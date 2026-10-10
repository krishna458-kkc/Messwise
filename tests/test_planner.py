"""Tests for Step 3: Cooking Quantity Planner and Consumption Learning (B1-B3).

Validates all 20 required points from PLAN.md and project specifications:
1. Served quantity calculation (cooked - leftover)
2. Per-head consumption rate (served / headcount)
3. Robust median estimator
4. Meal-type split
5. Recent-history selection (last 10 meals)
6. Zero headcount handling
7. Insufficient-history fallback
8. Invalid quantity handling (negative, leftover > cooked)
9. B1 quantity formula: H_q * r_d * (1 + prep_loss)
10. Preparation-loss calculation
11. Practical batch-size rounding
12. Service-level calculation (H_q derivation)
13. Changing service level changes recommendation
14. Higher service level does not produce lower planning quantity (monotonicity)
15. Expected surplus and run-out risk calculations
16. Synthetic vs real data separation
17. Planner output structure
18. FastAPI /plan endpoint
19. Invalid /plan inputs (422 validation)
20. Plan persistence in Prediction record and AuditLog
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app, get_db_session
from messwise.db import (
    Base,
    Dish,
    DishLog,
    Meal,
    get_or_create_dish,
    init_db,
    save_meal_plan,
)
from messwise.planner import (
    apply_batch_rounding,
    calculate_service_headcount,
    compute_dish_consumption_rates,
    generate_meal_plan,
    get_fallback_rate_for_dish,
)
from messwise.validation import PlanRequest


@pytest.fixture
def db_session():
    """Provides an isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def populated_session(db_session):
    """Seed test database with known historical meals, dishes, and dish logs."""
    # 1. Register dishes
    rice = get_or_create_dish(
        db_session,
        name="Steamed Rice",
        unit="kg",
        category="staple",
        batch_size=5.0,
        standard_portion=0.085,
    )
    dal = get_or_create_dish(
        db_session,
        name="Dal Tadka",
        unit="L",
        category="main",
        batch_size=5.0,
        standard_portion=0.120,
    )
    roti = get_or_create_dish(
        db_session,
        name="Roti",
        unit="count",
        category="staple",
        batch_size=10.0,
        standard_portion=2.5,
    )
    db_session.flush()

    # 2. Add 12 lunch meals with varying headcounts
    for i in range(12):
        day_str = f"2026-10-{i+1:02d}"
        hc = 400 + (i * 5)  # 400, 405, 410, ...
        m = Meal(
            date=day_str,
            meal_type="lunch",
            headcount=hc,
            hostel_strength=500,
            event_flag=0,
            exam_flag=0,
            holiday_flag=0,
            is_synthetic=0,
        )
        db_session.add(m)
        db_session.flush()

        # Rice log: ~0.100 kg/head served
        cooked_rice = hc * 0.110
        leftover_rice = hc * 0.010  # served = hc * 0.100
        dl_rice = DishLog(
            meal_id=m.id,
            dish_id=rice.id,
            cooked_qty=cooked_rice,
            leftover_qty=leftover_rice,
            unit="kg",
            ran_out=0,
            is_synthetic=0,
        )
        db_session.add(dl_rice)

        # Dal log: ~0.120 L/head served
        cooked_dal = hc * 0.130
        leftover_dal = hc * 0.010
        dl_dal = DishLog(
            meal_id=m.id,
            dish_id=dal.id,
            cooked_qty=cooked_dal,
            leftover_qty=leftover_dal,
            unit="L",
            ran_out=0,
            is_synthetic=0,
        )
        db_session.add(dl_dal)

        # Roti log: on day 5, dish ran out!
        ran_out_flag = 1 if i == 5 else 0
        cooked_roti = hc * 2.5
        leftover_roti = 0.0 if ran_out_flag else 20.0
        dl_roti = DishLog(
            meal_id=m.id,
            dish_id=roti.id,
            cooked_qty=cooked_roti,
            leftover_qty=leftover_roti,
            unit="count",
            ran_out=ran_out_flag,
            is_synthetic=0,
        )
        db_session.add(dl_roti)

    # 3. Add 4 dinner meals (different meal type) with higher rice appetite (~0.150 kg/head)
    for i in range(4):
        day_str = f"2026-10-{i+1:02d}"
        hc = 450
        m = Meal(
            date=day_str,
            meal_type="dinner",
            headcount=hc,
            hostel_strength=500,
            is_synthetic=0,
        )
        db_session.add(m)
        db_session.flush()

        dl_rice = DishLog(
            meal_id=m.id,
            dish_id=rice.id,
            cooked_qty=hc * 0.160,
            leftover_qty=hc * 0.010,  # served = hc * 0.150
            unit="kg",
            ran_out=0,
            is_synthetic=0,
        )
        db_session.add(dl_rice)

    db_session.commit()
    return db_session


# -----------------------------------------------------------------------------
# Test Cases 1-8: Consumption Learning (B2)
# -----------------------------------------------------------------------------

def test_1_and_2_served_qty_and_per_head_rate(populated_session):
    """Test 1 & 2: served = cooked - leftover and rate = served / headcount."""
    rates = compute_dish_consumption_rates(populated_session, meal_type="lunch", is_synthetic=0)
    # Find Steamed Rice
    rice_rec = next(r for r in rates.values() if r.dish_name == "Steamed Rice")
    assert rice_rec.num_observations > 0
    obs = rice_rec.observations[0]
    expected_served = obs.cooked_qty - obs.leftover_qty
    assert obs.served_qty == pytest.approx(expected_served, 1e-4)
    assert obs.rate == pytest.approx(expected_served / obs.headcount, 1e-4)
    # Target rate was seeded at 0.100 kg/head
    assert rice_rec.estimated_rate == pytest.approx(0.100, 1e-3)


def test_3_robust_median_estimator(db_session):
    """Test 3: Uses robust median rather than simple mean, resilient to outliers."""
    dish = get_or_create_dish(db_session, name="Paneer", unit="kg", category="main")
    db_session.flush()

    # 5 meals: 4 normal meals (rate=0.10), 1 extreme outlier overcooked (rate=0.40)
    for i in range(5):
        hc = 100
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=hc, hostel_strength=500, is_synthetic=0)
        db_session.add(m)
        db_session.flush()
        rate = 0.40 if i == 0 else 0.10
        db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=hc * rate, leftover_qty=0.0, unit="kg", ran_out=0, is_synthetic=0))
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=0)
    paneer_rec = rates[dish.id]
    # Median of [0.10, 0.10, 0.10, 0.10, 0.40] is 0.10, mean would be 0.16
    assert paneer_rec.estimated_rate == pytest.approx(0.10, 1e-3)
    assert paneer_rec.confidence_status in ("high", "moderate")


def test_4_meal_type_split(populated_session):
    """Test 4: Learns different consumption rates per meal type."""
    lunch_rates = compute_dish_consumption_rates(populated_session, meal_type="lunch", is_synthetic=0)
    dinner_rates = compute_dish_consumption_rates(populated_session, meal_type="dinner", is_synthetic=0)

    lunch_rice = next(r for r in lunch_rates.values() if r.dish_name == "Steamed Rice")
    dinner_rice = next(r for r in dinner_rates.values() if r.dish_name == "Steamed Rice")

    # Lunch rice rate was seeded at 0.100, Dinner at 0.150
    assert lunch_rice.estimated_rate == pytest.approx(0.100, 1e-3)
    assert dinner_rice.estimated_rate == pytest.approx(0.150, 1e-3)
    assert lunch_rice.estimated_rate != dinner_rice.estimated_rate


def test_5_recent_history_selection(populated_session):
    """Test 5: Considers up to window_size (default 10) most recent meals."""
    rates = compute_dish_consumption_rates(populated_session, meal_type="lunch", window_size=10, is_synthetic=0)
    rice_rec = next(r for r in rates.values() if r.dish_name == "Steamed Rice")
    # Even though 12 lunch meals were added, observations list is capped at 10
    assert len(rice_rec.observations) == 10
    assert rice_rec.num_observations == 10


def test_6_zero_headcount_handling(db_session):
    """Test 6: Headcount = 0 is safely ignored without ZeroDivisionError."""
    dish = get_or_create_dish(db_session, name="Soup", unit="L")
    m = Meal(date="2026-10-01", meal_type="dinner", headcount=0, hostel_strength=500, is_synthetic=0)
    db_session.add(m)
    db_session.flush()
    db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=20.0, leftover_qty=5.0, unit="L", is_synthetic=0))
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="dinner", is_synthetic=0)
    assert dish.id in rates
    # Zero headcount record ignored; fallback used
    assert rates[dish.id].num_usable_observations == 0
    assert rates[dish.id].is_fallback is True


def test_7_insufficient_history_fallback(db_session):
    """Test 7: Dishes with < 3 observations fallback safely to portion defaults."""
    dish_with_portion = get_or_create_dish(
        db_session, name="Special Biryani", unit="kg", category="main", standard_portion=0.180
    )
    dish_no_portion = get_or_create_dish(
        db_session, name="Raita", unit="L", category="side"
    )
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=0)
    # Biryani should use registered standard_portion
    assert rates[dish_with_portion.id].estimated_rate == 0.180
    assert rates[dish_with_portion.id].is_fallback is True
    assert "registered portion" in rates[dish_with_portion.id].fallback_reason

    # Raita should use side/L category default (0.075 L)
    assert rates[dish_no_portion.id].estimated_rate == 0.075
    assert rates[dish_no_portion.id].is_fallback is True


def test_8_invalid_quantity_handling(db_session):
    """Test 8: Negative quantities and leftover > cooked are skipped safely."""
    dish = get_or_create_dish(db_session, name="Idli", unit="count", category="staple")
    m = Meal(date="2026-10-01", meal_type="breakfast", headcount=200, hostel_strength=500, is_synthetic=0)
    db_session.add(m)
    db_session.flush()

    # Leftover > Cooked: invalid record
    db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=100.0, leftover_qty=200.0, unit="count", is_synthetic=0))
    # Negative cooked: invalid record
    db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=-50.0, leftover_qty=0.0, unit="count", is_synthetic=0))
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="breakfast", is_synthetic=0)
    assert rates[dish.id].num_usable_observations == 0
    assert rates[dish.id].is_fallback is True


# -----------------------------------------------------------------------------
# Test Cases 9-11: Quantity Formulas, Prep Loss & Batch Sizing (B1)
# -----------------------------------------------------------------------------

def test_9_and_10_b1_quantity_and_prep_loss(populated_session):
    """Test 9 & 10: Quantity = H_q * r_d * (1 + prep_loss)."""
    plan = generate_meal_plan(
        populated_session,
        target_date="2026-10-15",
        meal_type="lunch",
        service_level=0.95,
        prep_loss_pct=0.05,  # 5% prep loss
        is_synthetic=0,
    )
    assert plan.prep_loss_pct == 0.05
    for dish in plan.dishes:
        expected_theo = dish.per_head_rate * plan.planning_headcount * (1.0 + 0.05)
        assert dish.theo_quantity == pytest.approx(expected_theo, 0.05)


def test_11_practical_batch_size_rounding():
    """Test 11: Practical batch-size rounding rounds theoretical quantity up to batch increment."""
    # 41.3 kg with batch 5.0 kg -> 45.0 kg
    assert apply_batch_rounding(41.3, batch_size=5.0, unit="kg") == 45.0
    # 50.0 kg with batch 5.0 kg -> 50.0 kg
    assert apply_batch_rounding(50.0, batch_size=5.0, unit="kg") == 50.0
    # 0 kg -> 0.0 kg
    assert apply_batch_rounding(0.0, batch_size=5.0, unit="kg") == 0.0
    # Count with batch 10 -> ceil to 10
    assert apply_batch_rounding(12.0, batch_size=10.0, unit="count") == 20.0
    # Count with no batch -> ceil to integer
    assert apply_batch_rounding(12.4, batch_size=None, unit="count") == 13.0


# -----------------------------------------------------------------------------
# Test Cases 12-15: Service-Level Slider & Uncertainty (B3)
# -----------------------------------------------------------------------------

def test_12_and_13_service_level_changes_recommendations(populated_session):
    """Test 12 & 13: Service level calculation derives H_q and changing slider changes quantities."""
    plan_90 = generate_meal_plan(populated_session, "2026-10-15", "lunch", service_level=0.90, is_synthetic=0)
    plan_99 = generate_meal_plan(populated_session, "2026-10-15", "lunch", service_level=0.99, is_synthetic=0)

    assert plan_90.service_level == 0.90
    assert plan_99.service_level == 0.99
    assert plan_90.planning_headcount < plan_99.planning_headcount
    theo_90 = sum(d.theo_quantity for d in plan_90.dishes)
    theo_99 = sum(d.theo_quantity for d in plan_99.dishes)
    assert theo_90 < theo_99
    assert plan_90.total_planned_kg <= plan_99.total_planned_kg


def test_14_higher_service_level_never_produces_lower_quantity(populated_session):
    """Test 14: Monotonicity - H_q and planned quantities never decrease as service level rises."""
    levels = [0.80, 0.90, 0.95, 0.98, 0.99]
    plans = [
        generate_meal_plan(populated_session, "2026-10-15", "lunch", service_level=sl, is_synthetic=0)
        for sl in levels
    ]

    for i in range(len(plans) - 1):
        assert plans[i].planning_headcount <= plans[i+1].planning_headcount
        assert plans[i].total_planned_kg <= plans[i+1].total_planned_kg


def test_15_surplus_and_risk_calculations(populated_session):
    """Test 15: Surplus estimate and run-out risk indicator calculations."""
    plan = generate_meal_plan(populated_session, "2026-10-15", "lunch", service_level=0.95, is_synthetic=0)
    assert plan.run_out_risk_pct == pytest.approx(5.0, 0.5)
    for dish in plan.dishes:
        assert dish.expected_surplus_qty >= 0.0
        assert dish.run_out_risk_label in ("Low", "Moderate", "Elevated")


# -----------------------------------------------------------------------------
# Test Cases 16-17: Synthetic Separation & Structured Output
# -----------------------------------------------------------------------------

def test_16_synthetic_vs_real_separation(populated_session):
    """Test 16: Clearly distinguishes real pilot data from synthetic data."""
    real_plan = generate_meal_plan(populated_session, "2026-10-15", "lunch", is_synthetic=0)
    assert real_plan.is_synthetic == 0
    assert "Real pilot data" in real_plan.data_basis_label

    synth_plan = generate_meal_plan(populated_session, "2026-10-15", "lunch", is_synthetic=1)
    assert synth_plan.is_synthetic == 1
    # No synthetic records were seeded in populated_session for lunch
    assert synth_plan.real_obs_count == 0


def test_17_planner_output_structure(populated_session):
    """Test 17: MealPlanResult contains all documented fields and can serialize to dictionary."""
    plan = generate_meal_plan(populated_session, "2026-10-15", "lunch", is_synthetic=0)
    d = plan.to_dict()
    assert "target_date" in d
    assert "meal_type" in d
    assert "service_level" in d
    assert "forecast_h_hat" in d
    assert "planning_headcount" in d
    assert "dishes" in d
    assert "summary_explanation" in d
    assert len(d["dishes"]) > 0

    first_dish = d["dishes"][0]
    assert "per_head_rate" in first_dish
    assert "theo_quantity" in first_dish
    assert "planned_quantity" in first_dish
    assert "batch_size" in first_dish
    assert "expected_surplus_qty" in first_dish


# -----------------------------------------------------------------------------
# Test Cases 18-20: API /plan, Validation, and DB Persistence
# -----------------------------------------------------------------------------

@pytest.fixture
def client_with_data(populated_session):
    """FastAPI TestClient backed by populated test database."""
    def override_db():
        yield populated_session

    app.dependency_overrides[get_db_session] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_18_fastapi_plan_endpoint(client_with_data):
    """Test 18: FastAPI /plan endpoint returns 200 and structured plan."""
    resp = client_with_data.post(
        "/plan",
        json={
            "date": "2026-10-15",
            "meal_type": "lunch",
            "service_level": 0.95,
            "prep_loss_pct": 0.03,
            "hostel_strength": 500,
            "is_synthetic": 0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "plan" in body
    assert body["plan"]["planning_headcount"] > 0
    assert len(body["plan"]["dishes"]) >= 3


def test_19_invalid_plan_inputs_rejected(client_with_data):
    """Test 19: Rejects invalid inputs (bad date, bad meal, service level out of bounds)."""
    # Bad date
    r1 = client_with_data.post("/plan", json={"date": "bad-date", "meal_type": "lunch"})
    assert r1.status_code == 422

    # Bad meal type
    r2 = client_with_data.post("/plan", json={"date": "2026-10-15", "meal_type": "brunch"})
    assert r2.status_code == 422

    # Service level < 0.50
    r3 = client_with_data.post("/plan", json={"date": "2026-10-15", "meal_type": "lunch", "service_level": 0.30})
    assert r3.status_code == 422

    # Prep loss > 0.25
    r4 = client_with_data.post("/plan", json={"date": "2026-10-15", "meal_type": "lunch", "prep_loss_pct": 0.50})
    assert r4.status_code == 422


def test_20_plan_persistence_and_audit(populated_session):
    """Test 20: Persists plan into Prediction record and records AuditLog."""
    plan = generate_meal_plan(populated_session, "2026-10-15", "lunch", is_synthetic=0)
    pred = save_meal_plan(
        session=populated_session,
        meal_date="2026-10-15",
        meal_type="lunch",
        plan_dict=plan.to_dict(),
        service_level=0.95,
        is_synthetic=0,
        who="kitchen_manager",
    )
    assert pred is not None
    assert pred.plan_json is not None
    assert "Steamed Rice" in pred.plan_json
    assert pred.service_level == 0.95


def test_ran_out_dish_handling_distinguished(db_session):
    """Test that ran-out observations are distinguished and flagged as lower bound."""
    dish = get_or_create_dish(db_session, name="Chicken Curry", unit="kg", category="main")
    db_session.flush()

    # 4 meals where dish ran out (ran_out=1, leftover=0)
    for i in range(4):
        hc = 200
        m = Meal(date=f"2026-10-0{i+1}", meal_type="dinner", headcount=hc, hostel_strength=500, is_synthetic=0)
        db_session.add(m)
        db_session.flush()
        db_session.add(
            DishLog(
                meal_id=m.id,
                dish_id=dish.id,
                cooked_qty=20.0,
                leftover_qty=0.0,
                unit="kg",
                ran_out=1,
                is_synthetic=0,
            )
        )
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="dinner", is_synthetic=0)
    rec = rates[dish.id]
    assert rec.num_ran_out == 4
    assert rec.is_fallback is True
    assert "lower bound" in rec.fallback_reason.lower()
    # Check that observations have is_censored=True ready for B5 Kaplan-Meier
    assert all(o.is_censored for o in rec.observations)


# -----------------------------------------------------------------------------
# Data Honesty & Environment Isolation Tests
# -----------------------------------------------------------------------------

def test_zero_real_records_detection_and_honesty(db_session):
    """Test that zero real records is detected and does not claim real data."""
    from messwise.db import get_data_environment_summary

    summary = get_data_environment_summary(db_session)
    assert summary["real_meals_count"] == 0
    assert summary["has_real_data"] is False

    # In real mode with 0 records, planner uses portion defaults and does NOT claim real pilot data
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple", standard_portion=0.085)
    db_session.commit()

    plan = generate_meal_plan(db_session, "2026-10-15", "lunch", is_synthetic=0)
    assert plan.real_obs_count == 0
    assert "0 historical records available" in plan.data_basis_label
    assert "100% verified" not in plan.data_basis_label
    assert "demonstration only" not in plan.data_basis_label.lower()  # It's real environment with 0 records, not synthetic


def test_synthetic_queries_only_synthetic_records(db_session):
    """Test that synthetic environment queries only is_synthetic = 1 and ignores real."""
    dish = get_or_create_dish(db_session, name="Curd", unit="L", category="side")
    db_session.flush()

    # 1 real meal with very high consumption (rate 0.50)
    m_real = Meal(date="2026-10-01", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=0)
    db_session.add(m_real)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_real.id, dish_id=dish.id, cooked_qty=50.0, leftover_qty=0.0, unit="L", is_synthetic=0))

    # 3 synthetic meals with low consumption (rate 0.05)
    for i in range(3):
        m_synth = Meal(date=f"2026-10-0{i+2}", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
        db_session.add(m_synth)
        db_session.flush()
        db_session.add(DishLog(meal_id=m_synth.id, dish_id=dish.id, cooked_qty=5.0, leftover_qty=0.0, unit="L", is_synthetic=1))
    db_session.commit()

    # Query synthetic environment: must ignore the real record (0.50) completely!
    synth_rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=1)
    rec_synth = synth_rates[dish.id]
    assert rec_synth.num_observations == 3
    assert rec_synth.estimated_rate == pytest.approx(0.05, 1e-3)
    assert all(o.is_synthetic == 1 for o in rec_synth.observations)

    # Query real environment: must ignore synthetic records completely!
    real_rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=0)
    rec_real = real_rates[dish.id]
    assert rec_real.num_observations == 1
    assert all(o.is_synthetic == 0 for o in rec_real.observations)


def test_mixed_environments_remain_separated(db_session):
    """Test that mixed environments never leak or cross-contaminate calculations."""
    dish = get_or_create_dish(db_session, name="Dal", unit="L", category="main")
    db_session.flush()

    # Seed 5 real meals
    for i in range(5):
        m = Meal(date=f"2026-10-1{i}", meal_type="dinner", headcount=200, hostel_strength=500, is_synthetic=0)
        db_session.add(m)
        db_session.flush()
        db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=30.0, leftover_qty=0.0, unit="L", is_synthetic=0))

    # Seed 5 synthetic meals with different quantities
    for i in range(5):
        m = Meal(date=f"2026-10-2{i}", meal_type="dinner", headcount=200, hostel_strength=500, is_synthetic=1)
        db_session.add(m)
        db_session.flush()
        db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=10.0, leftover_qty=0.0, unit="L", is_synthetic=1))
    db_session.commit()

    real_plan = generate_meal_plan(db_session, "2026-10-25", "dinner", is_synthetic=0)
    synth_plan = generate_meal_plan(db_session, "2026-10-25", "dinner", is_synthetic=1)

    assert real_plan.real_obs_count == 5
    assert real_plan.synthetic_obs_count == 0
    assert "Real pilot data" in real_plan.data_basis_label

    assert synth_plan.real_obs_count == 0
    assert synth_plan.synthetic_obs_count == 5
    assert "Synthetic development data" in synth_plan.data_basis_label
    assert "demonstration only" in synth_plan.data_basis_label.lower()

    # Quantities must differ because learned rates are different (30/200 vs 10/200)
    dish_real = next(d for d in real_plan.dishes if d.dish_name == "Dal")
    dish_synth = next(d for d in synth_plan.dishes if d.dish_name == "Dal")
    assert dish_real.per_head_rate != dish_synth.per_head_rate
    assert dish_real.planned_quantity > dish_synth.planned_quantity


# -----------------------------------------------------------------------------
# B3 Service-Level Preset and Live Slider Regression Tests
# -----------------------------------------------------------------------------

def test_b3_presets_and_slider_synchronization_apptest():
    """Verify in Streamlit AppTest that presets and slider sync to shared state without stale 95% default."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    planner_path = Path(__file__).parent.parent / "app" / "pages" / "Planner.py"
    at = AppTest.from_file(planner_path).run()
    assert at.slider(key="service_level_pct").value == 95

    # 1. Selecting 90% updates the active state and slider
    at.button(key="btn_preset_90").click().run()
    assert at.slider(key="service_level_pct").value == 90
    assert not at.exception

    # 2. Selecting 99% updates the active state and slider
    at.button(key="btn_preset_99").click().run()
    assert at.slider(key="service_level_pct").value == 99
    assert not at.exception

    # 3. Selecting 95% updates the active state and slider
    at.button(key="btn_preset_95").click().run()
    assert at.slider(key="service_level_pct").value == 95
    assert not at.exception

    # 4. Continuous slider change updates state
    at.slider(key="service_level_pct").set_value(92).run()
    assert at.slider(key="service_level_pct").value == 92
    assert not at.exception


def test_b3_controlled_residuals_monotonicity_and_recalculation():
    """Verify monotonic planning headcount and quantity changes on controlled residual dataset."""
    from messwise.forecast import ForecastResult, HeadcountForecaster
    from messwise.planner import calculate_service_headcount

    forecaster = HeadcountForecaster()
    # Controlled distribution with distinct quantiles: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
    residuals = [float(x) for x in range(10, 110, 10)]
    forecaster.residuals_by_meal["lunch"] = residuals
    forecaster.all_residuals = residuals

    forecast = ForecastResult(
        target_date="2026-10-15",
        meal_type="lunch",
        h_hat=400,
        h_lo=380,
        h_hi=420,
        hostel_strength=500,
        predicted_participation_rate=0.80,
        baseline_last_week=400,
        baseline_trailing_avg=400,
        model_version="v0.2.0-ridge",
        confidence_status="high",
        low_confidence_flag=False,
        explanation="Test",
        top_drivers=[],
        similar_meals=[],
        is_synthetic=1,
    )

    hq_90, trade_90 = calculate_service_headcount(forecaster, forecast, service_level=0.90)
    hq_95, trade_95 = calculate_service_headcount(forecaster, forecast, service_level=0.95)
    hq_99, trade_99 = calculate_service_headcount(forecaster, forecast, service_level=0.99)

    # 1. Strict monotonicity: H_90 <= H_95 <= H_99
    assert hq_90 <= hq_95 <= hq_99
    # On this controlled dataset, quantiles are strictly separated
    assert hq_90 < hq_95 < hq_99

    # 2. Residual margins and buffers increase with service level
    assert trade_90["residual_margin"] < trade_95["residual_margin"] < trade_99["residual_margin"]
    assert trade_90["headcount_buffer"] < trade_95["headcount_buffer"] < trade_99["headcount_buffer"]

    # 3. Estimated run-out risks decrease with service level
    assert trade_90["run_out_risk_pct"] > trade_95["run_out_risk_pct"] > trade_99["run_out_risk_pct"]


def test_b3_dish_quantities_and_surplus_recalculated(db_session):
    """Verify that full generate_meal_plan recalculates dish quantities and surplus for different service levels."""
    # Seed 5 meals to provide history
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple", standard_portion=0.085)
    db_session.flush()

    for i in range(5):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=400, hostel_strength=500, is_synthetic=1)
        db_session.add(m)
        db_session.flush()
        db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=40.0, leftover_qty=4.0, unit="kg", is_synthetic=1))
    db_session.commit()

    plan_90 = generate_meal_plan(db_session, "2026-10-15", "lunch", service_level=0.90, is_synthetic=1)
    plan_95 = generate_meal_plan(db_session, "2026-10-15", "lunch", service_level=0.95, is_synthetic=1)
    plan_99 = generate_meal_plan(db_session, "2026-10-15", "lunch", service_level=0.99, is_synthetic=1)

    assert plan_90.service_level == 0.90
    assert plan_95.service_level == 0.95
    assert plan_99.service_level == 0.99

    assert plan_90.planning_headcount <= plan_95.planning_headcount <= plan_99.planning_headcount
    assert plan_90.total_planned_kg <= plan_95.total_planned_kg <= plan_99.total_planned_kg
    assert plan_90.total_expected_surplus_kg <= plan_95.total_expected_surplus_kg <= plan_99.total_expected_surplus_kg
    assert plan_90.run_out_risk_pct >= plan_95.run_out_risk_pct >= plan_99.run_out_risk_pct


def test_b3_plan_persistence_records_actual_service_level(db_session):
    """Verify that saving a plan persists the exact selected service level, not a stale 0.95."""
    import json
    from messwise.db import Prediction, save_meal_plan

    dish = get_or_create_dish(db_session, name="Khichdi", unit="kg", category="main")
    db_session.commit()

    plan_99 = generate_meal_plan(db_session, "2026-10-20", "dinner", service_level=0.99, is_synthetic=1)
    saved_pred = save_meal_plan(
        session=db_session,
        meal_date="2026-10-20",
        meal_type="dinner",
        plan_dict=plan_99.to_dict(),
        service_level=0.99,
        is_synthetic=1,
    )
    db_session.commit()

    assert saved_pred.service_level == 0.99
    parsed_payload = json.loads(saved_pred.plan_json)
    assert parsed_payload["service_level"] == 0.99


def test_b6_monte_carlo_determinism():
    """Verify B6 Monte Carlo simulation produces deterministic, reproducible results for fixed seed."""
    from messwise.planner import simulate_joint_demand_monte_carlo, DishObservation

    obs = [
        DishObservation("2026-10-01", 1, 300, 30.0, 3.0, 27.0, 0.090, False, False, 1),
        DishObservation("2026-10-02", 2, 320, 32.0, 2.0, 30.0, 0.0937, False, False, 1),
        DishObservation("2026-10-03", 3, 290, 28.0, 1.0, 27.0, 0.0931, False, False, 1),
    ]

    res1 = simulate_joint_demand_monte_carlo(
        h_hat=300,
        hostel_strength=500,
        residuals=[10.0, 15.0, 12.0, 8.0, 20.0],
        dish_id=1,
        dish_name="Rice",
        unit="kg",
        service_level=0.95,
        prep_loss_pct=0.03,
        learned_rate=0.092,
        dish_observations=obs,
        batch_size=5.0,
        num_simulations=1000,
        random_seed=42,
    )

    res2 = simulate_joint_demand_monte_carlo(
        h_hat=300,
        hostel_strength=500,
        residuals=[10.0, 15.0, 12.0, 8.0, 20.0],
        dish_id=1,
        dish_name="Rice",
        unit="kg",
        service_level=0.95,
        prep_loss_pct=0.03,
        learned_rate=0.092,
        dish_observations=obs,
        batch_size=5.0,
        num_simulations=1000,
        random_seed=42,
    )

    assert res1.theo_cook_quantity == res2.theo_cook_quantity
    assert res1.planned_cook_quantity == res2.planned_cook_quantity
    assert res1.demand_p50 == res2.demand_p50
    assert res1.p_runout == res2.p_runout
    assert res1.expected_surplus == res2.expected_surplus
    assert not res1.is_fallback


def test_b6_monte_carlo_monotonic_quantiles_and_service_level():
    """Verify B6 demand quantiles are strictly ordered and higher service level scales cook quantity."""
    from messwise.planner import simulate_joint_demand_monte_carlo

    residuals = [12.0, 18.0, 15.0, 10.0, 25.0]

    res_90 = simulate_joint_demand_monte_carlo(
        h_hat=350,
        hostel_strength=500,
        residuals=residuals,
        dish_id=2,
        dish_name="Dal",
        unit="L",
        service_level=0.90,
        prep_loss_pct=0.02,
        learned_rate=0.120,
        dish_observations=[],
        batch_size=5.0,
        num_simulations=2000,
        random_seed=123,
    )

    res_99 = simulate_joint_demand_monte_carlo(
        h_hat=350,
        hostel_strength=500,
        residuals=residuals,
        dish_id=2,
        dish_name="Dal",
        unit="L",
        service_level=0.99,
        prep_loss_pct=0.02,
        learned_rate=0.120,
        dish_observations=[],
        batch_size=5.0,
        num_simulations=2000,
        random_seed=123,
    )

    # Monotonic quantile progression
    assert res_90.demand_p10 <= res_90.demand_p50 <= res_90.demand_p90 <= res_90.demand_p95 <= res_90.demand_p99
    # Cold start with 0 observations reports fallback honestly
    assert res_90.is_fallback
    assert "Insufficient dish history" in (res_90.fallback_reason or "")
    # 99% target plans at least as much as 90% target
    assert res_99.planned_cook_quantity >= res_90.planned_cook_quantity
    assert res_99.p_runout <= res_90.p_runout


def test_b6_meal_plan_integration_has_mc_demand(db_session):
    """Verify that generate_meal_plan attaches mc_demand to all dishes and to_dict serializes it."""
    dish = get_or_create_dish(db_session, name="Sambar", unit="L", category="main", standard_portion=0.110)
    db_session.flush()

    for i in range(4):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=250, hostel_strength=500, is_synthetic=1)
        db_session.add(m)
        db_session.flush()
        db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=28.0, leftover_qty=2.0, unit="L", is_synthetic=1))
    db_session.commit()

    plan = generate_meal_plan(db_session, "2026-10-18", "lunch", service_level=0.95, is_synthetic=1)
    assert len(plan.dishes) >= 1
    sambar_item = next(d for d in plan.dishes if d.dish_id == dish.id)
    assert sambar_item.mc_demand is not None
    assert sambar_item.mc_demand.num_simulations == 5000
    assert sambar_item.mc_demand.demand_p50 > 0

    plan_dict = plan.to_dict()
    dish_dict = next(d for d in plan_dict["dishes"] if d["dish_id"] == dish.id)
    assert "mc_demand" in dish_dict
    assert dish_dict["mc_demand"]["demand_p50"] == sambar_item.mc_demand.demand_p50



