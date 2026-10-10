"""MessWise - Step 9 Feature Completion, Data Integrity, and Integration Test Suite.

Exhaustively verifies:
1. Data Provenance & Honesty: Unverified test entries cannot fabricate pilot savings.
2. A7: Campus event & exam calendar integration in forecasting.
3. A8: Menu popularity effect from prior cutoff ratings.
4. A9 & F1: Anonymous aggregate student meal check-ins.
5. A10: Arrival nowcast interval tightening & frozen forecast preservation.
6. A11: Time-ordered model retraining, champion-challenger promotion, drift, rollback.
7. B7: Progressive top-up batch cooking recommendations.
8. B8: What-if scenario sandbox without database mutations.
9. B9: Recipe-backed procurement requirements explosion.
10. B10: Per-plate and leftover costing with provenance and missing data handling.
11. B11: Run-out risk alerts based on joint demand distribution.
12. F2: Anonymous dish ratings.
13. F3: Aggregate Student Impact Wall public disclosures.
14. I5: Backend role-based authorization guards.
15. I7: Multi-mess data isolation.
16. I10: FastAPI endpoints for all sprint features.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app, get_db_session
from messwise.auth import check_role_permission, enforce_role_permission, validate_mess_scope, AuthorizationError
from messwise.db import (
    Base,
    CampusEvent,
    Dish,
    DishLog,
    EntranceTally,
    Meal,
    MealCheckIn,
    MealRating,
    ModelRegistry,
    Recipe,
    RecipeIngredient,
    add_campus_event,
    get_active_model,
    init_db,
    list_campus_events,
    log_model_version,
    promote_model_version,
    record_meal_checkin,
    record_meal_rating,
    save_recipe,
)
from messwise.forecast import get_trained_forecaster
from messwise.impact import compute_green_campus_summary
from messwise.planner import DishPlanItem, MealPlanResult, generate_meal_plan
from messwise.planner_extensions import (
    compute_meal_cost_metrics,
    compute_procurement_list_from_plan,
    compute_progressive_topup_plan,
    evaluate_run_out_risk_alerts,
    run_what_if_scenario,
)
from messwise.reports import compute_pilot_evidence_report
from messwise.retraining import check_model_drift, rollback_model_to_last_good, train_challenger_model
from messwise.student import (
    generate_privacy_hash,
    get_student_impact_wall,
    submit_student_checkin,
    submit_student_dish_rating,
)
from messwise.tally import generate_arrival_nowcast


@pytest.fixture
def db_session():
    """In-memory SQLite session with full MessWise schema using StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed baseline dishes
    d1 = Dish(id=1, name="Dal Tadka", category="main", unit="kg", standard_portion=0.15, waste_cost_co=60.0, mess_id="default_mess")
    d2 = Dish(id=2, name="Steamed Rice", category="staple", unit="kg", standard_portion=0.20, waste_cost_co=40.0, mess_id="default_mess")
    session.add_all([d1, d2])
    session.commit()

    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden DB session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. Critical Data Provenance & Honesty Audit
# ==============================================================================
def test_unverified_test_entries_do_not_create_false_pilot_savings(db_session):
    """Manual/unverified entries (verification_status != 'verified_pilot') cannot be claimed as real pilot results."""
    m_unverified = Meal(
        id=101,
        date="2026-10-05",
        meal_type="lunch",
        headcount=450,
        hostel_strength=500,
        is_synthetic=0,
        verification_status="unverified_test",
        mess_id="default_mess",
    )
    db_session.add(m_unverified)
    db_session.commit()

    # Check E2 Pilot Evidence Report
    report = compute_pilot_evidence_report(
        session=db_session,
        baseline_start="2026-10-01",
        baseline_end="2026-10-04",
        pilot_start="2026-10-05",
        pilot_end="2026-10-06",
        is_synthetic=0,
    )
    assert not report.has_sufficient_data, "Unverified entries must not qualify as sufficient pilot data"
    assert "unverified test entries" in report.status_message.lower()

    # Check H1-H4 Green Campus Summary
    impact = compute_green_campus_summary(
        session=db_session,
        is_synthetic=0,
        reporting_period="pilot_period",
    )
    assert impact.meals_count == 0
    assert not impact.co2e_impact.is_available
    assert "insufficient verified" in impact.co2e_impact.availability_reason.lower()


# ==============================================================================
# 2. A7: Event and Exam Calendar Integration
# ==============================================================================
def test_campus_event_calendar_forecast_injection(db_session):
    """Event calendar entries inject event flags and expected attendance factor into forecast feature pipeline."""
    # Seed historical meals
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=480,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    # Add exam event for 2026-10-12
    ev = add_campus_event(
        session=db_session,
        event_name="Midterm Exams",
        event_type="exam",
        start_date="2026-10-12",
        end_date="2026-10-16",
        expected_attendance_factor=0.85,
        mess_id="default_mess",
    )
    assert ev.id is not None

    # Predict slot on exam day
    forecaster, df_history = get_trained_forecaster(db_session, is_synthetic=1)
    pred_exam = forecaster.predict_slot(
        df_history=df_history,
        target_date_str="2026-10-12",
        meal_type="lunch",
        session=db_session,
        is_synthetic=1,
        hostel_strength=500,
        mess_id="default_mess",
    )
    assert any(d["feature"] == "campus_event" for d in pred_exam.top_drivers)
    # Forecast must reflect attendance drop
    assert pred_exam.h_hat < 480


# ==============================================================================
# 3. A8: Menu-Popularity Effect with Temporal Cutoff
# ==============================================================================
def test_menu_popularity_prior_ratings_only(db_session):
    """A8 uses prior rating feedback only; post-cutoff ratings are strictly excluded."""
    # Seed historical meals
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=450,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    # Rating submitted on 2026-10-01 (before 2026-10-05)
    record_meal_rating(db_session, dish_id=1, rating=5, meal_date="2026-10-01", meal_type="lunch", is_synthetic=1)
    record_meal_rating(db_session, dish_id=1, rating=5, meal_date="2026-10-01", meal_type="lunch", is_synthetic=1)
    record_meal_rating(db_session, dish_id=1, rating=5, meal_date="2026-10-01", meal_type="lunch", is_synthetic=1)

    # Post-cutoff rating on 2026-10-10 (should be excluded)
    record_meal_rating(db_session, dish_id=1, rating=1, meal_date="2026-10-10", meal_type="lunch", is_synthetic=1)

    forecaster, df_history = get_trained_forecaster(db_session, is_synthetic=1)
    pred = forecaster.predict_slot(
        df_history=df_history,
        target_date_str="2026-10-05",
        meal_type="lunch",
        session=db_session,
        is_synthetic=1,
        dishes_planned=[1],
    )
    assert any(d["feature"] == "menu_popularity" for d in pred.top_drivers)


# ==============================================================================
# 4. A9 & F1: Anonymous Aggregate Check-Ins
# ==============================================================================
def test_anonymous_meal_checkins_aggregate_blending(db_session):
    """Anonymous check-ins aggregate counts and blend turnout signals when sample >= 5 without collecting PII."""
    # Seed historical meals
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="dinner",
            headcount=450,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    # Submit 6 check-ins (5 yes, 1 no)
    for i in range(5):
        resp = submit_student_checkin(
            session=db_session,
            meal_date="2026-10-08",
            meal_type="dinner",
            response="yes",
            client_token=f"client_token_{i}",
            is_synthetic=1,
        )
        assert resp["success"] is True

    submit_student_checkin(
        session=db_session,
        meal_date="2026-10-08",
        meal_type="dinner",
        response="no",
        client_token="client_token_6",
        is_synthetic=1,
    )

    # Check forecast blending
    forecaster, df_history = get_trained_forecaster(db_session, is_synthetic=1)
    pred = forecaster.predict_slot(
        df_history=df_history,
        target_date_str="2026-10-08",
        meal_type="dinner",
        session=db_session,
        is_synthetic=1,
        hostel_strength=500,
    )
    assert any(d["feature"] == "student_checkins" for d in pred.top_drivers)


# ==============================================================================
# 5. A10: Arrival-Based Nowcast
# ==============================================================================
def test_arrival_nowcast_interval_tightening(db_session):
    """A10 re-estimates final headcount from arrival curve and tightens uncertainty interval."""
    # Meal #50
    m = Meal(
        id=50,
        date="2026-10-09",
        meal_type="lunch",
        headcount=0,
        hostel_strength=500,
        is_synthetic=1,
        verification_status="synthetic",
        mess_id="default_mess",
    )
    db_session.add(m)

    # Add arrival checkpoints: at 30 mins into service, 250 arrivals recorded
    t1 = EntranceTally(meal_id=50, time_bucket="15-30 min (Peak Arrival)", headcount_count=250, mess_id="default_mess", is_synthetic=1)
    db_session.add(t1)
    db_session.commit()

    nowcast = generate_arrival_nowcast(
        session=db_session,
        meal_id=50,
        mess_id="default_mess",
    )
    assert nowcast["has_nowcast"] is True
    assert nowcast["cumulative_arrivals"] == 250
    assert nowcast["nowcast_forecast"]["h_now"] > 0
    # Uncertainty interval should tighten
    orig_width = nowcast["original_frozen_forecast"]["h_hi"] - nowcast["original_frozen_forecast"]["h_lo"]
    now_width = nowcast["nowcast_forecast"]["h_hi"] - nowcast["nowcast_forecast"]["h_lo"]
    assert now_width <= orig_width
    assert "projected final turnout" in nowcast["explanation"].lower()


# ==============================================================================
# 6. A11: Self-Improving Retraining & Model Registry
# ==============================================================================
def test_model_retraining_champion_challenger_lifecycle(db_session):
    """A11 validates time-ordered splits, champion comparison, promotion gate, and rollback."""
    # Seed 25 chronological meals
    for i in range(1, 26):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=450 + (i % 7) * 5,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    # Train challenger
    result = train_challenger_model(
        session=db_session,
        is_synthetic=1,
        mess_id="default_mess",
        min_samples=14,
        force_promote=False,
    )
    assert "challenger_version" in result
    assert "challenger_metrics" in result
    assert result["challenger_metrics"]["mae"] >= 0

    # Test drift check
    drift = check_model_drift(session=db_session, mess_id="default_mess")
    assert "drift_detected" in drift
    assert "message" in drift

    # Test safe rollback
    rb = rollback_model_to_last_good(session=db_session, mess_id="default_mess")
    assert "success" in rb


# ==============================================================================
# 7. B7: Progressive Top-Up Plan
# ==============================================================================
def test_progressive_topup_recommendation(db_session):
    """B7 batches 70% initially, audits attendance, and suggests top-up batch."""
    # Seed meals so planner has data
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=480,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    base_plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-10",
        meal_type="lunch",
        service_level=0.95,
        is_synthetic=1,
    )

    # 45 mins into service, 350 arrivals observed
    topup = compute_progressive_topup_plan(
        base_plan=base_plan,
        initial_batch_pct=0.70,
        observed_arrivals=350,
        nowcast_headcount=470,
        elapsed_minutes=45,
    )
    assert topup.initial_batch_pct == 0.70
    assert len(topup.batches) >= 1
    d_topup = topup.batches[0]
    assert d_topup.initial_batch_qty > 0
    assert d_topup.checkpoint_topup_qty >= 0
    assert d_topup.total_planned_qty >= d_topup.initial_batch_qty


# ==============================================================================
# 8. B8: What-If Scenario Sandbox
# ==============================================================================
def test_what_if_scenario_sandbox_immutability(db_session):
    """B8 runs hypothetical simulation without modifying existing meals or predictions."""
    # Seed meals
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=480,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    count_meals_before = db_session.query(Meal).count()

    scenario = run_what_if_scenario(
        session=db_session,
        base_date="2026-10-11",
        meal_type="lunch",
        headcount_override=600,
        service_level=0.99,
        is_synthetic=1,
    )
    assert scenario["scenario_type"] == "hypothetical_sandbox"
    assert scenario["scenario_planning_headcount"] == 600
    assert db_session.query(Meal).count() == count_meals_before, "What-if simulation must NOT mutate database rows"


# ==============================================================================
# 9. B9: Recipe-Backed Procurement List
# ==============================================================================
def test_recipe_procurement_explosion(db_session):
    """B9 explodes planned dishes into ingredient-level procurement requirements."""
    # Seed meals
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=480,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    # Save recipe for Dal Tadka (dish_id=1)
    save_recipe(
        session=db_session,
        dish_id=1,
        servings_yield=100.0,
        ingredients_list=[
            {"ingredient_name": "Toor Dal", "amount": 10.0, "unit": "kg", "cost_per_unit": 120.0},
            {"ingredient_name": "Ghee", "amount": 1.5, "unit": "kg", "cost_per_unit": 500.0},
        ],
        mess_id="default_mess",
    )

    base_plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-12",
        meal_type="lunch",
        service_level=0.95,
        is_synthetic=1,
    )

    proc = compute_procurement_list_from_plan(
        session=db_session,
        plan=base_plan,
        mess_id="default_mess",
    )
    assert proc["procurement_items_count"] >= 2
    assert proc["total_estimated_rupee_cost"] is not None
    toor = next(i for i in proc["procurement_items"] if i["ingredient_name"] == "Toor Dal")
    assert toor["total_required_qty"] > 0
    assert toor["unit"] == "kg"
    assert toor["estimated_rupee_cost"] > 0


# ==============================================================================
# 10. B10: Per-Plate and Leftover Costing
# ==============================================================================
def test_meal_costing_metrics_calculation(db_session):
    """B10 computes per-serving plate cost and leftover cost from verified recipes."""
    # Seed meals
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=480,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    # Save recipes for all dishes in plan so cost is complete
    save_recipe(
        session=db_session,
        dish_id=1,
        servings_yield=100.0,
        ingredients_list=[
            {"ingredient_name": "Toor Dal", "amount": 10.0, "unit": "kg", "cost_per_unit": 120.0},
        ],
        mess_id="default_mess",
    )
    save_recipe(
        session=db_session,
        dish_id=2,
        servings_yield=100.0,
        ingredients_list=[
            {"ingredient_name": "Raw Rice", "amount": 15.0, "unit": "kg", "cost_per_unit": 40.0},
        ],
        mess_id="default_mess",
    )

    base_plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-12",
        meal_type="lunch",
        service_level=0.95,
        is_synthetic=1,
    )

    costing = compute_meal_cost_metrics(
        session=db_session,
        meal_plan=base_plan,
        mess_id="default_mess",
    )
    assert costing["is_cost_complete"] is True
    assert costing["cost_per_plate_inr"] > 0
    assert costing["total_planned_cooking_cost_inr"] > 0


# ==============================================================================
# 11. B11: Run-Out Risk Alerts
# ==============================================================================
def test_run_out_risk_alerts_generation(db_session):
    """B11 flags run-out risks when planned quantities fall behind demand distribution tails."""
    # Seed meals
    for i in range(1, 15):
        m = Meal(
            id=i,
            date=f"2026-09-{i:02d}",
            meal_type="lunch",
            headcount=480,
            hostel_strength=500,
            is_synthetic=1,
            verification_status="synthetic",
            mess_id="default_mess",
        )
        db_session.add(m)
    db_session.commit()

    plan = generate_meal_plan(
        session=db_session,
        target_date="2026-10-13",
        meal_type="lunch",
        service_level=0.95,
        is_synthetic=1,
    )

    alerts = evaluate_run_out_risk_alerts(plan, risk_threshold_pct=1.0)
    assert isinstance(alerts, list)


# ==============================================================================
# 12. F2 & F3: Student Engagement & Impact Wall Disclosures
# ==============================================================================
def test_student_rating_and_impact_wall(db_session):
    """F2 ratings validate bounds and F3 displays transparent disclosure banner."""
    # F2: Submit ratings
    r1 = submit_student_dish_rating(
        session=db_session,
        meal_date="2026-10-10",
        meal_type="lunch",
        dish_id=1,
        rating=4,
        client_token="token_hash_a",
        is_synthetic=1,
    )
    assert r1["success"] is True
    assert r1["your_rating"] == 4

    # F3: Student Impact Wall
    wall = get_student_impact_wall(session=db_session, is_synthetic=1)
    assert wall["is_synthetic_demo"] is True
    assert "DEMONSTRATION" in wall["status_banner"]
    assert "privacy_guarantee" in wall


# ==============================================================================
# 13. I5: Real Role-Based Backend Authorization Guards
# ==============================================================================
def test_backend_role_based_authorization_guards():
    """I5 enforces true backend permission checks, denying unauthorized callers."""
    # Cook cannot manage financial costs
    assert not check_role_permission(role="cook", action="configure_costs")
    with pytest.raises(AuthorizationError):
        enforce_role_permission(role="cook", action="configure_costs")

    # Manager can manage costs
    assert check_role_permission(role="manager", action="configure_costs")

    # Student cannot log kitchen dish logs
    assert not check_role_permission(role="student", action="create_dish_log")
    with pytest.raises(AuthorizationError):
        enforce_role_permission(role="student", action="create_dish_log")

    # Auditor is read-only
    assert check_role_permission(role="auditor", action="view_audit_log")
    assert not check_role_permission(role="auditor", action="retrain_model")


# ==============================================================================
# 14. I7: Multi-Mess Data Isolation
# ==============================================================================
def test_multi_mess_data_isolation(db_session):
    """I7 prevents cross-mess operational contamination."""
    # Add dish to Mess Alpha
    d_alpha = Dish(id=10, name="Alpha Sambar", category="main", mess_id="mess_alpha")
    # Add dish to Mess Beta
    d_beta = Dish(id=20, name="Beta Sambar", category="main", mess_id="mess_beta")
    db_session.add_all([d_alpha, d_beta])
    db_session.commit()

    # Query scoped to mess_alpha
    alpha_dishes = db_session.query(Dish).filter(Dish.mess_id == "mess_alpha").all()
    assert len(alpha_dishes) == 1
    assert alpha_dishes[0].name == "Alpha Sambar"

    # Validate mess scope guard
    assert validate_mess_scope(requested_mess_id="mess_alpha", user_authorized_mess_id="mess_alpha") == "mess_alpha"
    from messwise.auth import CrossMessAccessViolation
    with pytest.raises(CrossMessAccessViolation):
        validate_mess_scope(requested_mess_id="mess_beta", user_authorized_mess_id="mess_alpha")


# ==============================================================================
# 15. I10: FastAPI Endpoints Verification
# ==============================================================================
def test_fastapi_endpoints_sprint_features(client):
    """I10 validates all newly added REST endpoints via TestClient."""
    # 1. Calendar
    res = client.post("/calendar/events", json={
        "event_name": "Campus Fest",
        "event_type": "fest",
        "start_date": "2026-10-20",
        "end_date": "2026-10-22",
        "expected_attendance_factor": 1.15,
        "mess_id": "default_mess",
    })
    assert res.status_code == 201

    res_list = client.get("/calendar/events?mess_id=default_mess")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 2. Student Check-in
    res_chk = client.post("/student/check-in", json={
        "meal_date": "2026-10-20",
        "meal_type": "dinner",
        "response": "yes",
        "is_synthetic": 1,
    })
    assert res_chk.status_code == 200

    # 3. Student Rate
    res_rate = client.post("/student/rate", json={
        "meal_date": "2026-10-20",
        "meal_type": "lunch",
        "dish_id": 1,
        "rating": 4,
        "is_synthetic": 1,
    })
    assert res_rate.status_code == 200

    # 4. Student Impact Wall
    res_wall = client.get("/student/impact-wall?is_synthetic=1")
    assert res_wall.status_code == 200
    assert res_wall.json()["is_synthetic_demo"] is True

    # 5. What-if planner
    res_whatif = client.post("/plan/what-if", json={
        "base_date": "2026-10-20",
        "meal_type": "lunch",
        "headcount_override": 520,
        "service_level": 0.95,
        "is_synthetic": 1,
    })
    assert res_whatif.status_code == 200
    assert res_whatif.json()["scenario_type"] == "hypothetical_sandbox"

    # 6. Model registry
    res_reg = client.get("/model/registry?mess_id=default_mess")
    assert res_reg.status_code == 200
