"""messwise.simulator — Step 5: Savings Simulator (E3) and Blind Forecast Reveal (E4).

Core Architecture & Integrity:
1. Replays historical meals using strictly pre-cutoff information to prevent look-ahead leakage.
2. Compares actual cooked quantities against simulated MessWise plans.
3. Groups and reports metrics by strictly compatible units (kg, L, count) — never aggregates across incompatible units.
4. Identifies actual historical shortages (ran_out == 1) and distinguishes them from simulated shortage risk.
5. Flags right-censored demand candor: ran-out meals cannot be claimed as verified unconstrained demand.
6. Does NOT invent ingredient prices or rupee savings when cost data is missing from the database.
7. Enforces strict synthetic vs. real separation (0 real records -> honest zero-state disclosure).
8. Provides two-stage Blind Forecast Reveal: Stage 1/2 freezes pre-meal prediction/plan with actuals hidden;
   Stage 2/3 reveals measured outcomes and compares against the frozen plan without recomputing.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from messwise.db import Meal, Dish, DishLog, AuditLog
from messwise.forecast import (
    HeadcountForecaster,
    ForecastResult,
    compute_baseline_last_week,
    compute_baseline_trailing_avg,
    fetch_historical_meals,
    DEFAULT_HOSTEL_STRENGTH,
)
from messwise.planner import (
    generate_meal_plan,
    compute_dish_consumption_rates,
    calculate_service_headcount,
    apply_batch_rounding,
    MealPlanResult,
    DishPlanItem,
    DEFAULT_BATCH_SIZES,
)

logger = logging.getLogger(__name__)

# Minimum historical meals required prior to cutoff for confident evaluation
MIN_PRE_CUTOFF_MEALS = 3


@dataclass
class ReplayedDishItem:
    dish_id: int
    dish_name: str
    unit: str
    actual_cooked_qty: float
    recommended_qty: float
    qty_diff: float  # actual_cooked_qty - recommended_qty (positive = planned less)
    actual_leftover_qty: Optional[float]
    actual_ran_out: bool
    is_comparable: bool
    potential_quantity_reduction: float  # theoretical reduction without shortage inference
    simulated_shortage_risk: bool  # True if recommended < (actual_cooked - actual_leftover)
    limitation_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReplayedMealResult:
    meal_id: int
    meal_date: str
    meal_type: str
    actual_headcount: int
    forecast_headcount: Optional[int]
    forecast_interval: Optional[Tuple[int, int]]
    service_level: float
    is_evaluable: bool
    exclusion_reason: Optional[str]
    pre_cutoff_meals_count: int
    dish_comparisons: List[ReplayedDishItem] = field(default_factory=list)
    actual_shortage_event: bool = False
    simulated_shortage_risk_event: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meal_id": self.meal_id,
            "meal_date": self.meal_date,
            "meal_type": self.meal_type,
            "actual_headcount": self.actual_headcount,
            "forecast_headcount": self.forecast_headcount,
            "forecast_interval": list(self.forecast_interval) if self.forecast_interval else None,
            "service_level": self.service_level,
            "is_evaluable": self.is_evaluable,
            "exclusion_reason": self.exclusion_reason,
            "pre_cutoff_meals_count": self.pre_cutoff_meals_count,
            "dish_comparisons": [d.to_dict() for d in self.dish_comparisons],
            "actual_shortage_event": self.actual_shortage_event,
            "simulated_shortage_risk_event": self.simulated_shortage_risk_event,
        }


@dataclass
class SavingsSimulationReport:
    is_synthetic: int
    environment_label: str
    has_sufficient_data: bool
    total_meals_replayed: int
    meals_evaluable: int
    meals_excluded: int
    totals_by_unit: Dict[str, Dict[str, float]]  # unit -> {actual_cooked, recommended, potential_reduction, leftovers}
    actual_shortage_events_count: int
    simulated_shortage_risk_count: int
    cost_status_message: str
    cost_savings_rupees: Optional[float]
    candor_disclosures: List[str]
    replayed_meals: List[ReplayedMealResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_synthetic": self.is_synthetic,
            "environment_label": self.environment_label,
            "has_sufficient_data": self.has_sufficient_data,
            "total_meals_replayed": self.total_meals_replayed,
            "meals_evaluable": self.meals_evaluable,
            "meals_excluded": self.meals_excluded,
            "totals_by_unit": self.totals_by_unit,
            "actual_shortage_events_count": self.actual_shortage_events_count,
            "simulated_shortage_risk_count": self.simulated_shortage_risk_count,
            "cost_status_message": self.cost_status_message,
            "cost_savings_rupees": self.cost_savings_rupees,
            "candor_disclosures": self.candor_disclosures,
            "replayed_meals": [m.to_dict() for m in self.replayed_meals],
        }


@dataclass
class BlindForecastState:
    meal_id: int
    meal_date: str
    meal_type: str
    is_synthetic: int
    service_level: float
    hostel_strength: int
    pre_cutoff_meals_count: int
    is_eligible: bool
    ineligibility_reason: Optional[str]
    h_hat: Optional[int]
    h_lo: Optional[int]
    h_hi: Optional[int]
    h_q: Optional[int]
    baseline_lag7: Optional[int]
    baseline_trailing_avg: Optional[int]
    top_drivers: List[Dict[str, Any]]
    explanation: str
    planned_dishes: List[Dict[str, Any]]
    frozen_timestamp: str
    is_revealed: bool = False
    # Revealed outcome fields (populated strictly in Stage 3)
    actual_headcount: Optional[int] = None
    forecast_error: Optional[int] = None  # h_hat - actual
    abs_forecast_error: Optional[int] = None
    inside_interval: Optional[bool] = None
    baseline_lag7_error: Optional[int] = None
    baseline_trailing_error: Optional[int] = None
    dish_outcomes: List[Dict[str, Any]] = field(default_factory=list)
    actual_shortage_occurred: Optional[bool] = None
    evaluation_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_pre_cutoff_meals_dataframe(
    session: Session,
    target_date: str,
    target_meal_id: int,
    is_synthetic: int = 0,
) -> pd.DataFrame:
    """Fetch all meals strictly prior to the target meal cutoff to prevent look-ahead leakage."""
    stmt = (
        select(Meal)
        .where(
            Meal.is_synthetic == is_synthetic,
            or_(
                Meal.date < target_date,
                and_(Meal.date == target_date, Meal.id < target_meal_id),
            ),
        )
        .order_by(Meal.date.asc(), Meal.id.asc())
    )
    records = session.execute(stmt).scalars().all()
    if not records:
        return pd.DataFrame()

    data = [
        {
            "id": r.id,
            "date": r.date,
            "meal_type": r.meal_type.lower(),
            "headcount": r.headcount,
            "hostel_strength": r.hostel_strength if r.hostel_strength > 0 else DEFAULT_HOSTEL_STRENGTH,
            "participation_rate": (r.headcount / r.hostel_strength) if r.hostel_strength > 0 else 0.0,
            "event_flag": r.event_flag,
            "exam_flag": r.exam_flag,
            "holiday_flag": r.holiday_flag,
            "temp_c": r.temp_c if r.temp_c is not None else 28.0,
            "rain_mm": r.rain_mm if r.rain_mm is not None else 0.0,
            "is_synthetic": r.is_synthetic,
        }
        for r in records
    ]
    df = pd.DataFrame(data)
    df["dt"] = pd.to_datetime(df["date"])
    df["weekday"] = df["dt"].dt.weekday
    df["day_of_year"] = df["dt"].dt.dayofyear
    return df


def run_savings_simulation(
    session: Session,
    is_synthetic: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    meal_type: Optional[str] = None,
    service_level: float = 0.95,
    hostel_strength: int = DEFAULT_HOSTEL_STRENGTH,
) -> SavingsSimulationReport:
    """Execute E3 historical savings replay without look-ahead leakage.

    Methodology:
    1. Select historical candidate meals matching date/type criteria.
    2. For each candidate meal:
       a. Establish historical cutoff (strictly prior to candidate meal date and id).
       b. Check for sufficient prior history (>= MIN_PRE_CUTOFF_MEALS).
       c. If sufficient: train isolated forecaster and fit consumption rates using only pre-cutoff data.
       d. Generate simulated plan.
       e. Compare simulated plan to actual recorded cooked quantities by compatible units.
       f. Track recorded leftovers and actual ran-out shortage occurrences.
    3. Aggregate metrics strictly by unit (kg, L, count).
    4. Provide honest candor disclosures and zero-cost notices.
    """
    env_label = "Synthetic Demonstration — Not Real-World Results" if is_synthetic == 1 else "Real Pilot Records"

    # Query candidate meals
    stmt = select(Meal).where(Meal.is_synthetic == is_synthetic)
    if start_date:
        stmt = stmt.where(Meal.date >= start_date)
    if end_date:
        stmt = stmt.where(Meal.date <= end_date)
    if meal_type and meal_type.strip().lower() != "all":
        stmt = stmt.where(Meal.meal_type == meal_type.strip().lower())
    stmt = stmt.order_by(Meal.date.asc(), Meal.id.asc())

    candidate_meals = session.execute(stmt).scalars().all()

    if not candidate_meals:
        disclosures = [
            f"No historical records found for environment ({env_label}). "
            "Ensure data exists or check date filter."
        ]
        if is_synthetic == 0:
            disclosures.insert(0, "INSUFFICIENT REAL PILOT DATA: Zero real-world pilot meals exist in the database.")
        else:
            disclosures.insert(0, "SYNTHETIC DEMONSTRATION: Zero synthetic demo meals found for this filter.")

        return SavingsSimulationReport(
            is_synthetic=is_synthetic,
            environment_label=env_label,
            has_sufficient_data=False,
            total_meals_replayed=0,
            meals_evaluable=0,
            meals_excluded=0,
            totals_by_unit={},
            actual_shortage_events_count=0,
            simulated_shortage_risk_count=0,
            cost_status_message="Cost estimation unavailable — valid ingredient prices are not configured.",
            cost_savings_rupees=None,
            candor_disclosures=disclosures,
            replayed_meals=[],
        )

    # Initialize unit totals
    totals_by_unit: Dict[str, Dict[str, float]] = {}
    total_replayed = len(candidate_meals)
    evaluable_count = 0
    excluded_count = 0
    total_actual_shortages = 0
    total_simulated_shortage_risks = 0
    replayed_results: List[ReplayedMealResult] = []

    for target_meal in candidate_meals:
        # 1. Establish pre-cutoff history
        df_pre = get_pre_cutoff_meals_dataframe(
            session=session,
            target_date=target_meal.date,
            target_meal_id=target_meal.id,
            is_synthetic=is_synthetic,
        )
        pre_count = len(df_pre)

        # Exclusion guard: insufficient prior history
        if pre_count < MIN_PRE_CUTOFF_MEALS:
            excluded_count += 1
            replayed_results.append(
                ReplayedMealResult(
                    meal_id=target_meal.id,
                    meal_date=target_meal.date,
                    meal_type=target_meal.meal_type,
                    actual_headcount=target_meal.headcount,
                    forecast_headcount=None,
                    forecast_interval=None,
                    service_level=service_level,
                    is_evaluable=False,
                    exclusion_reason=(
                        f"Insufficient pre-cutoff history ({pre_count} meals < {MIN_PRE_CUTOFF_MEALS} required). "
                        "Excluded to prevent ungrounded cold-start distortion."
                    ),
                    pre_cutoff_meals_count=pre_count,
                    dish_comparisons=[],
                )
            )
            continue

        # 2. Train isolated forecaster on pre-cutoff history only
        isolated_forecaster = HeadcountForecaster()
        isolated_forecaster.fit(df_pre)

        # 3. Generate isolated meal plan using only pre-cutoff data
        try:
            plan_res = generate_meal_plan(
                session=session,
                target_date=target_meal.date,
                meal_type=target_meal.meal_type,
                service_level=service_level,
                hostel_strength=hostel_strength,
                is_synthetic=is_synthetic,
                before_date=target_meal.date,
                before_meal_id=target_meal.id,
                custom_forecaster=isolated_forecaster,
                custom_df_history=df_pre,
            )
        except Exception as e:
            logger.warning(f"Failed to generate simulated plan for meal {target_meal.id}: {e}")
            excluded_count += 1
            replayed_results.append(
                ReplayedMealResult(
                    meal_id=target_meal.id,
                    meal_date=target_meal.date,
                    meal_type=target_meal.meal_type,
                    actual_headcount=target_meal.headcount,
                    forecast_headcount=None,
                    forecast_interval=None,
                    service_level=service_level,
                    is_evaluable=False,
                    exclusion_reason=f"Plan calculation error: {str(e)}",
                    pre_cutoff_meals_count=pre_count,
                    dish_comparisons=[],
                )
            )
            continue

        # 4. Fetch actual recorded dish logs for this meal
        dish_logs_stmt = select(DishLog, Dish).join(Dish, DishLog.dish_id == Dish.id).where(
            DishLog.meal_id == target_meal.id,
            DishLog.is_synthetic == is_synthetic,
        )
        actual_dish_rows = session.execute(dish_logs_stmt).all()

        plan_map = {item.dish_id: item for item in plan_res.dishes}
        dish_comparisons: List[ReplayedDishItem] = []
        meal_had_shortage = False
        meal_had_sim_risk = False

        for dlog, dish in actual_dish_rows:
            p_item = plan_map.get(dlog.dish_id)
            if not p_item:
                # Dish was not in catalog or not planned
                dish_comparisons.append(
                    ReplayedDishItem(
                        dish_id=dlog.dish_id,
                        dish_name=dish.name,
                        unit=dish.unit,
                        actual_cooked_qty=float(dlog.cooked_qty) if dlog.cooked_qty is not None else 0.0,
                        recommended_qty=0.0,
                        qty_diff=0.0,
                        actual_leftover_qty=float(dlog.leftover_qty) if dlog.leftover_qty is not None else None,
                        actual_ran_out=bool(dlog.ran_out == 1),
                        is_comparable=False,
                        potential_quantity_reduction=0.0,
                        simulated_shortage_risk=False,
                        limitation_note="Dish not present in pre-cutoff planner catalog.",
                    )
                )
                continue

            actual_cooked = float(dlog.cooked_qty) if dlog.cooked_qty is not None else 0.0
            actual_leftover = float(dlog.leftover_qty) if dlog.leftover_qty is not None else 0.0
            rec_qty = float(p_item.planned_quantity)
            ran_out = bool(dlog.ran_out == 1)
            unit = dish.unit

            # Quantities difference: positive means kitchen cooked more than MessWise recommendation
            diff = round(actual_cooked - rec_qty, 2)

            # Potential quantity reduction:
            # If recommendation is lower than actual cooked:
            # We treat the delta as theoretical reduction in cooking quantity.
            # If actual cooked is lower than recommendation, delta is negative (MessWise would have cooked more).
            reduction = round(diff, 2)

            # Shortage risk: Did MessWise recommend less than the food actually eaten (served = cooked - leftover)?
            actual_served = max(0.0, actual_cooked - actual_leftover)
            sim_shortage = bool(rec_qty < actual_served)

            if ran_out:
                meal_had_shortage = True
                total_actual_shortages += 1
            if sim_shortage:
                meal_had_sim_risk = True
                total_simulated_shortage_risks += 1

            note = None
            if ran_out:
                note = "Dish ran out in reality: actual consumption was right-censored."
            elif sim_shortage:
                note = "Simulated plan was below recorded served quantity (shortage risk)."

            dish_item = ReplayedDishItem(
                dish_id=dlog.dish_id,
                dish_name=dish.name,
                unit=unit,
                actual_cooked_qty=actual_cooked,
                recommended_qty=rec_qty,
                qty_diff=diff,
                actual_leftover_qty=actual_leftover,
                actual_ran_out=ran_out,
                is_comparable=True,
                potential_quantity_reduction=reduction,
                simulated_shortage_risk=sim_shortage,
                limitation_note=note,
            )
            dish_comparisons.append(dish_item)

            # Accumulate totals by strictly compatible units
            if unit not in totals_by_unit:
                totals_by_unit[unit] = {
                    "actual_cooked": 0.0,
                    "simulated_recommended": 0.0,
                    "potential_reduction": 0.0,
                    "actual_leftovers": 0.0,
                }
            totals_by_unit[unit]["actual_cooked"] = round(totals_by_unit[unit]["actual_cooked"] + actual_cooked, 2)
            totals_by_unit[unit]["simulated_recommended"] = round(totals_by_unit[unit]["simulated_recommended"] + rec_qty, 2)
            totals_by_unit[unit]["potential_reduction"] = round(totals_by_unit[unit]["potential_reduction"] + reduction, 2)
            totals_by_unit[unit]["actual_leftovers"] = round(totals_by_unit[unit]["actual_leftovers"] + actual_leftover, 2)

        evaluable_count += 1
        replayed_results.append(
            ReplayedMealResult(
                meal_id=target_meal.id,
                meal_date=target_meal.date,
                meal_type=target_meal.meal_type,
                actual_headcount=target_meal.headcount,
                forecast_headcount=plan_res.forecast_h_hat,
                forecast_interval=None,
                service_level=service_level,
                is_evaluable=True,
                exclusion_reason=None,
                pre_cutoff_meals_count=pre_count,
                dish_comparisons=dish_comparisons,
                actual_shortage_event=meal_had_shortage,
                simulated_shortage_risk_event=meal_had_sim_risk,
            )
        )

    # Disclosures & Integrity notes
    disclosures = [
        "Replay strictly isolates historical information available before each meal's decision cutoff to prevent look-ahead leakage.",
        "Reduction figures represent theoretical cooking adjustments by compatible unit (kg, L, count) and must NOT be interpreted as verified physical savings.",
        "Dishes that ran out in reality had right-censored appetite; their recorded consumption does not reflect unconstrained demand.",
    ]
    if is_synthetic == 1:
        disclosures.insert(0, "SYNTHETIC DEMONSTRATION: Replayed from synthetic test data. Cannot be cited as real-world operational proof.")
    else:
        if total_replayed == 0:
            disclosures.insert(0, "INSUFFICIENT REAL PILOT DATA: Zero real-world pilot meals exist in the database.")

    return SavingsSimulationReport(
        is_synthetic=is_synthetic,
        environment_label=env_label,
        has_sufficient_data=(evaluable_count > 0),
        total_meals_replayed=total_replayed,
        meals_evaluable=evaluable_count,
        meals_excluded=excluded_count,
        totals_by_unit=totals_by_unit,
        actual_shortage_events_count=total_actual_shortages,
        simulated_shortage_risk_count=total_simulated_shortage_risks,
        cost_status_message="Cost estimation unavailable — valid ingredient prices are not configured.",
        cost_savings_rupees=None,
        candor_disclosures=disclosures,
        replayed_meals=replayed_results,
    )


def generate_blind_forecast(
    session: Session,
    meal_id: int,
    service_level: float = 0.95,
    hostel_strength: int = DEFAULT_HOSTEL_STRENGTH,
) -> BlindForecastState:
    """Stage 2: Generate and freeze blind forecast and plan using strictly pre-cutoff information.

    Masks all actual outcomes (headcount, leftovers, ran-out flags) until reveal action is triggered.
    """
    target_meal = session.execute(select(Meal).where(Meal.id == meal_id)).scalar_one_or_none()
    if not target_meal:
        return BlindForecastState(
            meal_id=meal_id,
            meal_date="",
            meal_type="",
            is_synthetic=0,
            service_level=service_level,
            hostel_strength=hostel_strength,
            pre_cutoff_meals_count=0,
            is_eligible=False,
            ineligibility_reason="Historical meal record not found.",
            h_hat=None,
            h_lo=None,
            h_hi=None,
            h_q=None,
            baseline_lag7=None,
            baseline_trailing_avg=None,
            top_drivers=[],
            explanation="Meal not found.",
            planned_dishes=[],
            frozen_timestamp=datetime.now(timezone.utc).isoformat(),
            is_revealed=False,
        )

    # 1. Fetch pre-cutoff history
    df_pre = get_pre_cutoff_meals_dataframe(
        session=session,
        target_date=target_meal.date,
        target_meal_id=target_meal.id,
        is_synthetic=target_meal.is_synthetic,
    )
    pre_count = len(df_pre)

    if pre_count < MIN_PRE_CUTOFF_MEALS:
        return BlindForecastState(
            meal_id=target_meal.id,
            meal_date=target_meal.date,
            meal_type=target_meal.meal_type,
            is_synthetic=target_meal.is_synthetic,
            service_level=service_level,
            hostel_strength=hostel_strength,
            pre_cutoff_meals_count=pre_count,
            is_eligible=False,
            ineligibility_reason=(
                f"Insufficient prior history ({pre_count} meals < {MIN_PRE_CUTOFF_MEALS} required). "
                "Forecast cannot be reliably generated without prior data."
            ),
            h_hat=None,
            h_lo=None,
            h_hi=None,
            h_q=None,
            baseline_lag7=None,
            baseline_trailing_avg=None,
            top_drivers=[],
            explanation="Cold-start state: insufficient history before this meal.",
            planned_dishes=[],
            frozen_timestamp=datetime.now(timezone.utc).isoformat(),
            is_revealed=False,
        )

    # 2. Train isolated forecaster on pre-cutoff history
    isolated_forecaster = HeadcountForecaster()
    isolated_forecaster.fit(df_pre)

    forecast_res = isolated_forecaster.predict_slot(
        df_history=df_pre,
        target_date_str=target_meal.date,
        meal_type=target_meal.meal_type,
        hostel_strength=hostel_strength,
        is_synthetic=target_meal.is_synthetic,
    )

    # Honest baselines calculated solely from pre-cutoff history
    b_lag7 = compute_baseline_last_week(df_pre, target_meal.date, target_meal.meal_type)
    b_trailing = compute_baseline_trailing_avg(df_pre, target_meal.date, target_meal.meal_type, hostel_strength)

    # 3. Generate cooking plan from pre-cutoff history
    plan_res = generate_meal_plan(
        session=session,
        target_date=target_meal.date,
        meal_type=target_meal.meal_type,
        service_level=service_level,
        hostel_strength=hostel_strength,
        is_synthetic=target_meal.is_synthetic,
        before_date=target_meal.date,
        before_meal_id=target_meal.id,
        custom_forecaster=isolated_forecaster,
        custom_df_history=df_pre,
    )

    planned_dishes_list = [
        {
            "dish_id": item.dish_id,
            "dish_name": item.dish_name,
            "category": item.category,
            "unit": item.unit,
            "per_head_rate": item.per_head_rate,
            "planned_cooking_qty": item.planned_quantity,
            "batch_size": item.batch_size,
            "expected_surplus": item.expected_surplus_qty,
            "run_out_risk": item.run_out_risk_label,
            "explanation": item.explanation,
        }
        for item in plan_res.dishes
    ]

    # Return frozen blind state — outcome fields REMAIN STRICTLY NONE
    return BlindForecastState(
        meal_id=target_meal.id,
        meal_date=target_meal.date,
        meal_type=target_meal.meal_type,
        is_synthetic=target_meal.is_synthetic,
        service_level=service_level,
        hostel_strength=hostel_strength,
        pre_cutoff_meals_count=pre_count,
        is_eligible=True,
        ineligibility_reason=None,
        h_hat=forecast_res.h_hat,
        h_lo=forecast_res.h_lo,
        h_hi=forecast_res.h_hi,
        h_q=plan_res.planning_headcount,
        baseline_lag7=b_lag7,
        baseline_trailing_avg=b_trailing,
        top_drivers=forecast_res.top_drivers,
        explanation=forecast_res.explanation,
        planned_dishes=planned_dishes_list,
        frozen_timestamp=datetime.now(timezone.utc).isoformat(),
        is_revealed=False,
    )


def reveal_blind_forecast(
    session: Session,
    frozen_state: BlindForecastState,
) -> BlindForecastState:
    """Stage 3: Reveal actual measured outcome and compare against the previously frozen forecast.

    CRITICAL INTEGRITY GUARD:
    Does NOT recompute or regenerate the frozen forecast, interval, or plan.
    Only loads the actual measured values from the database and calculates the comparison metrics.
    """
    if not frozen_state.is_eligible:
        return frozen_state

    target_meal = session.execute(
        select(Meal).where(Meal.id == frozen_state.meal_id)
    ).scalar_one_or_none()

    if not target_meal:
        frozen_state.is_revealed = True
        frozen_state.evaluation_summary = "Meal record could not be found for outcome association."
        return frozen_state

    actual_headcount = target_meal.headcount
    error = frozen_state.h_hat - actual_headcount if frozen_state.h_hat is not None else None
    abs_error = abs(error) if error is not None else None
    inside = (
        bool(frozen_state.h_lo <= actual_headcount <= frozen_state.h_hi)
        if (frozen_state.h_lo is not None and frozen_state.h_hi is not None)
        else None
    )

    lag7_err = (
        frozen_state.baseline_lag7 - actual_headcount
        if frozen_state.baseline_lag7 is not None
        else None
    )
    trailing_err = (
        frozen_state.baseline_trailing_avg - actual_headcount
        if frozen_state.baseline_trailing_avg is not None
        else None
    )

    # Load actual dish records
    dish_logs_stmt = (
        select(DishLog, Dish)
        .join(Dish, DishLog.dish_id == Dish.id)
        .where(
            DishLog.meal_id == target_meal.id,
            DishLog.is_synthetic == frozen_state.is_synthetic,
        )
    )
    actual_dish_rows = session.execute(dish_logs_stmt).all()

    actual_map = {row.DishLog.dish_id: (row.DishLog, row.Dish) for row in actual_dish_rows}
    dish_outcomes: List[Dict[str, Any]] = []
    shortage_found = False

    for p in frozen_state.planned_dishes:
        did = p["dish_id"]
        if did in actual_map:
            dlog, dish = actual_map[did]
            c_qty = float(dlog.cooked_qty) if dlog.cooked_qty is not None else 0.0
            l_qty = float(dlog.leftover_qty) if dlog.leftover_qty is not None else 0.0
            ran_out = bool(dlog.ran_out == 1)
            diff = round(c_qty - p["planned_cooking_qty"], 2)
            if ran_out:
                shortage_found = True

            dish_outcomes.append({
                "dish_id": did,
                "dish_name": dish.name,
                "unit": dish.unit,
                "planned_qty": p["planned_cooking_qty"],
                "actual_cooked_qty": c_qty,
                "diff_qty": diff,
                "actual_leftover_qty": l_qty,
                "actual_ran_out": ran_out,
                "shortage_risk": bool(p["planned_cooking_qty"] < (c_qty - l_qty)),
            })
        else:
            dish_outcomes.append({
                "dish_id": did,
                "dish_name": p["dish_name"],
                "unit": p["unit"],
                "planned_qty": p["planned_cooking_qty"],
                "actual_cooked_qty": None,
                "diff_qty": None,
                "actual_leftover_qty": None,
                "actual_ran_out": False,
                "shortage_risk": False,
            })

    # Prepare honest evaluation narrative
    if abs_error is not None:
        direction = "overestimated" if error > 0 else ("underestimated" if error < 0 else "hit exactly")
        cov_text = "inside the 80% uncertainty interval" if inside else "outside the 80% interval"
        eval_summary = (
            f"Forecast {direction} actual attendance by {abs_error} students "
            f"(Predicted {frozen_state.h_hat} vs Actual {actual_headcount}). "
            f"The actual result was {cov_text} [{frozen_state.h_lo}, {frozen_state.h_hi}]."
        )
    else:
        eval_summary = "Evaluation metrics unavailable."

    # Populate revealed fields while keeping frozen forecast unaltered
    frozen_state.is_revealed = True
    frozen_state.actual_headcount = actual_headcount
    frozen_state.forecast_error = error
    frozen_state.abs_forecast_error = abs_error
    frozen_state.inside_interval = inside
    frozen_state.baseline_lag7_error = lag7_err
    frozen_state.baseline_trailing_error = trailing_err
    frozen_state.dish_outcomes = dish_outcomes
    frozen_state.actual_shortage_occurred = shortage_found
    frozen_state.evaluation_summary = eval_summary

    return frozen_state
