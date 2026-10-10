"""Tests for MessWise Database Layer.

Verifies:
- database initialization and schema creation
- valid meal insertion and retrieval
- dish registration and dish log creation
- synthetic flag separation (real vs synthetic data)
- audit log tracking
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from messwise.db import (
    AuditLog,
    Base,
    Dish,
    DishLog,
    Meal,
    Override,
    Prediction,
    create_dish_log_record,
    create_meal_record,
    get_meal_with_dishes,
    get_or_create_dish,
    init_db,
    list_meals_query,
    log_audit,
)
from messwise.validation import DishLogCreate, MealCreate


@pytest.fixture
def memory_db():
    """Provides an isolated in-memory SQLite database and session for testing."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_database_initialization(memory_db):
    """Verify all core tables are initialized and queryable."""
    assert memory_db.execute(select(Meal)).scalars().all() == []
    assert memory_db.execute(select(Dish)).scalars().all() == []
    assert memory_db.execute(select(DishLog)).scalars().all() == []
    assert memory_db.execute(select(Prediction)).scalars().all() == []
    assert memory_db.execute(select(Override)).scalars().all() == []
    assert memory_db.execute(select(AuditLog)).scalars().all() == []


def test_valid_meal_insertion(memory_db):
    """Verify inserting and querying a valid meal record."""
    meal_data = MealCreate(
        date="2026-10-14",
        meal_type="lunch",
        headcount=430,
        hostel_strength=500,
        event_flag=0,
        exam_flag=1,
        holiday_flag=0,
        temp_c=25.0,
        rain_mm=5.0,
        source="tally",
        is_synthetic=0,
    )
    meal = create_meal_record(session=memory_db, meal_data=meal_data)
    memory_db.commit()

    assert meal.id is not None
    assert meal.headcount == 430
    assert meal.meal_type == "lunch"
    assert meal.is_synthetic == 0

    # Query back
    queried = memory_db.get(Meal, meal.id)
    assert queried is not None
    assert queried.date == "2026-10-14"


def test_dish_creation_and_dish_log(memory_db):
    """Verify creating a dish, linking a dish log to a meal, and retrieving it."""
    # 1. Create Meal
    meal_data = MealCreate(
        date="2026-10-14",
        meal_type="dinner",
        headcount=450,
        hostel_strength=500,
        is_synthetic=0,
    )
    meal = create_meal_record(session=memory_db, meal_data=meal_data)
    memory_db.commit()

    # 2. Get or create Dish
    dish = get_or_create_dish(
        session=memory_db,
        name="Steamed Rice",
        unit="kg",
        category="staple",
        criticality_tier="staple",
    )
    memory_db.commit()
    assert dish.id is not None
    assert dish.name == "Steamed Rice"

    # 3. Create DishLog
    dish_log_data = DishLogCreate(
        meal_id=meal.id,
        dish_id=dish.id,
        cooked_qty=50.0,
        leftover_qty=6.0,
        unit="kg",
        ran_out=0,
        waste_stage="serving_surplus",
        reason_tag="overproduction",
        entry_method="form",
        is_synthetic=0,
    )
    dish_log = create_dish_log_record(session=memory_db, dish_log_data=dish_log_data)
    memory_db.commit()

    assert dish_log.id is not None
    assert dish_log.cooked_qty == 50.0
    assert dish_log.leftover_qty == 6.0

    # 4. Retrieve with get_meal_with_dishes
    retrieved = get_meal_with_dishes(session=memory_db, meal_id=meal.id)
    assert retrieved is not None
    r_meal, r_dishes = retrieved
    assert r_meal.id == meal.id
    assert len(r_dishes) == 1
    assert r_dishes[0].dish.name == "Steamed Rice"


def test_synthetic_flag_handling(memory_db):
    """Crucial requirement: Real (0) and Synthetic (1) data must be strictly distinguishable."""
    # Insert 1 Real meal
    real_meal_data = MealCreate(
        date="2026-10-10",
        meal_type="lunch",
        headcount=415,
        hostel_strength=500,
        is_synthetic=0,
    )
    create_meal_record(session=memory_db, meal_data=real_meal_data)

    # Insert 2 Synthetic meals
    for i, m_type in enumerate(["breakfast", "dinner"]):
        synth_meal_data = MealCreate(
            date=f"2026-10-1{i+1}",
            meal_type=m_type,
            headcount=380,
            hostel_strength=500,
            is_synthetic=1,
        )
        create_meal_record(session=memory_db, meal_data=synth_meal_data)

    memory_db.commit()

    # Query only Real data
    real_meals = list_meals_query(session=memory_db, is_synthetic=0)
    assert len(real_meals) == 1
    assert real_meals[0].is_synthetic == 0

    # Query only Synthetic data
    synth_meals = list_meals_query(session=memory_db, is_synthetic=1)
    assert len(synth_meals) == 2
    assert all(m.is_synthetic == 1 for m in synth_meals)

    # Query All
    all_meals = list_meals_query(session=memory_db, is_synthetic=None)
    assert len(all_meals) == 3


def test_audit_log_tracking(memory_db):
    """Verify that operations record entries in the audit trail."""
    log_audit(
        session=memory_db,
        who="mess_manager",
        action="update_service_level",
        old_value="0.90",
        new_value="0.95",
    )
    memory_db.commit()

    logs = memory_db.execute(select(AuditLog)).scalars().all()
    assert len(logs) >= 1
    last_log = logs[-1]
    assert last_log.who == "mess_manager"
    assert last_log.action == "update_service_level"
    assert last_log.new_value == "0.95"


def test_get_data_environment_summary_import():
    """Verify get_data_environment_summary can be imported from messwise.db and messwise."""
    from messwise.db import get_data_environment_summary as summary_from_db
    from messwise import get_data_environment_summary as summary_from_pkg

    assert callable(summary_from_db)
    assert callable(summary_from_pkg)
    assert summary_from_db is summary_from_pkg


def test_get_data_environment_summary_zero_state(memory_db):
    """Verify accurate counts and honest zero-real-records reporting on empty/new DB."""
    from messwise.db import get_data_environment_summary

    summary = get_data_environment_summary(memory_db)
    assert summary["real_meals_count"] == 0
    assert summary["synthetic_meals_count"] == 0
    assert summary["total_meals_count"] == 0
    assert summary["real_dish_logs_count"] == 0
    assert summary["synthetic_dish_logs_count"] == 0
    assert summary["total_dish_logs_count"] == 0
    assert summary["registered_dishes_count"] == 0
    assert summary["has_real_data"] is False
    assert summary["has_synthetic_data"] is False


def test_get_data_environment_summary_counts_and_separation(memory_db):
    """Verify correct real/synthetic meal counts, dish-log counts, dish count, and separation."""
    from messwise.db import get_data_environment_summary

    # Create 3 dishes
    d1 = get_or_create_dish(session=memory_db, name="Dal Tadka", unit="L", category="main", is_synthetic=0)
    d2 = get_or_create_dish(session=memory_db, name="Jeera Rice", unit="kg", category="staple", is_synthetic=1)
    d3 = get_or_create_dish(session=memory_db, name="Gulab Jamun", unit="count", category="side", is_synthetic=1)
    memory_db.commit()

    # Create 2 real meals
    for i in range(2):
        create_meal_record(
            session=memory_db,
            meal_data=MealCreate(
                date=f"2026-10-0{i+1}",
                meal_type="lunch",
                headcount=400 + i * 10,
                hostel_strength=500,
                is_synthetic=0,
            ),
        )

    # Create 3 synthetic meals
    for i in range(3):
        create_meal_record(
            session=memory_db,
            meal_data=MealCreate(
                date=f"2026-10-1{i+1}",
                meal_type="dinner",
                headcount=380 + i * 5,
                hostel_strength=500,
                is_synthetic=1,
            ),
        )
    memory_db.commit()

    # Fetch meal IDs
    real_meals = list_meals_query(session=memory_db, is_synthetic=0)
    synth_meals = list_meals_query(session=memory_db, is_synthetic=1)

    # Add 2 real dish logs (1 for each real meal)
    for m in real_meals:
        create_dish_log_record(
            session=memory_db,
            dish_log_data=DishLogCreate(
                meal_id=m.id,
                dish_id=d1.id,
                cooked_qty=40.0,
                leftover_qty=3.0,
                unit="L",
                is_synthetic=0,
            ),
        )

    # Add 4 synthetic dish logs across synthetic meals
    for idx, m in enumerate(synth_meals):
        create_dish_log_record(
            session=memory_db,
            dish_log_data=DishLogCreate(
                meal_id=m.id,
                dish_id=d2.id,
                cooked_qty=35.0,
                leftover_qty=2.0,
                unit="kg",
                is_synthetic=1,
            ),
        )
        if idx == 0:
            create_dish_log_record(
                session=memory_db,
                dish_log_data=DishLogCreate(
                    meal_id=m.id,
                    dish_id=d3.id,
                    cooked_qty=100.0,
                    leftover_qty=5.0,
                    unit="count",
                    is_synthetic=1,
                ),
            )
    memory_db.commit()

    summary = get_data_environment_summary(memory_db)
    assert summary["real_meals_count"] == 2
    assert summary["synthetic_meals_count"] == 3
    assert summary["total_meals_count"] == 5
    assert summary["real_dish_logs_count"] == 2
    assert summary["synthetic_dish_logs_count"] == 4
    assert summary["total_dish_logs_count"] == 6
    assert summary["registered_dishes_count"] == 3
    assert summary["real_dishes_count"] == 1
    assert summary["synthetic_dishes_count"] == 2
    assert summary["has_real_data"] is True
    assert summary["has_synthetic_data"] is True


def test_get_data_environment_summary_default_session():
    """Verify that get_data_environment_summary() works when called without passing a session."""
    from messwise.db import get_data_environment_summary

    # Calling with no arguments uses default session factory
    summary = get_data_environment_summary()
    assert isinstance(summary, dict)
    assert "real_meals_count" in summary
    assert "synthetic_meals_count" in summary
    assert "registered_dishes_count" in summary
    assert "has_real_data" in summary
    # Dynamically verifies environment metrics against live database
    assert summary["real_meals_count"] >= 0
    assert summary["has_real_data"] == (summary["real_meals_count"] > 0)
    assert summary["synthetic_meals_count"] >= 28
    assert summary["has_synthetic_data"] is True

