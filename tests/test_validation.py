"""Tests for MessWise validation logic.

Verifies strict rejection of invalid data:
- negative headcounts
- negative hostel strength
- negative cooked / leftover quantities
- leftover exceeding cooked quantity
- invalid meal types and dates
- invalid units and flags
"""

import pytest
from pydantic import ValidationError

from messwise.validation import (
    DishCreate,
    DishEntryItem,
    DishLogCreate,
    MealCreate,
    normalize_meal_type,
    normalize_unit,
    validate_dish_log_dict,
    validate_meal_dict,
)


def test_valid_meal_creation():
    """Verify valid meal data succeeds."""
    meal = MealCreate(
        date="2026-10-14",
        meal_type="Lunch",
        headcount=410,
        hostel_strength=500,
        event_flag=0,
        exam_flag=1,
        holiday_flag=0,
        temp_c=26.5,
        rain_mm=12.0,
        is_synthetic=0,
    )
    assert meal.date == "2026-10-14"
    assert meal.meal_type == "lunch"
    assert meal.headcount == 410
    assert meal.hostel_strength == 500
    assert meal.is_synthetic == 0


def test_reject_negative_headcount():
    """Verify negative headcount is rejected."""
    with pytest.raises(ValidationError) as exc:
        MealCreate(
            date="2026-10-14",
            meal_type="lunch",
            headcount=-5,
            hostel_strength=500,
        )
    assert "Headcount cannot be negative" in str(exc.value)


def test_reject_negative_hostel_strength():
    """Verify negative hostel strength is rejected."""
    with pytest.raises(ValidationError) as exc:
        MealCreate(
            date="2026-10-14",
            meal_type="lunch",
            headcount=100,
            hostel_strength=-500,
        )
    assert "Hostel strength cannot be negative" in str(exc.value)


def test_reject_negative_rain():
    """Verify negative rainfall is rejected."""
    with pytest.raises(ValidationError) as exc:
        MealCreate(
            date="2026-10-14",
            meal_type="dinner",
            headcount=300,
            hostel_strength=500,
            rain_mm=-10.0,
        )
    assert "Rainfall cannot be negative" in str(exc.value)


def test_reject_invalid_date():
    """Verify malformed or invalid dates are rejected."""
    with pytest.raises(ValidationError):
        MealCreate(
            date="not-a-date",
            meal_type="lunch",
            headcount=300,
            hostel_strength=500,
        )

    with pytest.raises(ValidationError):
        MealCreate(
            date="2026-02-31",  # Invalid calendar date
            meal_type="lunch",
            headcount=300,
            hostel_strength=500,
        )


def test_reject_invalid_meal_type():
    """Verify non-standard meal types are rejected."""
    with pytest.raises(ValidationError) as exc:
        MealCreate(
            date="2026-10-14",
            meal_type="midnight_snack",
            headcount=50,
            hostel_strength=500,
        )
    assert "Invalid meal type" in str(exc.value)


def test_reject_invalid_flags():
    """Verify boolean flags must be 0 or 1."""
    with pytest.raises(ValidationError):
        MealCreate(
            date="2026-10-14",
            meal_type="lunch",
            headcount=300,
            hostel_strength=500,
            event_flag=2,
        )


def test_valid_dish_log():
    """Verify valid dish log creation."""
    dish_log = DishLogCreate(
        meal_id=1,
        dish_id=2,
        cooked_qty=40.0,
        leftover_qty=4.0,
        unit="kg",
        ran_out=0,
        waste_stage="serving_surplus",
        reason_tag="overproduction",
        is_synthetic=0,
    )
    assert dish_log.cooked_qty == 40.0
    assert dish_log.leftover_qty == 4.0
    assert dish_log.unit == "kg"


def test_reject_negative_cooked_qty():
    """Verify negative cooked quantity is rejected."""
    with pytest.raises(ValidationError) as exc:
        DishLogCreate(
            meal_id=1,
            dish_id=2,
            cooked_qty=-10.0,
            leftover_qty=0.0,
            unit="kg",
        )
    assert "Cooked quantity cannot be negative" in str(exc.value)


def test_reject_negative_leftover_qty():
    """Verify negative leftover quantity is rejected."""
    with pytest.raises(ValidationError) as exc:
        DishLogCreate(
            meal_id=1,
            dish_id=2,
            cooked_qty=10.0,
            leftover_qty=-2.0,
            unit="kg",
        )
    assert "Leftover quantity cannot be negative" in str(exc.value)


def test_reject_leftover_greater_than_cooked():
    """Crucial domain rule: leftover quantity cannot exceed cooked quantity."""
    with pytest.raises(ValidationError) as exc:
        DishLogCreate(
            meal_id=1,
            dish_id=2,
            cooked_qty=20.0,
            leftover_qty=25.0,
            unit="kg",
        )
    assert "Leftover quantity (25.0) cannot be greater than cooked quantity (20.0)" in str(exc.value)


def test_leftover_equal_to_cooked_allowed():
    """Boundary condition: leftover == cooked is valid (nobody consumed the dish)."""
    dish_log = DishLogCreate(
        meal_id=1,
        dish_id=2,
        cooked_qty=15.0,
        leftover_qty=15.0,
        unit="kg",
    )
    assert dish_log.cooked_qty == dish_log.leftover_qty


def test_reject_invalid_unit():
    """Verify invalid measurement units are rejected."""
    with pytest.raises(ValidationError) as exc:
        DishLogCreate(
            meal_id=1,
            dish_id=2,
            cooked_qty=20.0,
            leftover_qty=2.0,
            unit="gallons",
        )
    assert "Invalid unit" in str(exc.value)


def test_dictionary_validators():
    """Verify the plain dictionary validators for Streamlit UI forms."""
    # Valid meal dict
    valid_m, errs_m = validate_meal_dict({
        "date": "2026-10-15",
        "meal_type": "dinner",
        "headcount": 350,
        "hostel_strength": 500,
        "event_flag": 0,
        "is_synthetic": 0,
    })
    assert valid_m is True
    assert len(errs_m) == 0

    # Invalid meal dict
    invalid_m, errs_m2 = validate_meal_dict({
        "date": "invalid-date",
        "meal_type": "unknown",
        "headcount": -10,
        "hostel_strength": -20,
    })
    assert invalid_m is False
    assert len(errs_m2) >= 3

    # Invalid dish dict: leftover > cooked
    invalid_d, errs_d = validate_dish_log_dict({
        "dish_name": "Dal",
        "cooked_qty": 10.0,
        "leftover_qty": 18.0,
        "unit": "L",
    })
    assert invalid_d is False
    assert any("greater than cooked" in e for e in errs_d)
