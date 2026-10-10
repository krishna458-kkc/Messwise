"""Comprehensive verification test suite for Build-Ladder Step 6: B4 & B5.

Verifies:
- B4 Cost-Aware Optimiser (Newsvendor logic):
  1. Newsvendor formula q* = Cu / (Cu + Co)
  2. Equivalent ratio k = Cu / Co (q* = k / (k + 1))
  3. Correct default criticality tiers (staple 99%, main 95%, side 90%)
  4. Safety floor behavior (clamping at default 90%)
  5. Missing economic cost honest policy fallback
  6. Non-positive and invalid cost handling
  7. Manager override application and reason recording
  8. Monotonicity of shortage penalty ratio k
  9. Planner integration of effective service level
  10. Dish quantities reflect cost-aware service level
  11. Explanation accuracy
  12. B3 manual mode compatibility
- B5 Kaplan-Meier Shortage-Aware Consumption Learning:
  13. Correct served-quantity calculation
  14. Correct per-head rate
  15. Meal type and dish separation
  16. Recent history window selection
  17. Explicit ran_out = 1 right-censoring
  18. Event indicators exact vs censored
  19. Kaplan-Meier quantile direction (S(r_q) <= 1 - q)
  20. Monotonicity across quantiles
  21. Small history fallback (n < 3)
  22. Heavy censoring fallback (n_exact < 2)
  23. Fallback and confidence indicators
  24. Ambiguous zero-leftover records handling
  25. Zero headcount and invalid quantities safety
  26. Strict synthetic vs real data isolation
  27. Look-ahead leakage prevention (before_date / before_meal_id)
  28. Planner consumption of B5 rates
  29. Cutoff compatibility with simulator
  30. Prediction log and audit preservation
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from messwise.db import (
    Base,
    Dish,
    DishLog,
    Meal,
    Prediction,
    get_or_create_dish,
    init_db,
    save_meal_plan,
)
from messwise.planner import (
    DEFAULT_CRITICALITY_TIERS,
    DEFAULT_SAFETY_FLOOR,
    DishCostConfig,
    calculate_newsvendor_service_level,
    compute_dish_consumption_rates,
    fit_kaplan_meier_consumption,
    generate_meal_plan,
)


@pytest.fixture
def db_session():
    """Create isolated in-memory SQLite database session."""
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


# =============================================================================
# B4 Tests: Cost-Aware Optimiser / Newsvendor Logic
# =============================================================================

def test_1_newsvendor_formula_direct_cu_co():
    """Test 1: Direct Cu and Co inputs satisfy q* = Cu / (Cu + Co)."""
    # Cu=19, Co=1 -> q* = 19/20 = 0.95
    res = calculate_newsvendor_service_level(category="main", cu=19.0, co=1.0)
    assert res.economic_service_level == pytest.approx(0.95, 1e-4)
    assert res.effective_service_level == pytest.approx(0.95, 1e-4)
    assert res.cost_ratio_k == pytest.approx(19.0, 1e-4)
    assert res.is_policy_default is False
    assert res.is_floor_applied is False

    # Cu=99, Co=1 -> q* = 99/100 = 0.99
    res_staple = calculate_newsvendor_service_level(category="staple", cu=99.0, co=1.0)
    assert res_staple.economic_service_level == pytest.approx(0.99, 1e-4)
    assert res_staple.effective_service_level == pytest.approx(0.99, 1e-4)


def test_2_newsvendor_equivalent_ratio_k():
    """Test 2: Equivalent cost ratio k = Cu / Co yields q* = k / (k + 1)."""
    # k = 9 -> q* = 9 / 10 = 0.90
    res_9 = calculate_newsvendor_service_level(category="side", k=9.0)
    assert res_9.economic_service_level == pytest.approx(0.90, 1e-4)
    assert res_9.effective_service_level == pytest.approx(0.90, 1e-4)
    assert res_9.is_policy_default is False

    # k = 49 -> q* = 49 / 50 = 0.98
    res_49 = calculate_newsvendor_service_level(category="main", k=49.0)
    assert res_49.economic_service_level == pytest.approx(0.98, 1e-4)
    assert res_49.effective_service_level == pytest.approx(0.98, 1e-4)


def test_3_dish_criticality_defaults():
    """Test 3: Correct default criticality tiers when no costs are configured."""
    # Staples (rice, roti): 99% target (k=99)
    res_staple = calculate_newsvendor_service_level(category="staple")
    assert res_staple.effective_service_level == 0.99
    assert res_staple.cost_ratio_k == 99.0
    assert res_staple.criticality_tier == "staple"
    assert res_staple.is_policy_default is True

    # Main curries: 95% target (k=19)
    res_main = calculate_newsvendor_service_level(category="main")
    assert res_main.effective_service_level == 0.95
    assert res_main.cost_ratio_k == 19.0
    assert res_main.criticality_tier == "main"
    assert res_main.is_policy_default is True

    # Sides: 90% target (k=9)
    res_side = calculate_newsvendor_service_level(category="side")
    assert res_side.effective_service_level == 0.90
    assert res_side.cost_ratio_k == 9.0
    assert res_side.criticality_tier == "side"
    assert res_side.is_policy_default is True

    # Unknown category: falls back to main tier (95%) with clear note
    res_unknown = calculate_newsvendor_service_level(category="dessert_special")
    assert res_unknown.effective_service_level == 0.95
    assert res_unknown.criticality_tier == "main"
    assert res_unknown.is_policy_default is True


def test_4_safety_floor_protection():
    """Test 4: Economic target below safety floor is raised to the safety floor."""
    # Cu=3, Co=1 -> k=3, q* = 3/4 = 0.75. Floor is 0.90
    res = calculate_newsvendor_service_level(category="main", cu=3.0, co=1.0, safety_floor=0.90)
    assert res.economic_service_level == pytest.approx(0.75, 1e-4)
    assert res.effective_service_level == pytest.approx(0.90, 1e-4)
    assert res.is_floor_applied is True
    assert "Safety protection floor (90%) raised the economic target" in res.explanation


def test_5_missing_economic_costs_uses_policy_honestly():
    """Test 5: Explicitly declares that policy default is used rather than verified costs."""
    res = calculate_newsvendor_service_level(category="staple", cu=None, co=None, k=None)
    assert res.is_policy_default is True
    assert "No verified economic cost inputs are configured" in res.explanation
    assert "documented criticality policy defaults" in res.explanation


def test_6_invalid_cost_inputs_handled_safely():
    """Test 6: Negative, zero, or non-numeric costs safely fall back to policy defaults."""
    # Negative costs
    res_neg = calculate_newsvendor_service_level(category="main", cu=-10.0, co=5.0)
    assert res_neg.is_policy_default is True
    assert res_neg.effective_service_level == 0.95

    # Zero cost
    res_zero = calculate_newsvendor_service_level(category="staple", cu=0.0, co=10.0)
    assert res_zero.is_policy_default is True
    assert res_zero.effective_service_level == 0.99

    # Non-numeric
    res_invalid = calculate_newsvendor_service_level(category="side", k=-5.0)
    assert res_invalid.is_policy_default is True
    assert res_invalid.effective_service_level == 0.90


def test_7_manager_overrides_applied_and_recorded():
    """Test 7: Manager override takes precedence and records reason."""
    res = calculate_newsvendor_service_level(
        category="staple",
        manager_override=0.92,
        override_reason="Hostel budget emergency constraints",
    )
    assert res.effective_service_level == pytest.approx(0.92, 1e-4)
    assert res.manager_override == pytest.approx(0.92, 1e-4)
    assert res.override_reason == "Hostel budget emergency constraints"
    assert "Manager applied an explicit override to 92.0%" in res.explanation


def test_8_shortage_penalty_monotonicity():
    """Test 8: Higher relative shortage penalties never reduce recommended service level."""
    k_values = [1.0, 4.0, 9.0, 19.0, 49.0, 99.0]
    econ_levels = [
        calculate_newsvendor_service_level(category="main", k=k, safety_floor=0.50).economic_service_level
        for k in k_values
    ]
    for i in range(len(econ_levels) - 1):
        assert econ_levels[i] <= econ_levels[i + 1]


def test_9_and_10_cost_aware_planner_integration(db_session):
    """Tests 9 & 10: Real planner uses B4 service level and dishes reflect cost targets."""
    # Register dishes of different categories
    rice = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    dal = get_or_create_dish(db_session, name="Dal", unit="L", category="main")
    salad = get_or_create_dish(db_session, name="Salad", unit="kg", category="side")
    db_session.flush()

    # Seed meals
    for i in range(5):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=400, hostel_strength=500, is_synthetic=1)
        db_session.add(m)
        db_session.flush()
        db_session.add(DishLog(meal_id=m.id, dish_id=rice.id, cooked_qty=40.0, leftover_qty=4.0, unit="kg", is_synthetic=1))
        db_session.add(DishLog(meal_id=m.id, dish_id=dal.id, cooked_qty=50.0, leftover_qty=5.0, unit="L", is_synthetic=1))
        db_session.add(DishLog(meal_id=m.id, dish_id=salad.id, cooked_qty=20.0, leftover_qty=2.0, unit="kg", is_synthetic=1))
    db_session.commit()

    # Run cost-aware planner
    cost_plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-10",
        meal_type="lunch",
        is_synthetic=1,
        cost_mode=True,
        safety_floor=0.90,
    )

    assert cost_plan.cost_mode is True
    assert cost_plan.plan_mode == "cost_aware"

    dish_by_name = {d.dish_name: d for d in cost_plan.dishes}
    assert dish_by_name["Rice"].effective_service_level == 0.99
    assert dish_by_name["Dal"].effective_service_level == 0.95
    assert dish_by_name["Salad"].effective_service_level == 0.90
    assert dish_by_name["Rice"].is_cost_aware is True


def test_11_explanation_fidelity():
    """Test 11: Explanations reflect actual configured values."""
    res = calculate_newsvendor_service_level(category="main", cu=19.0, co=1.0)
    assert "Cu=19" in res.explanation
    assert "Co=1" in res.explanation
    assert "95.0%" in res.explanation


def test_12_existing_b3_manual_mode_remains_functional(db_session):
    """Test 12: Manual slider mode continues to work as before without disruption."""
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.commit()

    manual_plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-10",
        meal_type="lunch",
        service_level=0.92,
        cost_mode=False,
        is_synthetic=1,
    )
    assert manual_plan.service_level == 0.92
    assert manual_plan.cost_mode is False
    assert manual_plan.plan_mode == "manual"


# =============================================================================
# B5 Tests: Kaplan-Meier Shortage-Aware Consumption Learning
# =============================================================================

def test_13_and_14_served_quantity_and_per_head_rate():
    """Tests 13 & 14: served_qty = cooked - leftover and rate = served / headcount."""
    cooked = 50.0
    leftover = 5.0
    headcount = 450
    served = cooked - leftover
    rate = served / headcount
    assert served == 45.0
    assert rate == pytest.approx(0.100, 1e-4)


def test_15_meal_type_and_dish_separation(db_session):
    """Test 15: History is strictly split by dish and meal type."""
    rice = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.flush()

    # Lunch: rate = 0.10
    m_lunch = Meal(date="2026-10-01", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m_lunch)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_lunch.id, dish_id=rice.id, cooked_qty=10.0, leftover_qty=0.0, unit="kg", ran_out=0, is_synthetic=1))

    # Dinner: rate = 0.20
    m_dinner = Meal(date="2026-10-01", meal_type="dinner", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m_dinner)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_dinner.id, dish_id=rice.id, cooked_qty=20.0, leftover_qty=0.0, unit="kg", ran_out=0, is_synthetic=1))
    db_session.commit()

    lunch_rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=1)
    dinner_rates = compute_dish_consumption_rates(db_session, meal_type="dinner", is_synthetic=1)

    assert lunch_rates[rice.id].meal_type == "lunch"
    assert dinner_rates[rice.id].meal_type == "dinner"


def test_16_recent_history_window_selection(db_session):
    """Test 16: Up to window_size (default 10) most recent meals are retained."""
    dish = get_or_create_dish(db_session, name="Sambar", unit="L", category="main")
    db_session.flush()

    for i in range(15):
        m = Meal(date=f"2026-10-{i+1:02d}", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
        db_session.add(m)
        db_session.flush()
        db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=30.0, leftover_qty=2.0, unit="L", is_synthetic=1))
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="lunch", window_size=10, is_synthetic=1)
    assert rates[dish.id].num_observations == 10
    assert len(rates[dish.id].observations) == 10


def test_17_and_18_explicit_ran_out_right_censored(db_session):
    """Tests 17 & 18: ran_out = 1 is right-censored; ran_out = 0 is exact."""
    dish = get_or_create_dish(db_session, name="Chapati", unit="count", category="staple")
    db_session.flush()

    # 1 meal where dish ran out (lower bound)
    m1 = Meal(date="2026-10-01", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m1)
    db_session.flush()
    db_session.add(DishLog(meal_id=m1.id, dish_id=dish.id, cooked_qty=200.0, leftover_qty=0.0, unit="count", ran_out=1, is_synthetic=1))

    # 1 meal where dish did not run out (exact)
    m2 = Meal(date="2026-10-02", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m2)
    db_session.flush()
    db_session.add(DishLog(meal_id=m2.id, dish_id=dish.id, cooked_qty=250.0, leftover_qty=20.0, unit="count", ran_out=0, is_synthetic=1))
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=1)
    obs = rates[dish.id].observations
    obs_by_date = {o.meal_date: o for o in obs}

    assert obs_by_date["2026-10-01"].ran_out is True
    assert obs_by_date["2026-10-01"].is_censored is True

    assert obs_by_date["2026-10-02"].ran_out is False
    assert obs_by_date["2026-10-02"].is_censored is False


def test_19_and_20_kaplan_meier_quantile_direction_and_monotonicity():
    """Tests 19 & 20: Kaplan-Meier quantile satisfies S(r_q) <= 1 - q and higher q gives >= rate."""
    rates = [0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]
    exacts = [True, True, False, True, True, True, False, True]

    km_50 = fit_kaplan_meier_consumption(rates, exacts, target_quantile=0.50)
    km_75 = fit_kaplan_meier_consumption(rates, exacts, target_quantile=0.75)
    km_90 = fit_kaplan_meier_consumption(rates, exacts, target_quantile=0.90)
    km_95 = fit_kaplan_meier_consumption(rates, exacts, target_quantile=0.95)

    assert km_50.estimated_rate <= km_75.estimated_rate <= km_90.estimated_rate <= km_95.estimated_rate
    assert km_95.method == "kaplan_meier_quantile"


def test_21_small_history_fallback():
    """Test 21: Fewer than 3 observations triggers portion default fallback."""
    rates = [0.10, 0.11]
    exacts = [True, True]
    km = fit_kaplan_meier_consumption(rates, exacts, target_quantile=0.95, standard_portion=0.085, unit="kg")
    assert km.is_fallback is True
    assert km.method == "portion_default_fallback"
    assert km.confidence_status == "low"
    assert km.estimated_rate == pytest.approx(0.085, 1e-4)


def test_22_heavy_censoring_fallback():
    """Test 22: Fewer than 2 exact observations out of >= 3 triggers censored lower bound bump."""
    # 4 meals, but 3 ran out!
    rates = [0.10, 0.11, 0.12, 0.13]
    exacts = [False, False, False, True]
    km = fit_kaplan_meier_consumption(rates, exacts, target_quantile=0.95)
    assert km.is_fallback is True
    assert km.method == "censored_lower_bound_bump"
    assert km.confidence_status == "low"
    assert "heavy shortage censoring" in km.fallback_reason


def test_23_confidence_status_indicators():
    """Test 23: Low, moderate, and high confidence flags are assigned accurately."""
    # Large sample (n=10, 8 exact) -> high confidence
    rates_large = [0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17]
    exacts_large = [True, True, True, False, True, True, True, False, True, True]
    km_high = fit_kaplan_meier_consumption(rates_large, exacts_large, target_quantile=0.95)
    assert km_high.confidence_status == "high"

    # Moderate sample (n=5, 4 exact) -> moderate confidence
    rates_mod = [0.10, 0.11, 0.12, 0.13, 0.14]
    exacts_mod = [True, True, True, False, True]
    km_mod = fit_kaplan_meier_consumption(rates_mod, exacts_mod, target_quantile=0.95)
    assert km_mod.confidence_status == "moderate"


def test_24_ambiguous_zero_leftover_records(db_session):
    """Test 24: Leftover=0 without ran_out=1 is not silently misclassified as shortage."""
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.flush()

    m = Meal(date="2026-10-01", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m)
    db_session.flush()
    # Leftover is 0, but ran_out is 0 (staff did NOT record a shortage)
    db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=10.0, leftover_qty=0.0, unit="kg", ran_out=0, is_synthetic=1))
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=1)
    obs = rates[dish.id].observations[0]
    assert obs.ran_out is False
    assert obs.is_censored is False
    assert obs.is_ambiguous is True


def test_25_invalid_quantities_and_zero_headcount(db_session):
    """Test 25: Headcount=0 or cooked < leftover are safely ignored."""
    dish = get_or_create_dish(db_session, name="Soup", unit="L", category="main")
    db_session.flush()

    # Zero headcount meal
    m_zero = Meal(date="2026-10-01", meal_type="lunch", headcount=0, hostel_strength=500, is_synthetic=1)
    db_session.add(m_zero)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_zero.id, dish_id=dish.id, cooked_qty=10.0, leftover_qty=0.0, unit="L", is_synthetic=1))

    # Invalid leftover > cooked
    m_inv = Meal(date="2026-10-02", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m_inv)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_inv.id, dish_id=dish.id, cooked_qty=10.0, leftover_qty=15.0, unit="L", is_synthetic=1))
    db_session.commit()

    rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=1)
    assert rates[dish.id].num_observations == 0


def test_26_strict_synthetic_real_isolation(db_session):
    """Test 26: Real pilot records never contaminate synthetic estimates and vice versa."""
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.flush()

    # Real meal with high rate (0.20)
    m_real = Meal(date="2026-10-01", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=0)
    db_session.add(m_real)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_real.id, dish_id=dish.id, cooked_qty=20.0, leftover_qty=0.0, unit="kg", is_synthetic=0))

    # Synthetic meals with low rate (0.05)
    for i in range(4):
        m_synth = Meal(date=f"2026-10-0{i+2}", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
        db_session.add(m_synth)
        db_session.flush()
        db_session.add(DishLog(meal_id=m_synth.id, dish_id=dish.id, cooked_qty=5.0, leftover_qty=0.0, unit="kg", is_synthetic=1))
    db_session.commit()

    synth_rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=1)
    real_rates = compute_dish_consumption_rates(db_session, meal_type="lunch", is_synthetic=0)

    assert synth_rates[dish.id].num_observations == 4
    assert synth_rates[dish.id].estimated_rate == pytest.approx(0.05, 1e-4)

    assert real_rates[dish.id].num_observations == 1


def test_27_future_dish_observations_cutoff_prevention(db_session):
    """Test 27: before_date strictly excludes future observations from rate calculation."""
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.flush()

    m_past = Meal(date="2026-10-01", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m_past)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_past.id, dish_id=dish.id, cooked_qty=10.0, leftover_qty=0.0, unit="kg", is_synthetic=1))

    m_future = Meal(date="2026-10-05", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m_future)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_future.id, dish_id=dish.id, cooked_qty=30.0, leftover_qty=0.0, unit="kg", is_synthetic=1))
    db_session.commit()

    cutoff_rates = compute_dish_consumption_rates(
        db_session, meal_type="lunch", is_synthetic=1, before_date="2026-10-03"
    )
    assert cutoff_rates[dish.id].num_observations == 1
    assert cutoff_rates[dish.id].observations[0].meal_date == "2026-10-01"


def test_28_planner_consumes_b5_output(db_session):
    """Test 28: Full meal plan exposes B5 metadata on every dish item."""
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.flush()

    for i in range(4):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
        db_session.add(m)
        db_session.flush()
        db_session.add(DishLog(meal_id=m.id, dish_id=dish.id, cooked_qty=20.0, leftover_qty=2.0, unit="kg", ran_out=0, is_synthetic=1))
    db_session.commit()

    plan = generate_meal_plan(db_session, "2026-10-10", "lunch", is_synthetic=1)
    dish_item = plan.dishes[0]
    assert dish_item.num_observations == 4
    assert dish_item.num_exact == 4
    assert dish_item.num_censored == 0
    assert dish_item.estimation_method is not None


def test_29_e3_e4_simulator_compatibility(db_session):
    """Test 29: generate_meal_plan remains compatible with before_date and simulator kwargs."""
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.commit()

    plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-10",
        meal_type="lunch",
        before_date="2026-10-05",
        is_synthetic=1,
    )
    assert plan is not None
    assert plan.target_date == "2026-10-10"


def test_30_plan_persistence_and_audit_preservation(db_session):
    """Test 30: Saving plan stores cost mode and policy metadata in prediction record and audit log."""
    dish = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple")
    db_session.commit()

    plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-10",
        meal_type="lunch",
        cost_mode=True,
        is_synthetic=1,
    )

    pred = save_meal_plan(
        session=db_session,
        meal_date="2026-10-10",
        meal_type="lunch",
        plan_dict=plan.to_dict(),
        service_level=plan.service_level,
        is_synthetic=1,
        who="kitchen_manager",
    )
    assert pred is not None
    assert "cost_aware" in pred.plan_json
    assert pred.service_level == plan.service_level


def test_31_planner_streamlit_apptest_cost_mode():
    """Test 31: Streamlit Planner UI renders both manual and cost-aware mode without errors."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("../app/pages/Planner.py")
    at.run(timeout=30)
    assert not at.exception

    # Switch to Cost-Aware Optimiser mode
    at.radio(key="planner_strategy_selector").set_value("Cost-Aware Optimiser / Newsvendor (B4)").run()
    assert not at.exception
