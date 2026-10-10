"""MessWise Synthetic Development Data Generator.

Generates realistic institutional mess meal and dish consumption records
strictly marked with `is_synthetic = 1`.

Crucial Safety & Separation Rules (per PLAN.md Section 7.6):
1. Every generated record has `is_synthetic = 1`.
2. NEVER writes into `data/raw/` (reserved strictly for real pilot data).
3. Writes output to `data/synthetic/` and optionally populates SQLite.
4. Clearly labelled as synthetic development/demo data.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from datetime import date, datetime, timedelta
import sys
from pathlib import Path

# Ensure root directory is on Python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from messwise.db import (
    Dish,
    DishLog,
    Meal,
    get_engine,
    get_or_create_dish,
    get_session_factory,
    init_db,
)
from messwise.validation import (
    DishCreate,
    DishLogCreate,
    MealCreate,
)

# Root directory reference
BASE_DIR = Path(__file__).resolve().parent.parent
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"

# Canonical Dishes for Synthetic Institutional Mess
DEFAULT_DISHES = [
    {"name": "Steamed Rice", "category": "staple", "unit": "kg", "criticality_tier": "staple", "prep_loss_pct": 0.04, "base_rate": 0.18},
    {"name": "Roti", "category": "staple", "unit": "count", "criticality_tier": "staple", "prep_loss_pct": 0.02, "base_rate": 2.2},
    {"name": "Dal Tadka", "category": "staple", "unit": "L", "criticality_tier": "staple", "prep_loss_pct": 0.03, "base_rate": 0.12},
    {"name": "Sambar", "category": "main", "unit": "L", "criticality_tier": "staple", "prep_loss_pct": 0.03, "base_rate": 0.13},
    {"name": "Paneer Butter Masala", "category": "main", "unit": "kg", "criticality_tier": "main", "prep_loss_pct": 0.05, "base_rate": 0.11},
    {"name": "Mixed Veg Korma", "category": "side", "unit": "kg", "criticality_tier": "side", "prep_loss_pct": 0.04, "base_rate": 0.09},
    {"name": "Aloo Fry", "category": "side", "unit": "kg", "criticality_tier": "side", "prep_loss_pct": 0.03, "base_rate": 0.08},
    {"name": "Curd", "category": "side", "unit": "L", "criticality_tier": "side", "prep_loss_pct": 0.01, "base_rate": 0.07},
]

MEAL_DISH_MAPPINGS = {
    "breakfast": ["Roti", "Aloo Fry", "Curd"],
    "lunch": ["Steamed Rice", "Dal Tadka", "Mixed Veg Korma", "Curd"],
    "snacks": ["Roti", "Curd"],
    "dinner": ["Steamed Rice", "Roti", "Paneer Butter Masala", "Sambar"],
}

BASE_PARTICIPATION = {
    "breakfast": 0.65,
    "lunch": 0.82,
    "snacks": 0.48,
    "dinner": 0.86,
}


def generate_synthetic_dataset(
    days: int = 14,
    start_date: str = "2026-10-01",
    hostel_strength: int = 500,
    seed: int = 42,
) -> Tuple[List[dict], List[dict]]:
    """Generate realistic synthetic meal and dish-log dictionaries."""
    random.seed(seed)
    current_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    meals_records: List[dict] = []
    dish_log_records: List[dict] = []

    meal_id_counter = 1
    dish_log_id_counter = 1

    for day_idx in range(days):
        dt = current_date + timedelta(days=day_idx)
        date_str = dt.isoformat()
        weekday = dt.weekday()  # 0=Monday, 6=Sunday

        # Context features
        is_weekend = 1 if weekday in (5, 6) else 0
        is_exam = 1 if 5 <= day_idx <= 8 else 0
        is_holiday = 1 if weekday == 6 or day_idx == 3 else 0
        is_event = 1 if day_idx == 12 else 0

        # Weather simulation (Hyderabad October climate)
        is_rainy = 1 if random.random() < 0.25 else 0
        rain_mm = round(random.uniform(5.0, 35.0), 1) if is_rainy else 0.0
        temp_c = round(random.uniform(23.0, 31.0), 1)

        for meal_type in ["breakfast", "lunch", "snacks", "dinner"]:
            base_p = BASE_PARTICIPATION[meal_type]

            # Context modifiers
            p = base_p
            if is_weekend:
                p -= 0.08  # Students go home or eat outside
            if is_exam:
                p -= 0.06  # Irregular schedules during exams
            if is_holiday:
                p -= 0.12  # Holiday trips
            if is_event:
                p += 0.09  # Campus event keeps students inside
            if is_rainy:
                p += 0.05  # Rain discourages eating outside

            p = max(0.20, min(0.98, p + random.gauss(0, 0.03)))
            headcount = int(round(hostel_strength * p))

            meal_dict = {
                "id": meal_id_counter,
                "date": date_str,
                "meal_type": meal_type,
                "headcount": headcount,
                "hostel_strength": hostel_strength,
                "event_flag": is_event,
                "exam_flag": is_exam,
                "holiday_flag": is_holiday,
                "temp_c": temp_c,
                "rain_mm": rain_mm,
                "source": "synthetic",
                "is_synthetic": 1,  # Strictly marked
            }
            meals_records.append(meal_dict)

            # Generate dish logs for this meal
            dishes_for_meal = MEAL_DISH_MAPPINGS[meal_type]
            for dish_name in dishes_for_meal:
                dish_meta = next(d for d in DEFAULT_DISHES if d["name"] == dish_name)
                base_rate = dish_meta["base_rate"]
                actual_appetite_rate = max(0.01, random.gauss(base_rate, base_rate * 0.10))
                actual_demand = headcount * actual_appetite_rate

                # Overproduction bias: cooks cook for ~10% more on average
                planned_margin = random.uniform(1.02, 1.15)
                # Occasional shortage (5% chance)
                if random.random() < 0.05:
                    cooked_qty = round(actual_demand * random.uniform(0.85, 0.95), 1)
                else:
                    cooked_qty = round(actual_demand * planned_margin, 1)

                if dish_meta["unit"] == "count":
                    cooked_qty = float(math.ceil(cooked_qty / 10.0) * 10)

                # Determine leftover & ran_out
                if cooked_qty <= actual_demand:
                    leftover_qty = 0.0
                    ran_out = 1
                    reason_tag = "timing"
                else:
                    leftover_qty = round(cooked_qty - actual_demand, 1)
                    ran_out = 0
                    reason_tag = "overproduction" if leftover_qty > (0.10 * cooked_qty) else "none"

                dish_log_dict = {
                    "id": dish_log_id_counter,
                    "meal_id": meal_id_counter,
                    "dish_name": dish_name,
                    "unit": dish_meta["unit"],
                    "cooked_qty": max(0.0, cooked_qty),
                    "leftover_qty": min(max(0.0, leftover_qty), cooked_qty),
                    "ran_out": ran_out,
                    "waste_stage": "serving_surplus",
                    "reason_tag": reason_tag,
                    "entry_method": "synthetic",
                    "photo_ref": None,
                    "is_synthetic": 1,  # Strictly marked
                }
                dish_log_records.append(dish_log_dict)
                dish_log_id_counter += 1

            meal_id_counter += 1

    return meals_records, dish_log_records


def save_synthetic_csvs(meals: List[dict], dish_logs: List[dict]) -> Tuple[Path, Path]:
    """Write synthetic datasets to data/synthetic/ CSV files."""
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    meals_csv = SYNTHETIC_DIR / "synthetic_meals.csv"
    dish_logs_csv = SYNTHETIC_DIR / "synthetic_dish_logs.csv"

    # Write meals CSV
    if meals:
        with open(meals_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(meals[0].keys()))
            writer.writeheader()
            writer.writerows(meals)

    # Write dish logs CSV
    if dish_logs:
        with open(dish_logs_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(dish_logs[0].keys()))
            writer.writeheader()
            writer.writerows(dish_logs)

    return meals_csv, dish_logs_csv


def populate_database_with_synthetic(
    meals: List[dict],
    dish_logs: List[dict],
    engine=None,
) -> int:
    """Insert synthetic dishes, meals, and dish logs into SQLite."""
    eng = engine or get_engine()
    init_db(eng)
    session_factory = get_session_factory(eng)

    inserted_count = 0
    with session_factory() as session:
        # Pre-register default dishes
        dish_lookup: dict[str, Dish] = {}
        for d in DEFAULT_DISHES:
            dish_obj = get_or_create_dish(
                session=session,
                name=d["name"],
                unit=d["unit"],
                category=d["category"],
                criticality_tier=d["criticality_tier"],
                prep_loss_pct=d["prep_loss_pct"],
                is_synthetic=1,
            )
            dish_lookup[d["name"]] = dish_obj

        session.commit()

        # Map synthetic meal id to real DB Meal id
        meal_id_map: dict[int, int] = {}

        for m_data in meals:
            meal_create = MealCreate(
                date=m_data["date"],
                meal_type=m_data["meal_type"],
                headcount=m_data["headcount"],
                hostel_strength=m_data["hostel_strength"],
                event_flag=m_data["event_flag"],
                exam_flag=m_data["exam_flag"],
                holiday_flag=m_data["holiday_flag"],
                temp_c=m_data["temp_c"],
                rain_mm=m_data["rain_mm"],
                source="synthetic",
                is_synthetic=1,
            )
            meal_orm = Meal(
                date=meal_create.date,
                meal_type=meal_create.meal_type,
                headcount=meal_create.headcount,
                hostel_strength=meal_create.hostel_strength,
                event_flag=meal_create.event_flag,
                exam_flag=meal_create.exam_flag,
                holiday_flag=meal_create.holiday_flag,
                temp_c=meal_create.temp_c,
                rain_mm=meal_create.rain_mm,
                source=meal_create.source,
                is_synthetic=1,
            )
            session.add(meal_orm)
            session.flush()
            meal_id_map[m_data["id"]] = meal_orm.id
            inserted_count += 1

        for dl_data in dish_logs:
            real_meal_id = meal_id_map[dl_data["meal_id"]]
            dish_obj = dish_lookup[dl_data["dish_name"]]

            dish_log_orm = DishLog(
                meal_id=real_meal_id,
                dish_id=dish_obj.id,
                cooked_qty=dl_data["cooked_qty"],
                leftover_qty=dl_data["leftover_qty"],
                unit=dl_data["unit"],
                ran_out=dl_data["ran_out"],
                waste_stage=dl_data["waste_stage"],
                reason_tag=dl_data["reason_tag"],
                entry_method="synthetic",
                is_synthetic=1,
            )
            session.add(dish_log_orm)

        session.commit()

    return inserted_count


def main():
    parser = argparse.ArgumentParser(description="MessWise Synthetic Data Generator")
    parser.add_argument("--days", type=int, default=14, help="Number of days to simulate (default: 14)")
    parser.add_argument("--strength", type=int, default=500, help="Hostel strength (default: 500)")
    parser.add_argument("--start-date", type=str, default="2026-10-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--db", action="store_true", help="Also populate local SQLite database")
    args = parser.parse_args()

    print(f"Generating synthetic development data for {args.days} days...")
    meals, dish_logs = generate_synthetic_dataset(
        days=args.days,
        start_date=args.start_date,
        hostel_strength=args.strength,
    )

    meals_path, dl_path = save_synthetic_csvs(meals, dish_logs)
    print(f"[OK] Saved synthetic meals ({len(meals)} rows): {meals_path}")
    print(f"[OK] Saved synthetic dish logs ({len(dish_logs)} rows): {dl_path}")

    if args.db:
        inserted = populate_database_with_synthetic(meals, dish_logs)
        print(f"[OK] Populated database with {inserted} synthetic meal records (is_synthetic = 1).")


if __name__ == "__main__":
    main()
