"""Tests for MessWise Waste Intelligence Engine (Module D: D1-D3).

Verifies:
- D1: KPI formulas, zero cooked-quantity handling, empty datasets, date/environment filtering
- D2: Aggregations by weekday, meal type, dish, and chronological trend series
- D3: Dish performance rankings, low-observation handling, operational suggestions
- Strict synthetic vs real isolation
- No fabricated costs or popularity ratings
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from messwise.db import Dish, DishLog, Meal, get_or_create_dish, init_db
from messwise.intelligence import (
    aggregate_waste_by_dish,
    aggregate_waste_by_meal_type,
    aggregate_waste_by_weekday,
    aggregate_waste_trends,
    compute_dish_performance_rankings,
    compute_kpi_summary,
)


@pytest.fixture
def memory_db():
    """Provides isolated in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_d1_kpi_empty_database(memory_db):
    """Verify D1 KPI calculations handle empty datasets gracefully without division-by-zero."""
    kpis = compute_kpi_summary(session=memory_db, is_synthetic=1)
    assert kpis.total_meals_count == 0
    assert kpis.total_leftover_kg == 0.0
    assert kpis.total_cooked_kg == 0.0
    assert kpis.waste_percentage == 0.0
    assert kpis.service_level_achieved == 1.0
    assert kpis.shortage_incidents_count == 0
    assert kpis.cost_estimate_rupees is None
    assert "unavailable" in kpis.cost_status_note.lower()


def test_d1_kpi_formula_and_zero_cooked_handling(memory_db):
    """Verify exact formula (leftover / cooked * 100) and zero cooked quantity edge case."""
    d = get_or_create_dish(memory_db, name="Dal", unit="L", category="main")
    m = Meal(date="2026-10-01", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
    memory_db.add(m)
    memory_db.flush()

    # Normal entry: 50L cooked, 5L leftover -> 10.0%
    log = DishLog(meal_id=m.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=5.0, unit="L", is_synthetic=1)
    memory_db.add(log)
    memory_db.commit()

    kpis = compute_kpi_summary(session=memory_db, is_synthetic=1)
    assert kpis.total_meals_count == 1
    assert kpis.total_headcount_served == 200
    assert kpis.total_cooked_kg == 50.0
    assert kpis.total_leftover_kg == 5.0
    assert kpis.waste_percentage == 10.0
    assert kpis.service_level_achieved == 1.0


def test_d1_kpi_shortage_service_level(memory_db):
    """Verify service level formula: 1 - (shortages / total logs)."""
    d1 = get_or_create_dish(memory_db, name="Rice", unit="kg", category="staple")
    d2 = get_or_create_dish(memory_db, name="Sambar", unit="L", category="main")
    m = Meal(date="2026-10-02", meal_type="dinner", headcount=300, hostel_strength=500, is_synthetic=1)
    memory_db.add(m)
    memory_db.flush()

    # 1 normal, 1 shortage (ran_out=1) -> 50% service level
    memory_db.add(DishLog(meal_id=m.id, dish_id=d1.id, cooked_qty=40.0, leftover_qty=4.0, unit="kg", ran_out=0, is_synthetic=1))
    memory_db.add(DishLog(meal_id=m.id, dish_id=d2.id, cooked_qty=30.0, leftover_qty=0.0, unit="L", ran_out=1, is_synthetic=1))
    memory_db.commit()

    kpis = compute_kpi_summary(session=memory_db, is_synthetic=1)
    assert kpis.shortage_incidents_count == 1
    assert kpis.total_dish_logs_count == 2
    assert kpis.service_level_achieved == 0.5


def test_d1_environment_isolation(memory_db):
    """Verify synthetic (1) vs real (0) isolation in KPIs."""
    d = get_or_create_dish(memory_db, name="Puri", unit="count", category="staple")
    m_real = Meal(date="2026-10-01", meal_type="breakfast", headcount=100, hostel_strength=500, is_synthetic=0)
    m_synth = Meal(date="2026-10-02", meal_type="breakfast", headcount=150, hostel_strength=500, is_synthetic=1)
    memory_db.add_all([m_real, m_synth])
    memory_db.flush()

    memory_db.add(DishLog(meal_id=m_real.id, dish_id=d.id, cooked_qty=200.0, leftover_qty=10.0, unit="count", is_synthetic=0))
    memory_db.add(DishLog(meal_id=m_synth.id, dish_id=d.id, cooked_qty=300.0, leftover_qty=30.0, unit="count", is_synthetic=1))
    memory_db.commit()

    kpi_real = compute_kpi_summary(session=memory_db, is_synthetic=0)
    kpi_synth = compute_kpi_summary(session=memory_db, is_synthetic=1)

    assert kpi_real.total_meals_count == 1
    assert kpi_real.total_headcount_served == 100

    assert kpi_synth.total_meals_count == 1
    assert kpi_synth.total_headcount_served == 150


def test_d2_waste_by_weekday_and_meal_type(memory_db):
    """Verify D2 aggregations correctly bucket records by weekday and meal slot."""
    d = get_or_create_dish(memory_db, name="Biryani", unit="kg", category="main")
    # 2026-10-05 was Monday, 2026-10-06 was Tuesday
    m_mon = Meal(date="2026-10-05", meal_type="lunch", headcount=250, hostel_strength=500, is_synthetic=1)
    m_tue = Meal(date="2026-10-06", meal_type="dinner", headcount=240, hostel_strength=500, is_synthetic=1)
    memory_db.add_all([m_mon, m_tue])
    memory_db.flush()

    memory_db.add(DishLog(meal_id=m_mon.id, dish_id=d.id, cooked_qty=50.0, leftover_qty=5.0, unit="kg", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m_tue.id, dish_id=d.id, cooked_qty=60.0, leftover_qty=12.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    df_week = aggregate_waste_by_weekday(session=memory_db, is_synthetic=1)
    mon_row = df_week[df_week["weekday_name"] == "Monday"].iloc[0]
    tue_row = df_week[df_week["weekday_name"] == "Tuesday"].iloc[0]

    assert mon_row["leftover_kg"] == 5.0
    assert mon_row["waste_pct"] == 10.0
    assert tue_row["leftover_kg"] == 12.0
    assert tue_row["waste_pct"] == 20.0

    df_slot = aggregate_waste_by_meal_type(session=memory_db, is_synthetic=1)
    lunch_row = df_slot[df_slot["meal_type"] == "Lunch"].iloc[0]
    dinner_row = df_slot[df_slot["meal_type"] == "Dinner"].iloc[0]

    assert lunch_row["leftover_kg"] == 5.0
    assert dinner_row["leftover_kg"] == 12.0


def test_d2_waste_by_dish_and_trends(memory_db):
    """Verify D2 dish ranking breakdown and chronological trend series."""
    d1 = get_or_create_dish(memory_db, name="Rice", unit="kg", category="staple")
    d2 = get_or_create_dish(memory_db, name="Curry", unit="kg", category="main")
    m = Meal(date="2026-10-01", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
    memory_db.add(m)
    memory_db.flush()

    memory_db.add(DishLog(meal_id=m.id, dish_id=d1.id, cooked_qty=40.0, leftover_qty=2.0, unit="kg", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m.id, dish_id=d2.id, cooked_qty=30.0, leftover_qty=9.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    df_dishes = aggregate_waste_by_dish(session=memory_db, is_synthetic=1)
    assert len(df_dishes) == 2
    top_dish = df_dishes.iloc[0]
    assert top_dish["dish_name"] == "Curry"  # 9.0 kg > 2.0 kg
    assert top_dish["total_leftover"] == 9.0

    df_trends = aggregate_waste_trends(session=memory_db, is_synthetic=1)
    assert len(df_trends) == 1
    assert df_trends.iloc[0]["leftover_kg"] == 11.0  # 2 + 9


def test_d3_dish_performance_ranking_and_candor(memory_db):
    """Verify D3 rankings, operational review candidates, and candor note."""
    d1 = get_or_create_dish(memory_db, name="High Waste Dish", unit="kg", category="main")
    d2 = get_or_create_dish(memory_db, name="Low Waste Performer", unit="kg", category="staple")

    for i in range(3):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
        memory_db.add(m)
        memory_db.flush()
        # High waste: 50 cooked, 15 leftover -> 30%
        memory_db.add(DishLog(meal_id=m.id, dish_id=d1.id, cooked_qty=50.0, leftover_qty=15.0, unit="kg", is_synthetic=1))
        # Low waste: 50 cooked, 1 leftover -> 2%
        memory_db.add(DishLog(meal_id=m.id, dish_id=d2.id, cooked_qty=50.0, leftover_qty=1.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    rankings = compute_dish_performance_rankings(session=memory_db, is_synthetic=1)
    hw = rankings["highest_waste_dishes"]
    perf = rankings["operational_performers"]

    assert len(hw) >= 1
    assert hw[0]["dish_name"] == "High Waste Dish"
    assert hw[0]["waste_percentage"] == 30.0
    assert "Review batch preparation" in hw[0]["recommendation_note"]

    assert len(perf) >= 1
    assert perf[0]["dish_name"] == "Low Waste Performer"
    assert perf[0]["waste_percentage"] == 2.0
    assert "clearance" in perf[0]["recommendation_note"].lower()

    # Candor check: Never claims popularity
    assert "popularity ratings are not collected" in rankings["data_limitation_note"].lower()


def test_d4_anomaly_detection_min_history_and_z_score(memory_db):
    """Verify D4 robust z-score anomaly detection and min-history guard."""
    from messwise.intelligence import detect_dish_waste_anomalies

    d = get_or_create_dish(memory_db, name="Rice", unit="kg", category="staple")
    memory_db.flush()

    # Seed 4 normal meals: should be marked insufficient_history
    for i in range(4):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
        memory_db.add(m)
        memory_db.flush()
        memory_db.add(DishLog(meal_id=m.id, dish_id=d.id, cooked_qty=40.0, leftover_qty=2.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    anomalies_few = detect_dish_waste_anomalies(memory_db, is_synthetic=1, min_history=6)
    assert len(anomalies_few) == 4
    assert all(a.status == "insufficient_history" for a in anomalies_few)
    assert not any(a.is_anomaly for a in anomalies_few)

    # Seed 3 more meals with 5% waste (total 7 meals) and 1 extreme spike (60% waste)
    for i in range(4, 7):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
        memory_db.add(m)
        memory_db.flush()
        memory_db.add(DishLog(meal_id=m.id, dish_id=d.id, cooked_qty=40.0, leftover_qty=2.0, unit="kg", is_synthetic=1))

    m_spike = Meal(date="2026-10-08", meal_type="lunch", headcount=200, hostel_strength=500, is_synthetic=1)
    memory_db.add(m_spike)
    memory_db.flush()
    memory_db.add(DishLog(meal_id=m_spike.id, dish_id=d.id, cooked_qty=40.0, leftover_qty=24.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    anomalies_full = detect_dish_waste_anomalies(memory_db, is_synthetic=1, min_history=6, z_threshold=3.5)
    assert len(anomalies_full) == 8
    spike_anom = next(a for a in anomalies_full if a.log_id == anomalies_full[0].log_id)
    assert spike_anom.observed_waste_pct == 60.0
    assert spike_anom.is_anomaly
    assert spike_anom.status == "evaluated"
    assert abs(spike_anom.z_score) > 3.5


def test_d5_root_cause_hypotheses(memory_db):
    """Verify D5 rule-based pattern matching produces manager review hypotheses."""
    from messwise.intelligence import generate_root_cause_hypotheses
    from messwise.db import Override, Prediction

    d1 = get_or_create_dish(memory_db, name="Roti", unit="count", category="staple")
    d2 = get_or_create_dish(memory_db, name="Dal", unit="L", category="main")
    memory_db.flush()

    # Meal with headcount far below forecast -> Attendance shortfall hypothesis
    m1 = Meal(date="2026-10-10", meal_type="lunch", headcount=150, hostel_strength=500, is_synthetic=1)
    memory_db.add(m1)
    memory_db.flush()
    # High leftover across all dishes
    memory_db.add(DishLog(meal_id=m1.id, dish_id=d1.id, cooked_qty=400.0, leftover_qty=100.0, unit="count", is_synthetic=1))
    memory_db.add(DishLog(meal_id=m1.id, dish_id=d2.id, cooked_qty=50.0, leftover_qty=12.0, unit="L", is_synthetic=1))
    # Prediction had h_hat = 250
    memory_db.add(Prediction(meal_date="2026-10-10", meal_type="lunch", h_hat=250, h_lo=220, h_hi=280, is_synthetic=1))
    memory_db.commit()

    hypotheses = generate_root_cause_hypotheses(memory_db, m1.id)
    assert len(hypotheses) >= 1
    shortfall = next((h for h in hypotheses if "attendance shortfall" in h.hypothesis_shown.lower()), None)
    assert shortfall is not None
    assert shortfall.confidence_label == "Hypothesis for Manager Review"
    assert "event calendar" in shortfall.suggested_action.lower()


def test_d6_override_analytics(memory_db):
    """Verify D6 override analytics, reason aggregations, and outcome tracking."""
    from messwise.intelligence import compute_override_analytics
    from messwise.db import Override

    # Empty state
    empty_res = compute_override_analytics(memory_db, is_synthetic=1)
    assert empty_res.total_overrides == 0
    assert "no manager overrides" in empty_res.outcome_comparison_note.lower()

    # Add 2 overrides
    d = get_or_create_dish(memory_db, name="Biryani", unit="kg", category="main")
    m = Meal(date="2026-10-12", meal_type="dinner", headcount=300, hostel_strength=500, is_synthetic=1)
    memory_db.add(m)
    memory_db.flush()

    memory_db.add(Override(dish_id=d.id, meal_id=m.id, recommended_qty=30.0, final_qty=40.0, reason="Festival extra crowd", is_synthetic=1))
    memory_db.add(Override(dish_id=d.id, meal_id=m.id, recommended_qty=30.0, final_qty=25.0, reason="Rainy evening low turnout", is_synthetic=1))
    memory_db.commit()

    ov_res = compute_override_analytics(memory_db, is_synthetic=1)
    assert ov_res.total_overrides == 2
    assert ov_res.net_positive_overrides == 1
    assert ov_res.net_negative_overrides == 1
    assert "Festival extra crowd" in ov_res.reasons_breakdown
    assert "insufficient" in ov_res.outcome_comparison_note.lower()


def test_d7_weekly_operational_brief(memory_db):
    """Verify D7 template-based operational brief generation and data provenance."""
    from messwise.intelligence import generate_weekly_operational_brief

    # Empty brief
    empty_brief = generate_weekly_operational_brief(memory_db, is_synthetic=1)
    assert empty_brief.total_meals_logged == 0
    assert "insufficient records" in empty_brief.data_quality_warning.lower()

    # Seed 3 meals
    d = get_or_create_dish(memory_db, name="Pulao", unit="kg", category="staple")
    for i in range(3):
        m = Meal(date=f"2026-10-0{i+1}", meal_type="lunch", headcount=180, hostel_strength=500, is_synthetic=1)
        memory_db.add(m)
        memory_db.flush()
        memory_db.add(DishLog(meal_id=m.id, dish_id=d.id, cooked_qty=35.0, leftover_qty=3.0, unit="kg", is_synthetic=1))
    memory_db.commit()

    brief = generate_weekly_operational_brief(memory_db, is_synthetic=1)
    assert brief.total_meals_logged == 3
    assert brief.total_headcount_served == 540
    assert brief.overall_waste_pct > 0.0
    assert "demonstration data notice" in brief.data_quality_warning.lower()
    assert len(brief.brief_narrative) > 50

