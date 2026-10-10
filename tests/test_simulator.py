"""Tests for Step 5: Savings Simulator (E3) and Blind Forecast Reveal (E4).

Validates all 24 required points from PLAN.md and Step 5 specification:
1. Historical replay uses only prior information (no look-ahead).
2. Future meal outcomes do not leak into forecasting.
3. Replay handles insufficient training history (<3 meals excluded).
4. Synthetic and real records remain strictly isolated.
5. Compatible unit comparison (kg, L, count separated).
6. Incompatible units are not combined.
7. Potential quantity reduction is calculated correctly.
8. Potential reduction is not mislabeled as verified savings.
9. Cost output is unavailable when prices are missing (no invented rupees).
10. Shortage events use actual recorded evidence (ran_out == 1).
11. Blind forecasts freeze before outcome reveal.
12. Actual outcomes are hidden before reveal (None / False).
13. Reveal compares against frozen prediction rather than regenerating it.
14. Forecast error and absolute error are correct.
15. Prediction interval coverage is evaluated correctly.
16. Missing actual outcomes / ineligible meals are handled safely.
17. Invalid input is rejected (FastAPI 422).
18. API simulator endpoint (/simulate) works.
19. API blind-reveal workflow (/simulate/blind-reveal) works.
20. Synthetic demo outputs are clearly labelled.
21. Zero real pilot records never produce real-world impact claims.
22. Existing saved predictions remain unchanged.
23. Existing audit-log behaviour is preserved.
24. Streamlit Simulator page runs cleanly without exceptions.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app, get_db_session
from messwise.db import (
    Base,
    Dish,
    DishLog,
    Meal,
    Prediction,
    AuditLog,
    get_or_create_dish,
)
from messwise.simulator import (
    run_savings_simulation,
    generate_blind_forecast,
    reveal_blind_forecast,
    get_pre_cutoff_meals_dataframe,
    MIN_PRE_CUTOFF_MEALS,
)


@pytest.fixture
def db_session():
    """Create a completely isolated, in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client overriding get_db_session dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_test_history(db_session, is_synthetic: int = 1, count: int = 6):
    """Helper to seed clean sequential test meals and dish logs."""
    dish_rice = get_or_create_dish(db_session, name="Rice", unit="kg", category="staple", is_synthetic=is_synthetic)
    dish_dal = get_or_create_dish(db_session, name="Dal", unit="L", category="main", is_synthetic=is_synthetic)
    dish_egg = get_or_create_dish(db_session, name="Egg", unit="count", category="side", is_synthetic=is_synthetic)
    db_session.flush()

    meals = []
    for i in range(count):
        date_str = f"2026-10-{i+1:02d}"
        hc = 200 + (i * 10)
        m = Meal(
            date=date_str,
            meal_type="lunch",
            headcount=hc,
            hostel_strength=500,
            event_flag=0,
            exam_flag=0,
            holiday_flag=0,
            is_synthetic=is_synthetic,
        )
        db_session.add(m)
        db_session.flush()

        # Seed dish logs with compatible units
        db_session.add(DishLog(meal_id=m.id, dish_id=dish_rice.id, cooked_qty=25.0, leftover_qty=3.0, unit="kg", ran_out=0, is_synthetic=is_synthetic))
        db_session.add(DishLog(meal_id=m.id, dish_id=dish_dal.id, cooked_qty=30.0, leftover_qty=2.0, unit="L", ran_out=0, is_synthetic=is_synthetic))
        # Day 5 runs out of eggs
        ran_out_egg = 1 if i == 4 else 0
        db_session.add(DishLog(meal_id=m.id, dish_id=dish_egg.id, cooked_qty=200.0, leftover_qty=0.0 if ran_out_egg else 10.0, unit="count", ran_out=ran_out_egg, is_synthetic=is_synthetic))
        meals.append(m)

    db_session.commit()
    return meals, [dish_rice, dish_dal, dish_egg]


# -----------------------------------------------------------------------------
# 1 & 2. Leakage Prevention Tests
# -----------------------------------------------------------------------------

def test_historical_replay_uses_only_prior_information(db_session):
    """Verify pre-cutoff DataFrame strictly excludes the target meal and subsequent meals."""
    meals, _ = seed_test_history(db_session, is_synthetic=1, count=5)
    target = meals[3]  # Meal #4 on 2026-10-04

    df_pre = get_pre_cutoff_meals_dataframe(
        session=db_session,
        target_date=target.date,
        target_meal_id=target.id,
        is_synthetic=1,
    )

    # Must contain only earlier meals (id < target.id, date < target.date)
    assert len(df_pre) == 3
    pre_ids = list(df_pre["id"])
    assert target.id not in pre_ids
    assert meals[4].id not in pre_ids
    assert all(d < target.date for d in df_pre["date"])


def test_future_meal_outcomes_do_not_leak_into_forecasting(db_session):
    """Adding an extreme future meal must NOT change the forecast or plan for a prior meal."""
    meals, _ = seed_test_history(db_session, is_synthetic=1, count=4)
    target = meals[3]  # 4th meal

    # Generate blind forecast with only 4 meals in DB
    forecast_before = generate_blind_forecast(db_session, meal_id=target.id, service_level=0.95)
    h_hat_before = forecast_before.h_hat
    plan_before = forecast_before.planned_dishes[0]["planned_cooking_qty"]

    # Now insert a wild future meal on 2026-10-10 with 500 headcount and massive cooked quantities
    future_m = Meal(date="2026-10-10", meal_type="lunch", headcount=500, hostel_strength=500, is_synthetic=1)
    db_session.add(future_m)
    db_session.flush()
    db_session.add(DishLog(meal_id=future_m.id, dish_id=1, cooked_qty=100.0, leftover_qty=0.0, unit="kg", is_synthetic=1))
    db_session.commit()

    # Re-generate blind forecast for target meal
    forecast_after = generate_blind_forecast(db_session, meal_id=target.id, service_level=0.95)
    
    # Must be 100% strictly identical
    assert forecast_after.h_hat == h_hat_before
    assert forecast_after.planned_dishes[0]["planned_cooking_qty"] == plan_before


# -----------------------------------------------------------------------------
# 3. Insufficient History Exclusion
# -----------------------------------------------------------------------------

def test_insufficient_training_history_exclusion(db_session):
    """Meals with < MIN_PRE_CUTOFF_MEALS prior history must be excluded from evaluation."""
    meals, _ = seed_test_history(db_session, is_synthetic=1, count=4)
    
    report = run_savings_simulation(db_session, is_synthetic=1)
    assert report.total_meals_replayed == 4
    # The first 3 meals have 0, 1, 2 pre-cutoff meals -> excluded
    assert report.meals_excluded == 3
    # Only the 4th meal has 3 pre-cutoff meals -> evaluable
    assert report.meals_evaluable == 1
    
    first_meal_res = report.replayed_meals[0]
    assert first_meal_res.is_evaluable is False
    assert "Insufficient pre-cutoff history" in first_meal_res.exclusion_reason


# -----------------------------------------------------------------------------
# 4. Synthetic vs Real Isolation
# -----------------------------------------------------------------------------

def test_synthetic_and_real_records_isolation(db_session):
    """Synthetic queries must not touch real records, and real queries must not touch synthetic."""
    seed_test_history(db_session, is_synthetic=1, count=5)  # 5 synthetic meals
    
    # Run simulation for real environment (which has 0 meals)
    real_report = run_savings_simulation(db_session, is_synthetic=0)
    assert real_report.has_sufficient_data is False
    assert real_report.total_meals_replayed == 0
    assert real_report.meals_evaluable == 0
    assert "INSUFFICIENT REAL PILOT DATA" in real_report.candor_disclosures[0]

    # Run simulation for synthetic environment
    synth_report = run_savings_simulation(db_session, is_synthetic=1)
    assert synth_report.has_sufficient_data is True
    assert synth_report.total_meals_replayed == 5
    assert "SYNTHETIC DEMONSTRATION" in synth_report.candor_disclosures[0]


# -----------------------------------------------------------------------------
# 5 & 6. Unit Separation & Incompatible Unit Protection
# -----------------------------------------------------------------------------

def test_compatible_unit_comparison_and_separation(db_session):
    """Verify kg, L, and count are tracked separately and never aggregated into a single sum."""
    seed_test_history(db_session, is_synthetic=1, count=5)
    report = run_savings_simulation(db_session, is_synthetic=1)

    assert "kg" in report.totals_by_unit
    assert "L" in report.totals_by_unit
    assert "count" in report.totals_by_unit

    # Check that counts (hundreds of eggs) are not summed into kilograms
    kg_cooked = report.totals_by_unit["kg"]["actual_cooked"]
    count_cooked = report.totals_by_unit["count"]["actual_cooked"]
    assert count_cooked > 300
    assert kg_cooked < 100


# -----------------------------------------------------------------------------
# 7, 8 & 9. Potential Reduction vs Verified Savings & Missing Price Candor
# -----------------------------------------------------------------------------

def test_potential_quantity_reduction_and_missing_cost_notice(db_session):
    """Verify potential reduction is calculated and cost estimation reports unavailable."""
    seed_test_history(db_session, is_synthetic=1, count=5)
    report = run_savings_simulation(db_session, is_synthetic=1)

    # Reduction is calculated
    for unit, stats in report.totals_by_unit.items():
        assert "potential_reduction" in stats
        # Theoretical delta: actual_cooked - simulated_recommended
        expected_diff = round(stats["actual_cooked"] - stats["simulated_recommended"], 2)
        assert stats["potential_reduction"] == pytest.approx(expected_diff, 1e-2)

    # Cost estimation MUST report unavailable — no invented rupees!
    assert report.cost_savings_rupees is None
    assert "Cost estimation unavailable — valid ingredient prices are not configured." in report.cost_status_message
    assert any("must NOT be interpreted as verified physical savings" in d for d in report.candor_disclosures)


# -----------------------------------------------------------------------------
# 10. Actual Shortage Evidence & Right-Censoring
# -----------------------------------------------------------------------------

def test_shortage_events_recorded_evidence(db_session):
    """Verify actual recorded ran_out == 1 is reported as an actual shortage event."""
    seed_test_history(db_session, is_synthetic=1, count=5)  # 5th meal has ran_out=1 for eggs
    report = run_savings_simulation(db_session, is_synthetic=1)

    assert report.actual_shortage_events_count == 1
    evaluable_meal = next(m for m in report.replayed_meals if m.meal_id == 5)
    assert evaluable_meal.actual_shortage_event is True

    ran_out_dish = next(d for d in evaluable_meal.dish_comparisons if d.dish_name == "Egg")
    assert ran_out_dish.actual_ran_out is True
    assert "right-censored" in ran_out_dish.limitation_note.lower()


# -----------------------------------------------------------------------------
# 11, 12 & 13. Blind Forecast Freeze and Reveal Invariance
# -----------------------------------------------------------------------------

def test_blind_forecast_freeze_and_reveal_invariance(db_session):
    """Test two-stage reveal workflow: freeze hides outcomes, reveal retains frozen plan."""
    meals, _ = seed_test_history(db_session, is_synthetic=1, count=5)
    target = meals[4]

    # Stage 2: Generate and freeze blind forecast
    blind = generate_blind_forecast(db_session, meal_id=target.id, service_level=0.95)
    assert blind.is_eligible is True
    assert blind.is_revealed is False
    assert blind.actual_headcount is None
    assert blind.forecast_error is None
    assert blind.abs_forecast_error is None
    assert blind.inside_interval is None

    frozen_h_hat = blind.h_hat
    frozen_h_lo = blind.h_lo
    frozen_h_hi = blind.h_hi
    frozen_plan_qty = blind.planned_dishes[0]["planned_cooking_qty"]

    # Stage 3: Reveal actual outcome
    revealed = reveal_blind_forecast(db_session, frozen_state=blind)
    assert revealed.is_revealed is True
    assert revealed.actual_headcount == target.headcount
    assert revealed.forecast_error == (frozen_h_hat - target.headcount)
    assert revealed.abs_forecast_error == abs(frozen_h_hat - target.headcount)
    assert revealed.inside_interval == (frozen_h_lo <= target.headcount <= frozen_h_hi)

    # Invariance check: frozen prediction MUST NOT have changed
    assert revealed.h_hat == frozen_h_hat
    assert revealed.h_lo == frozen_h_lo
    assert revealed.h_hi == frozen_h_hi
    assert revealed.planned_dishes[0]["planned_cooking_qty"] == frozen_plan_qty


# -----------------------------------------------------------------------------
# 16 & 17. Missing and Ineligible Meals Handled Safely
# -----------------------------------------------------------------------------

def test_missing_or_ineligible_meals_handled_safely(db_session):
    """Test non-existent meal and cold-start meal handling."""
    # Non-existent meal
    missing_blind = generate_blind_forecast(db_session, meal_id=9999)
    assert missing_blind.is_eligible is False
    assert "not found" in missing_blind.ineligibility_reason.lower()

    # Meal with 0 prior history (Day 1)
    meals, _ = seed_test_history(db_session, is_synthetic=1, count=2)
    cold_blind = generate_blind_forecast(db_session, meal_id=meals[0].id)
    assert cold_blind.is_eligible is False
    assert "insufficient prior history" in cold_blind.ineligibility_reason.lower()


# -----------------------------------------------------------------------------
# 18 & 19. FastAPI Simulator Endpoints
# -----------------------------------------------------------------------------

def test_fastapi_simulator_endpoints(client, db_session):
    """Verify /simulate, /simulate/blind-forecast, and /simulate/blind-reveal endpoints."""
    meals, _ = seed_test_history(db_session, is_synthetic=1, count=5)
    target_id = meals[4].id

    # POST /simulate
    sim_resp = client.post(
        "/simulate",
        json={"is_synthetic": 1, "service_level": 0.95, "hostel_strength": 500},
    )
    assert sim_resp.status_code == 200
    report = sim_resp.json()["report"]
    assert report["total_meals_replayed"] == 5
    assert report["meals_evaluable"] == 2
    assert report["cost_savings_rupees"] is None

    # POST /simulate/blind-forecast
    blind_resp = client.post(
        "/simulate/blind-forecast",
        json={"meal_id": target_id, "service_level": 0.95, "hostel_strength": 500},
    )
    assert blind_resp.status_code == 200
    blind_data = blind_resp.json()["blind_state"]
    assert blind_data["is_revealed"] is False
    assert blind_data["actual_headcount"] is None

    # POST /simulate/blind-reveal
    reveal_resp = client.post(
        "/simulate/blind-reveal",
        json={"meal_id": target_id, "service_level": 0.95, "hostel_strength": 500},
    )
    assert reveal_resp.status_code == 200
    reveal_data = reveal_resp.json()["revealed_state"]
    assert reveal_data["is_revealed"] is True
    assert reveal_data["actual_headcount"] is not None
    assert reveal_data["abs_forecast_error"] is not None

    # Invalid input rejection (422)
    bad_resp = client.post("/simulate", json={"service_level": 1.5})
    assert bad_resp.status_code == 422


# -----------------------------------------------------------------------------
# 20 & 21. Data Honesty & Zero Real Pilot Safeguard
# -----------------------------------------------------------------------------

def test_zero_real_records_never_claim_impact(db_session):
    """Verify 0 real records yields explicit insufficiency warning, never claiming savings."""
    report = run_savings_simulation(db_session, is_synthetic=0)
    assert report.has_sufficient_data is False
    assert report.total_meals_replayed == 0
    assert report.meals_evaluable == 0
    assert "INSUFFICIENT REAL PILOT DATA" in report.candor_disclosures[0]


# -----------------------------------------------------------------------------
# 22 & 23. Existing Predictions and Audit Logs Preserved
# -----------------------------------------------------------------------------

def test_existing_predictions_and_audit_logs_unaltered(db_session):
    """Verify simulator queries do not corrupt or delete existing Prediction or AuditLog rows."""
    p = Prediction(
        meal_date="2026-10-15",
        meal_type="lunch",
        h_hat=250.0,
        h_lo=220.0,
        h_hi=280.0,
        status="pending",
        is_synthetic=1,
    )
    db_session.add(p)
    audit = AuditLog(who="system", action="test", old_value="initial", new_value="preserving check")
    db_session.add(audit)
    db_session.commit()

    # Run replay
    run_savings_simulation(db_session, is_synthetic=1)

    # Check persistence
    p_check = db_session.execute(select(Prediction).where(Prediction.id == p.id)).scalar_one()
    audit_check = db_session.execute(select(AuditLog).where(AuditLog.id == audit.id)).scalar_one()
    assert p_check.h_hat == 250.0
    assert audit_check.new_value == "preserving check"


def test_streamlit_simulator_apptest():
    """Verify Streamlit Simulator page loads, generates blind forecast, reveals, and replays without exceptions."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    sim_page = Path(__file__).parent.parent / "app" / "pages" / "Simulator.py"
    at = AppTest.from_file(str(sim_page), default_timeout=30)
    at.run()

    # Must run without any red Streamlit exceptions
    assert not at.exception
    assert len(at.tabs) == 2

    # Click Generate Blind Forecast button — regression check for TypeError
    btn_blind = next((b for b in at.button if b.key == "btn_gen_blind"), None)
    assert btn_blind is not None
    btn_blind.click().run()
    assert not at.exception, "Exception occurred upon clicking Generate Blind Forecast!"

    # Click Reveal button
    btn_reveal = next((b for b in at.button if b.key == "btn_reveal"), None)
    assert btn_reveal is not None
    btn_reveal.click().run()
    assert not at.exception, "Exception occurred upon clicking Reveal Actual Outcome!"

    # Click Run Simulation button
    btn_sim = next((b for b in at.button if b.key == "btn_run_sim"), None)
    assert btn_sim is not None
    btn_sim.click().run()
    assert not at.exception, "Exception occurred upon clicking Run Historical Savings Replay!"


def test_generate_meal_plan_cutoff_arguments_compatibility(db_session):
    """Regression test: verify generate_meal_plan directly accepts before_date and before_meal_id."""
    from messwise.planner import generate_meal_plan

    meals, _ = seed_test_history(db_session, is_synthetic=1, count=5)
    target = meals[4]

    # Call with before_date and before_meal_id directly
    plan = generate_meal_plan(
        session=db_session,
        target_date=target.date,
        meal_type=target.meal_type,
        service_level=0.95,
        is_synthetic=1,
        before_date=target.date,
        before_meal_id=target.id,
    )
    assert plan is not None
    assert plan.target_date == target.date
    assert len(plan.dishes) > 0


def test_future_dish_logs_do_not_leak_into_consumption_rates(db_session):
    """Verify future dish consumption does not affect historical learned rates."""
    from messwise.planner import compute_dish_consumption_rates

    meals, dishes = seed_test_history(db_session, is_synthetic=1, count=4)
    target_date = "2026-10-04"

    rates_before = compute_dish_consumption_rates(
        session=db_session,
        meal_type="lunch",
        is_synthetic=1,
        before_date=target_date,
    )
    rice_rate_before = rates_before[dishes[0].id].estimated_rate

    # Insert a future dish log on 2026-10-10 with massive consumption (10x rate)
    m_future = Meal(date="2026-10-10", meal_type="lunch", headcount=100, hostel_strength=500, is_synthetic=1)
    db_session.add(m_future)
    db_session.flush()
    db_session.add(DishLog(meal_id=m_future.id, dish_id=dishes[0].id, cooked_qty=100.0, leftover_qty=0.0, unit="kg", is_synthetic=1))
    db_session.commit()

    # Re-compute rates with cutoff at target_date
    rates_after = compute_dish_consumption_rates(
        session=db_session,
        meal_type="lunch",
        is_synthetic=1,
        before_date=target_date,
    )
    rice_rate_after = rates_after[dishes[0].id].estimated_rate

    # Must be completely identical
    assert rice_rate_after == rice_rate_before

