"""MessWise - Waste Intelligence & Analytics Engine (Module D: D1-D3).

Implements operational intelligence specified in PLAN.md Section 5 (Module D) & Section 9.1:
- D1: KPI Dashboard (leftover quantity, waste %, meals logged, service level, forecast error, cost transparency)
- D2: Pattern Charts (waste by weekday, meal type, dish, and headcount/waste trends)
- D3: Dish Performance Ranking (highest waste, operational performers, honest review hypotheses)

Adheres strictly to synthetic/real data separation.
Never fabricates cost or popularity data.
All metrics computed directly from database records.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from messwise.db import AuditLog, Dish, DishLog, Meal, Override, Prediction


# Weekday order and labels for Indian institutional mess operations
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MEAL_TYPES_ORDER = ["breakfast", "lunch", "snacks", "dinner"]


@dataclass
class KPISummary:
    """Structured operational KPIs for institutional kitchen waste intelligence (D1)."""

    total_leftover_kg: float
    total_cooked_kg: float
    waste_percentage: float
    total_meals_count: int
    total_headcount_served: int
    total_dish_logs_count: int
    service_level_achieved: float
    shortage_incidents_count: int
    forecast_wape: Optional[float]
    forecast_mae: Optional[float]
    forecast_eval_count: int
    cost_currency: str
    cost_estimate_rupees: Optional[float]
    cost_status_note: str
    popularity_status_note: str
    is_synthetic: int
    date_range_start: Optional[str]
    date_range_end: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_kpi_summary(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> KPISummary:
    """Compute verified operational KPIs from kitchen records (D1).

    Honest definitions:
    - Leftover kg: sum of leftover_qty for weight/volume records (1L ~ 1kg standard approx for gravies/rice).
    - Waste rate: (total leftover kg / total cooked kg) * 100.
    - Service level: 1 - (dish_meals with ran_out == 1 / total dish_meals).
    - Forecast error: WAPE/MAE on evaluated predictions only.
    - Cost: None / unavailable because ingredient unit costs are not entered in core schema.
    """
    # Base query for meals
    meal_stmt = select(Meal).where(Meal.is_synthetic == is_synthetic)
    if start_date:
        meal_stmt = meal_stmt.where(Meal.date >= start_date)
    if end_date:
        meal_stmt = meal_stmt.where(Meal.date <= end_date)

    meals = session.execute(meal_stmt.order_by(Meal.date.asc())).scalars().all()
    meal_ids = [m.id for m in meals]

    if not meal_ids:
        return KPISummary(
            total_leftover_kg=0.0,
            total_cooked_kg=0.0,
            waste_percentage=0.0,
            total_meals_count=0,
            total_headcount_served=0,
            total_dish_logs_count=0,
            service_level_achieved=1.0,
            shortage_incidents_count=0,
            forecast_wape=None,
            forecast_mae=None,
            forecast_eval_count=0,
            cost_currency="INR",
            cost_estimate_rupees=None,
            cost_status_note="Cost estimation unavailable: ingredient purchase prices not configured.",
            popularity_status_note="Student rating data unavailable: low waste reflects operational clearance, not popularity.",
            is_synthetic=is_synthetic,
            date_range_start=start_date,
            date_range_end=end_date,
        )

    # Dish logs query
    dish_log_stmt = (
        select(DishLog)
        .where(DishLog.meal_id.in_(meal_ids))
        .where(DishLog.is_synthetic == is_synthetic)
    )
    dish_logs = session.execute(dish_log_stmt).scalars().all()

    # Weight and volume normalization (kg and L treated as 1:1 bulk gravies; counts excluded from kg sum)
    cooked_kg = sum(
        log.cooked_qty for log in dish_logs if log.unit in ("kg", "L")
    )
    leftover_kg = sum(
        log.leftover_qty for log in dish_logs if log.unit in ("kg", "L")
    )

    waste_pct = (leftover_kg / cooked_kg * 100.0) if cooked_kg > 0 else 0.0
    total_headcount = sum(m.headcount for m in meals)

    shortages = sum(1 for log in dish_logs if log.ran_out == 1)
    service_level = (
        (1.0 - (shortages / len(dish_logs))) if dish_logs else 1.0
    )

    # Predictions query for forecast evaluation in selected window
    pred_stmt = (
        select(Prediction)
        .where(Prediction.is_synthetic == is_synthetic)
        .where(Prediction.actual_headcount.isnot(None))
    )
    if start_date:
        pred_stmt = pred_stmt.where(Prediction.meal_date >= start_date)
    if end_date:
        pred_stmt = pred_stmt.where(Prediction.meal_date <= end_date)

    evaluated_preds = session.execute(pred_stmt).scalars().all()
    abs_errors = []
    actual_headcounts = []
    for p in evaluated_preds:
        if p.actual_headcount is not None and p.h_hat is not None:
            # Prefer stored abs_error if present, otherwise calculate exact |actual - h_hat|
            err = p.abs_error if p.abs_error is not None else abs(float(p.actual_headcount) - float(p.h_hat))
            abs_errors.append(float(err))
            actual_headcounts.append(float(p.actual_headcount))

    if abs_errors and actual_headcounts:
        total_actual = sum(actual_headcounts)
        wape = (sum(abs_errors) / total_actual) if total_actual > 0 else 0.0
        mae = float(np.mean(abs_errors))
        eval_count = len(abs_errors)
    else:
        wape = None
        mae = None
        eval_count = 0

    dates_present = [m.date for m in meals]
    actual_start = min(dates_present) if dates_present else start_date
    actual_end = max(dates_present) if dates_present else end_date

    return KPISummary(
        total_leftover_kg=round(float(leftover_kg), 1),
        total_cooked_kg=round(float(cooked_kg), 1),
        waste_percentage=round(float(waste_pct), 1),
        total_meals_count=len(meals),
        total_headcount_served=int(total_headcount),
        total_dish_logs_count=len(dish_logs),
        service_level_achieved=round(float(service_level), 3),
        shortage_incidents_count=int(shortages),
        forecast_wape=round(float(wape), 3) if wape is not None else None,
        forecast_mae=round(float(mae), 1) if mae is not None else None,
        forecast_eval_count=eval_count,
        cost_currency="INR",
        cost_estimate_rupees=None,
        cost_status_note="Cost estimation unavailable: ingredient purchase prices not configured.",
        popularity_status_note="Student rating data unavailable: low waste reflects operational clearance, not popularity.",
        is_synthetic=is_synthetic,
        date_range_start=actual_start,
        date_range_end=actual_end,
    )


# -----------------------------------------------------------------------------
# D2: Pattern Breakdown Aggregations
# -----------------------------------------------------------------------------

def aggregate_waste_by_weekday(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Aggregate waste metrics by day of the week (D2)."""
    meal_stmt = select(Meal).where(Meal.is_synthetic == is_synthetic)
    if start_date:
        meal_stmt = meal_stmt.where(Meal.date >= start_date)
    if end_date:
        meal_stmt = meal_stmt.where(Meal.date <= end_date)

    meals = session.execute(meal_stmt).scalars().all()
    if not meals:
        return pd.DataFrame(columns=["weekday_name", "leftover_kg", "cooked_kg", "waste_pct", "meal_count"])

    meal_map = {m.id: m for m in meals}
    dish_logs = session.execute(
        select(DishLog)
        .where(DishLog.meal_id.in_(list(meal_map.keys())))
        .where(DishLog.is_synthetic == is_synthetic)
    ).scalars().all()

    # Bucket by weekday (0=Monday .. 6=Sunday)
    weekday_data: Dict[int, Dict[str, float]] = {
        i: {"leftover_kg": 0.0, "cooked_kg": 0.0, "meal_ids": set()}
        for i in range(7)
    }

    for log in dish_logs:
        m = meal_map.get(log.meal_id)
        if not m:
            continue
        try:
            dt = pd.to_datetime(m.date)
            w = dt.weekday()
        except Exception:
            w = 0

        weekday_data[w]["meal_ids"].add(m.id)
        if log.unit in ("kg", "L"):
            weekday_data[w]["cooked_kg"] += log.cooked_qty
            weekday_data[w]["leftover_kg"] += log.leftover_qty

    rows = []
    for w in range(7):
        info = weekday_data[w]
        c = info["cooked_kg"]
        l = info["leftover_kg"]
        pct = (l / c * 100.0) if c > 0 else 0.0
        rows.append({
            "weekday_index": w,
            "weekday_name": WEEKDAY_NAMES[w],
            "leftover_kg": round(l, 1),
            "cooked_kg": round(c, 1),
            "waste_pct": round(pct, 1),
            "meal_count": len(info["meal_ids"]),
        })

    return pd.DataFrame(rows)


def aggregate_waste_by_meal_type(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Aggregate waste metrics by meal type slot (D2)."""
    meal_stmt = select(Meal).where(Meal.is_synthetic == is_synthetic)
    if start_date:
        meal_stmt = meal_stmt.where(Meal.date >= start_date)
    if end_date:
        meal_stmt = meal_stmt.where(Meal.date <= end_date)

    meals = session.execute(meal_stmt).scalars().all()
    if not meals:
        return pd.DataFrame(columns=["meal_type", "leftover_kg", "cooked_kg", "waste_pct", "meal_count"])

    meal_map = {m.id: m for m in meals}
    dish_logs = session.execute(
        select(DishLog)
        .where(DishLog.meal_id.in_(list(meal_map.keys())))
        .where(DishLog.is_synthetic == is_synthetic)
    ).scalars().all()

    type_data: Dict[str, Dict[str, float]] = {
        m_t: {"leftover_kg": 0.0, "cooked_kg": 0.0, "meal_ids": set()}
        for m_t in MEAL_TYPES_ORDER
    }

    for log in dish_logs:
        m = meal_map.get(log.meal_id)
        if not m:
            continue
        m_type = m.meal_type.lower()
        if m_type not in type_data:
            type_data[m_type] = {"leftover_kg": 0.0, "cooked_kg": 0.0, "meal_ids": set()}

        type_data[m_type]["meal_ids"].add(m.id)
        if log.unit in ("kg", "L"):
            type_data[m_type]["cooked_kg"] += log.cooked_qty
            type_data[m_type]["leftover_kg"] += log.leftover_qty

    rows = []
    for m_t in MEAL_TYPES_ORDER:
        info = type_data.get(m_t, {"leftover_kg": 0.0, "cooked_kg": 0.0, "meal_ids": set()})
        c = info["cooked_kg"]
        l = info["leftover_kg"]
        pct = (l / c * 100.0) if c > 0 else 0.0
        rows.append({
            "meal_type": m_t.title(),
            "leftover_kg": round(l, 1),
            "cooked_kg": round(c, 1),
            "waste_pct": round(pct, 1),
            "meal_count": len(info["meal_ids"]),
        })

    return pd.DataFrame(rows)


def aggregate_waste_by_dish(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """Aggregate total waste and waste rate by individual dish (D2)."""
    meal_stmt = select(Meal).where(Meal.is_synthetic == is_synthetic)
    if start_date:
        meal_stmt = meal_stmt.where(Meal.date >= start_date)
    if end_date:
        meal_stmt = meal_stmt.where(Meal.date <= end_date)

    meals = session.execute(meal_stmt).scalars().all()
    if not meals:
        return pd.DataFrame(columns=["dish_name", "category", "unit", "total_leftover", "total_cooked", "waste_pct", "observations"])

    meal_ids = [m.id for m in meals]
    dish_logs = session.execute(
        select(DishLog)
        .where(DishLog.meal_id.in_(meal_ids))
        .where(DishLog.is_synthetic == is_synthetic)
    ).scalars().all()

    dish_ids = list(set(log.dish_id for log in dish_logs))
    dishes = session.execute(select(Dish).where(Dish.id.in_(dish_ids))).scalars().all()
    dish_name_map = {d.id: d.name for d in dishes}
    dish_cat_map = {d.id: d.category for d in dishes}

    dish_stats: Dict[int, Dict[str, Any]] = {}
    for log in dish_logs:
        d_id = log.dish_id
        if d_id not in dish_stats:
            dish_stats[d_id] = {
                "dish_name": dish_name_map.get(d_id, f"Dish #{d_id}"),
                "category": dish_cat_map.get(d_id, "main"),
                "unit": log.unit,
                "total_leftover": 0.0,
                "total_cooked": 0.0,
                "observations": 0,
                "ran_out_count": 0,
            }
        dish_stats[d_id]["total_leftover"] += log.leftover_qty
        dish_stats[d_id]["total_cooked"] += log.cooked_qty
        dish_stats[d_id]["observations"] += 1
        if log.ran_out == 1:
            dish_stats[d_id]["ran_out_count"] += 1

    rows = []
    for d_id, data in dish_stats.items():
        c = data["total_cooked"]
        l = data["total_leftover"]
        pct = (l / c * 100.0) if c > 0 else 0.0
        rows.append({
            "dish_name": data["dish_name"],
            "category": data["category"],
            "unit": data["unit"],
            "total_leftover": round(l, 1),
            "total_cooked": round(c, 1),
            "waste_pct": round(pct, 1),
            "observations": data["observations"],
            "ran_out_count": data["ran_out_count"],
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="total_leftover", ascending=False).head(top_n).reset_index(drop=True)
    return df


def aggregate_waste_trends(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Aggregate chronological daily waste and turnout trend series (D2)."""
    meal_stmt = select(Meal).where(Meal.is_synthetic == is_synthetic)
    if start_date:
        meal_stmt = meal_stmt.where(Meal.date >= start_date)
    if end_date:
        meal_stmt = meal_stmt.where(Meal.date <= end_date)

    meals = session.execute(meal_stmt.order_by(Meal.date.asc(), Meal.id.asc())).scalars().all()
    if not meals:
        return pd.DataFrame(columns=["date", "meal_type", "headcount", "leftover_kg", "cooked_kg", "waste_pct"])

    meal_map = {m.id: m for m in meals}
    dish_logs = session.execute(
        select(DishLog)
        .where(DishLog.meal_id.in_(list(meal_map.keys())))
        .where(DishLog.is_synthetic == is_synthetic)
    ).scalars().all()

    meal_leftover: Dict[int, float] = {m.id: 0.0 for m in meals}
    meal_cooked: Dict[int, float] = {m.id: 0.0 for m in meals}

    for log in dish_logs:
        if log.unit in ("kg", "L"):
            meal_leftover[log.meal_id] += log.leftover_qty
            meal_cooked[log.meal_id] += log.cooked_qty

    rows = []
    for m in meals:
        c = meal_cooked[m.id]
        l = meal_leftover[m.id]
        pct = (l / c * 100.0) if c > 0 else 0.0
        rows.append({
            "date": m.date,
            "meal_type": m.meal_type.title(),
            "headcount": m.headcount,
            "leftover_kg": round(l, 1),
            "cooked_kg": round(c, 1),
            "waste_pct": round(pct, 1),
        })

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# D3: Dish Performance Ranking & Honest Operational Review
# -----------------------------------------------------------------------------

@dataclass
class DishRankingItem:
    """Detailed dish performance summary item (D3)."""

    dish_name: str
    category: str
    unit: str
    total_cooked: float
    total_leftover: float
    waste_percentage: float
    observations_count: int
    ran_out_count: int
    recommendation_note: str


def compute_dish_performance_rankings(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Derive performance ranking and operational suggestions grounded in measured data (D3).

    Strict Data Honesty Rule:
    - Does NOT claim low-waste dishes are 'most loved' or popular without student survey/rating data.
    - Low waste is strictly reported as high operational clearance.
    - Identifies top-waste items for recipe/batch review.
    - Labels suggestions as operational hypotheses.
    """
    df_dishes = aggregate_waste_by_dish(
        session=session,
        is_synthetic=is_synthetic,
        start_date=start_date,
        end_date=end_date,
        top_n=100,  # All dishes
    )

    if df_dishes.empty:
        return {
            "highest_waste_dishes": [],
            "operational_performers": [],
            "review_candidates": [],
            "total_dishes_evaluated": 0,
            "data_limitation_note": "No dish log entries found for the selected environment and date window.",
        }

    items: List[DishRankingItem] = []
    for _, row in df_dishes.iterrows():
        pct = float(row["waste_pct"])
        n_obs = int(row["observations"])
        ran_out = int(row["ran_out_count"])
        d_name = str(row["dish_name"])

        # Grounded operational suggestion
        if n_obs < 3:
            note = f"Preliminary observation ({n_obs} meals). Collect more kitchen data before menu modifications."
        elif ran_out > 0:
            note = f"Shortage recorded in {ran_out} meal(s). Increase service-level safety margin to protect student coverage."
        elif pct > 12.0:
            note = f"High leftover rate ({pct:.1f}%). Suggestion: Review batch preparation size or adjust standard portion multiplier."
        elif pct < 5.0:
            note = f"High operational clearance ({pct:.1f}% leftover). Maintained adequate supply without significant surplus."
        else:
            note = f"Balanced operational profile ({pct:.1f}% leftover, {n_obs} meals observed)."

        items.append(
            DishRankingItem(
                dish_name=d_name,
                category=str(row["category"]),
                unit=str(row["unit"]),
                total_cooked=float(row["total_cooked"]),
                total_leftover=float(row["total_leftover"]),
                waste_percentage=pct,
                observations_count=n_obs,
                ran_out_count=ran_out,
                recommendation_note=note,
            )
        )

    # Top wasted dishes (by total leftover volume)
    highest_waste = sorted(items, key=lambda x: x.total_leftover, reverse=True)[:5]

    # Operational performers (lowest waste % among items with at least 2 observations)
    qualified = [x for x in items if x.observations_count >= 2]
    performers = sorted(qualified, key=lambda x: x.waste_percentage)[:5]

    # Review candidates (waste > 10% or ran out > 0)
    review_candidates = [
        x for x in items
        if (x.waste_percentage >= 10.0 or x.ran_out_count > 0) and x.observations_count >= 2
    ]

    return {
        "highest_waste_dishes": [asdict(x) for x in highest_waste],
        "operational_performers": [asdict(x) for x in performers],
        "review_candidates": [asdict(x) for x in review_candidates],
        "total_dishes_evaluated": len(items),
        "data_limitation_note": (
            "Operational note: Low leftovers reflect kitchen clearance and portion alignment. "
            "Popularity ratings are not collected in this version and should not be inferred solely from waste data."
        ),
    }


# =============================================================================
# D4: ANOMALY DETECTION (ROBUST Z-SCORE & IQR METHODOLOGY)
# =============================================================================

@dataclass
class WasteAnomaly:
    """Statistical anomaly flag for dish waste percentage (D4)."""

    log_id: int
    dish_id: int
    dish_name: str
    category: str
    meal_id: int
    meal_date: str
    meal_type: str
    observed_waste_pct: float
    historical_median_pct: float
    mad_val: float
    z_score: float
    is_anomaly: bool
    status: str  # "evaluated", "insufficient_history"
    num_observations: int
    threshold: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def detect_dish_waste_anomalies(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    z_threshold: float = 3.5,
    min_history: int = 6,
) -> List[WasteAnomaly]:
    """Detect dish-level waste anomalies using robust z-scores (D4).

    Formula from PLAN.md Section 8.9:
    z = 0.6745 * (x - median) / MAD
    where x = (leftover_qty / cooked_qty) * 100.
    Flagged when |z| > z_threshold (default 3.5).
    Requires at least min_history (default 6) historical observations,
    otherwise flagged as 'insufficient_history'.
    """
    # 1. Fetch all dish logs with meal context in the given environment
    stmt = (
        select(DishLog, Meal, Dish)
        .join(Meal, DishLog.meal_id == Meal.id)
        .join(Dish, DishLog.dish_id == Dish.id)
        .where(
            DishLog.is_synthetic == is_synthetic,
            Meal.is_synthetic == is_synthetic,
        )
    )
    if start_date:
        stmt = stmt.where(Meal.date >= start_date)
    if end_date:
        stmt = stmt.where(Meal.date <= end_date)
    stmt = stmt.order_by(Meal.date.desc(), DishLog.id.desc())

    records = session.execute(stmt).all()
    if not records:
        return []

    # 2. Group historical waste rates by (dish_id, meal_type)
    # First, collect all history across meals in this environment
    hist_stmt = (
        select(DishLog.dish_id, Meal.meal_type, DishLog.cooked_qty, DishLog.leftover_qty)
        .join(Meal, DishLog.meal_id == Meal.id)
        .where(
            DishLog.is_synthetic == is_synthetic,
            Meal.is_synthetic == is_synthetic,
        )
    )
    hist_rows = session.execute(hist_stmt).all()
    history_by_dish: Dict[Tuple[int, str], List[float]] = {}
    for d_id, m_type, c_qty, l_qty in hist_rows:
        if c_qty is not None and c_qty > 0 and l_qty is not None and l_qty >= 0:
            rate = float(l_qty / c_qty * 100.0)
            key = (d_id, m_type)
            history_by_dish.setdefault(key, []).append(rate)

    results: List[WasteAnomaly] = []

    for dl, m, dish in records:
        if dl.cooked_qty is None or dl.cooked_qty <= 0 or dl.leftover_qty is None or dl.leftover_qty < 0:
            continue

        waste_pct = float(dl.leftover_qty / dl.cooked_qty * 100.0)
        key = (dish.id, m.meal_type)
        dish_history = history_by_dish.get(key, [])

        if len(dish_history) < min_history:
            results.append(
                WasteAnomaly(
                    log_id=dl.id,
                    dish_id=dish.id,
                    dish_name=dish.name,
                    category=dish.category,
                    meal_id=m.id,
                    meal_date=m.date,
                    meal_type=m.meal_type,
                    observed_waste_pct=round(waste_pct, 1),
                    historical_median_pct=round(float(np.median(dish_history)), 1) if dish_history else 0.0,
                    mad_val=0.0,
                    z_score=0.0,
                    is_anomaly=False,
                    status="insufficient_history",
                    num_observations=len(dish_history),
                    threshold=z_threshold,
                    explanation=f"Insufficient history ({len(dish_history)} past meals < {min_history} required).",
                )
            )
            continue

        arr = np.array(dish_history, dtype=float)
        median_val = float(np.median(arr))
        abs_dev = np.abs(arr - median_val)
        mad_val = float(np.median(abs_dev))
        if mad_val <= 0.001:
            # Fallback to mean absolute deviation when >50% of history is identical
            mad_val = float(np.mean(abs_dev))

        if mad_val > 0.001:
            z = 0.6745 * (waste_pct - median_val) / mad_val
        else:
            z = 0.0

        is_anom = bool(abs(z) > z_threshold)
        explanation = (
            f"Waste {waste_pct:.1f}% vs median {median_val:.1f}% "
            f"(MAD={mad_val:.1f}, robust z={z:.2f}, threshold ±{z_threshold:g})."
        )

        results.append(
            WasteAnomaly(
                log_id=dl.id,
                dish_id=dish.id,
                dish_name=dish.name,
                category=dish.category,
                meal_id=m.id,
                meal_date=m.date,
                meal_type=m.meal_type,
                observed_waste_pct=round(waste_pct, 1),
                historical_median_pct=round(median_val, 1),
                mad_val=round(mad_val, 2),
                z_score=round(z, 2),
                is_anomaly=is_anom,
                status="evaluated",
                num_observations=len(dish_history),
                threshold=z_threshold,
                explanation=explanation,
            )
        )

    return results


# =============================================================================
# D5: ROOT-CAUSE HYPOTHESES (RULE-BASED OPERATIONAL PATTERNS)
# =============================================================================

@dataclass
class RootCauseHypothesis:
    """Operational root-cause pattern hypothesis for manager review (D5)."""

    meal_id: int
    meal_date: str
    meal_type: str
    pattern_observed: str
    hypothesis_shown: str
    suggested_action: str
    confidence_label: str  # "Hypothesis for Manager Review"
    trigger_metric: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_root_cause_hypotheses(
    session: Session,
    meal_id: int,
) -> List[RootCauseHypothesis]:
    """Generate transparent rule-based explanations for observed kitchen patterns (D5).

    Specification from PLAN.md Section 8.9:
    1. High leftover on all dishes + headcount far below forecast -> Attendance shortfall.
    2. High leftover on one dish + low per-head rate -> Dish is unpopular / portion mismatch.
    3. Cooked quantity well above plan + high leftover -> Over-cooking versus recommendation.
    4. Dish ran out + headcount above upper band -> Unexpected surge.
    5. Waste spike on a day after a holiday/weekend -> Return-pattern effect.
    """
    meal = session.execute(select(Meal).where(Meal.id == meal_id)).scalar_one_or_none()
    if not meal:
        return []

    # Fetch dish logs
    dish_logs_stmt = (
        select(DishLog, Dish)
        .join(Dish, DishLog.dish_id == Dish.id)
        .where(DishLog.meal_id == meal_id)
    )
    logs_and_dishes = session.execute(dish_logs_stmt).all()
    if not logs_and_dishes:
        return []

    # Fetch corresponding prediction if exists
    pred = session.execute(
        select(Prediction)
        .where(
            Prediction.meal_date == meal.date,
            Prediction.meal_type == meal.meal_type,
            Prediction.is_synthetic == meal.is_synthetic,
        )
    ).scalars().first()

    # Fetch overrides for this meal
    overrides = session.execute(
        select(Override).where(Override.meal_id == meal_id)
    ).scalars().all()
    overrides_by_dish = {ov.dish_id: ov for ov in overrides}

    hypotheses: List[RootCauseHypothesis] = []

    # Calculate dish-level waste percentages
    dish_waste_pcts: Dict[int, float] = {}
    dish_names: Dict[int, str] = {}
    ran_out_dishes: List[str] = []

    for dl, dish in logs_and_dishes:
        dish_names[dish.id] = dish.name
        if dl.cooked_qty and dl.cooked_qty > 0 and dl.leftover_qty is not None:
            pct = float(dl.leftover_qty / dl.cooked_qty * 100.0)
            dish_waste_pcts[dish.id] = pct
        if dl.ran_out == 1:
            ran_out_dishes.append(dish.name)

    avg_waste = float(np.mean(list(dish_waste_pcts.values()))) if dish_waste_pcts else 0.0

    # Pattern 1: Attendance shortfall
    if pred and pred.h_hat > 0 and meal.headcount > 0:
        headcount_gap = pred.h_hat - meal.headcount
        if headcount_gap > 35 and avg_waste > 12.0:
            hypotheses.append(
                RootCauseHypothesis(
                    meal_id=meal.id,
                    meal_date=meal.date,
                    meal_type=meal.meal_type,
                    pattern_observed=f"High leftover across all dishes (avg {avg_waste:.1f}%) + headcount ({meal.headcount}) far below forecast ({int(pred.h_hat)}).",
                    hypothesis_shown="Attendance shortfall (forecast miss or unlogged campus event)",
                    suggested_action="Check event calendar; widen uncertainty interval for similar days.",
                    confidence_label="Hypothesis for Manager Review",
                    trigger_metric=f"Headcount shortfall: -{headcount_gap} students, Avg Waste: {avg_waste:.1f}%",
                )
            )

    # Pattern 2: Dish is unpopular / portion mismatch (single high waste item)
    if len(dish_waste_pcts) >= 2:
        for d_id, w_pct in dish_waste_pcts.items():
            other_pcts = [p for other_id, p in dish_waste_pcts.items() if other_id != d_id]
            median_other = float(np.median(other_pcts)) if other_pcts else 0.0
            if w_pct >= 20.0 and median_other <= 10.0:
                hypotheses.append(
                    RootCauseHypothesis(
                        meal_id=meal.id,
                        meal_date=meal.date,
                        meal_type=meal.meal_type,
                        pattern_observed=f"High leftover on {dish_names.get(d_id, 'dish')} ({w_pct:.1f}%) while other dishes averaged {median_other:.1f}%.",
                        hypothesis_shown=f"Dish {dish_names.get(d_id, 'dish')} has recipe fatigue, low student appetite, or excessive standard portioning.",
                        suggested_action=f"Review recipe for {dish_names.get(d_id, 'dish')}; consider smaller batch preparation or portion spoon adjustment.",
                        confidence_label="Hypothesis for Manager Review",
                        trigger_metric=f"Dish Waste: {w_pct:.1f}% vs Menu Median: {median_other:.1f}%",
                    )
                )

    # Pattern 3: Over-cooking versus recommendation (override)
    for dl, dish in logs_and_dishes:
        ov = overrides_by_dish.get(dish.id)
        if ov and ov.recommended_qty > 0:
            if ov.final_qty > ov.recommended_qty * 1.15:
                w_pct = dish_waste_pcts.get(dish.id, 0.0)
                if w_pct > 12.0:
                    delta = round(ov.final_qty - ov.recommended_qty, 1)
                    hypotheses.append(
                        RootCauseHypothesis(
                            meal_id=meal.id,
                            meal_date=meal.date,
                            meal_type=meal.meal_type,
                            pattern_observed=f"Cooked quantity for {dish.name} ({ov.final_qty:g}) exceeded recommendation ({ov.recommended_qty:g}) by +{delta:g}, followed by {w_pct:.1f}% leftover.",
                            hypothesis_shown="Over-cooking versus recommendation (override)",
                            suggested_action=f"Review staff override reason ('{ov.reason}'); share the cost of the override with kitchen staff.",
                            confidence_label="Hypothesis for Manager Review",
                            trigger_metric=f"Override Delta: +{delta:g}, Resulting Waste: {w_pct:.1f}%",
                        )
                    )

    # Pattern 4: Unexpected surge
    if ran_out_dishes and pred and pred.h_hi > 0:
        if meal.headcount > pred.h_hi:
            surge_heads = meal.headcount - int(pred.h_hi)
            hypotheses.append(
                RootCauseHypothesis(
                    meal_id=meal.id,
                    meal_date=meal.date,
                    meal_type=meal.meal_type,
                    pattern_observed=f"Dishes ran out ({', '.join(ran_out_dishes)}) while actual headcount ({meal.headcount}) exceeded upper forecast band ({int(pred.h_hi)}).",
                    hypothesis_shown="Unexpected surge in attendance beyond conformal upper confidence limit",
                    suggested_action="Use top-up emergency cooking plan; log the root cause in the hostel event calendar.",
                    confidence_label="Hypothesis for Manager Review",
                    trigger_metric=f"Headcount Surge: +{surge_heads} above upper band ({int(pred.h_hi)})",
                )
            )

    # Pattern 5: Return-pattern effect (Monday waste spike)
    try:
        from datetime import date
        d_obj = date.fromisoformat(meal.date)
        if d_obj.weekday() == 0 and avg_waste > 15.0:  # Monday
            hypotheses.append(
                RootCauseHypothesis(
                    meal_id=meal.id,
                    meal_date=meal.date,
                    meal_type=meal.meal_type,
                    pattern_observed=f"High menu waste ({avg_waste:.1f}%) on Monday meal following the weekend.",
                    hypothesis_shown="Return-pattern effect (fluctuating student return times and irregular weekend attendance)",
                    suggested_action="Flag Monday as low-confidence day next week; widen planning buffers conservatively.",
                    confidence_label="Hypothesis for Manager Review",
                    trigger_metric=f"Monday Avg Waste: {avg_waste:.1f}%",
                )
            )
    except Exception:
        pass

    return hypotheses


# =============================================================================
# D6: OVERRIDE ANALYTICS (STAFF OVERRIDE PATTERNS & OUTCOMES)
# =============================================================================

@dataclass
class OverrideAnalyticsResult:
    """Analysis of historical kitchen overrides and outcome tracking (D6)."""

    total_overrides: int
    override_rate_pct: float
    reasons_breakdown: Dict[str, int]
    avg_delta_qty: float
    net_positive_overrides: int
    net_negative_overrides: int
    evaluated_outcomes_count: int
    outcome_comparison_note: str
    is_synthetic: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_override_analytics(
    session: Session,
    is_synthetic: int = 1,
) -> OverrideAnalyticsResult:
    """Analyze kitchen staff overrides to recommended quantities (D6).

    Tracks override frequency, recorded reasons, average deltas,
    and associated outcomes without claiming unverified improvements.
    """
    stmt = (
        select(Override)
        .where(Override.is_synthetic == is_synthetic)
        .order_by(Override.ts.desc())
    )
    overrides = session.execute(stmt).scalars().all()

    if not overrides:
        return OverrideAnalyticsResult(
            total_overrides=0,
            override_rate_pct=0.0,
            reasons_breakdown={},
            avg_delta_qty=0.0,
            net_positive_overrides=0,
            net_negative_overrides=0,
            evaluated_outcomes_count=0,
            outcome_comparison_note="No manager overrides recorded in this environment.",
            is_synthetic=is_synthetic,
        )

    # Count total predictions or meal dish items in this environment to compute override rate
    total_dish_logs_count = session.execute(
        select(func.count(DishLog.id)).where(DishLog.is_synthetic == is_synthetic)
    ).scalar_one() or 1

    total_ov = len(overrides)
    ov_rate = min(100.0, (total_ov / total_dish_logs_count) * 100.0)

    reasons_map: Dict[str, int] = {}
    deltas = []
    pos_count = 0
    neg_count = 0

    for ov in overrides:
        r_text = (ov.reason or "Unspecified reason").strip()
        reasons_map[r_text] = reasons_map.get(r_text, 0) + 1
        delta = float(ov.final_qty - ov.recommended_qty)
        deltas.append(delta)
        if delta > 0:
            pos_count += 1
        elif delta < 0:
            neg_count += 1

    avg_delta = float(np.mean(deltas)) if deltas else 0.0

    # Matched outcomes count (where meal_id and dish_id match a recorded DishLog)
    matched_logs = []
    for ov in overrides:
        if ov.meal_id and ov.dish_id:
            dl = session.execute(
                select(DishLog).where(DishLog.meal_id == ov.meal_id, DishLog.dish_id == ov.dish_id)
            ).scalars().first()
            if dl and dl.cooked_qty and dl.cooked_qty > 0:
                matched_logs.append(dl)

    n_outcomes = len(matched_logs)
    if n_outcomes < 5:
        outcome_note = (
            f"Sample size ({n_outcomes} matched post-override outcomes) is insufficient "
            f"for statistical comparison of waste reduction versus automated plans."
        )
    else:
        waste_rates = [(dl.leftover_qty / dl.cooked_qty * 100.0) for dl in matched_logs]
        avg_ov_waste = float(np.mean(waste_rates))
        outcome_note = (
            f"Evaluated {n_outcomes} post-override outcomes: "
            f"average resulting waste was {avg_ov_waste:.1f}%."
        )

    return OverrideAnalyticsResult(
        total_overrides=total_ov,
        override_rate_pct=round(ov_rate, 1),
        reasons_breakdown=reasons_map,
        avg_delta_qty=round(avg_delta, 2),
        net_positive_overrides=pos_count,
        net_negative_overrides=neg_count,
        evaluated_outcomes_count=n_outcomes,
        outcome_comparison_note=outcome_note,
        is_synthetic=is_synthetic,
    )


# =============================================================================
# D7: AUTOMATIC WEEKLY OPERATIONAL BRIEF (TEMPLATE-BASED REPORTING)
# =============================================================================

@dataclass
class WeeklyOperationalBrief:
    """Concise template-based weekly operational intelligence brief (D7)."""

    report_title: str
    date_range_label: str
    environment_label: str
    total_meals_logged: int
    total_headcount_served: int
    total_cooked_kg: float
    total_leftover_kg: float
    overall_waste_pct: float
    service_level_achieved: float
    shortage_incidents: int
    forecast_wape_display: str
    anomalies_detected_count: int
    top_wasted_dishes: List[str]
    chief_operational_hypotheses: List[str]
    brief_narrative: str
    data_quality_warning: str
    is_synthetic: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_weekly_operational_brief(
    session: Session,
    is_synthetic: int = 1,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> WeeklyOperationalBrief:
    """Generate concise weekly operational summary directly from logged records (D7).

    Template-based generation requires no external LLM API keys.
    Maintains strict real versus synthetic data provenance.
    """
    env_label = "Synthetic Development Data (Demonstration Only)" if is_synthetic == 1 else "Real Pilot Data"

    # Compute operational KPIs
    kpi = compute_kpi_summary(session, is_synthetic=is_synthetic, start_date=start_date, end_date=end_date)
    date_label = f"{kpi.date_range_start or 'Start'} to {kpi.date_range_end or 'Latest'}"

    # Check for empty state
    if kpi.total_meals_count == 0:
        return WeeklyOperationalBrief(
            report_title="Weekly Operational Intelligence Brief",
            date_range_label=date_label,
            environment_label=env_label,
            total_meals_logged=0,
            total_headcount_served=0,
            total_cooked_kg=0.0,
            total_leftover_kg=0.0,
            overall_waste_pct=0.0,
            service_level_achieved=1.0,
            shortage_incidents=0,
            forecast_wape_display="N/A (0 predictions)",
            anomalies_detected_count=0,
            top_wasted_dishes=[],
            chief_operational_hypotheses=[],
            brief_narrative="No meal logs exist in the database for the selected date window.",
            data_quality_warning="Insufficient records: log kitchen meals to generate an operational brief.",
            is_synthetic=is_synthetic,
        )

    # Dish performance ranking (D3)
    ranking = compute_dish_performance_rankings(session, is_synthetic=is_synthetic, start_date=start_date, end_date=end_date)
    top_dishes = [d["dish_name"] for d in ranking.get("highest_waste_dishes", [])[:3]]

    # Detect anomalies (D4)
    anomalies = detect_dish_waste_anomalies(session, is_synthetic=is_synthetic, start_date=start_date, end_date=end_date)
    flagged_anomalies = [a for a in anomalies if a.is_anomaly]

    # Collect hypotheses from recent meals (D5)
    recent_meals = session.execute(
        select(Meal)
        .where(Meal.is_synthetic == is_synthetic)
        .order_by(Meal.date.desc())
        .limit(5)
    ).scalars().all()

    hypotheses_list = []
    for rm in recent_meals:
        h_items = generate_root_cause_hypotheses(session, rm.id)
        for hi in h_items:
            hypotheses_list.append(f"{hi.pattern_observed} -> {hi.hypothesis_shown}")

    # Forecast accuracy display
    wape_str = f"{kpi.forecast_wape:.1%}" if kpi.forecast_wape is not None else "N/A"

    # Narrative construction
    narrative = (
        f"During the reporting period ({date_label}), the mess logged {kpi.total_meals_count} meals "
        f"serving {kpi.total_headcount_served} students. Total food prepared was {kpi.total_cooked_kg:.1f} kg, "
        f"with {kpi.total_leftover_kg:.1f} kg leftovers, representing an overall waste rate of {kpi.waste_percentage:.1f}%. "
        f"Operational service level was maintained at {kpi.service_level_achieved:.1%} "
        f"({kpi.shortage_incidents_count} ran-out incident{'s' if kpi.shortage_incidents_count != 1 else ''}). "
        f"Rolling forecast WAPE was {wape_str} across {kpi.forecast_eval_count} evaluated meals. "
        f"Statistical anomaly screening flagged {len(flagged_anomalies)} dish log{'s' if len(flagged_anomalies) != 1 else ''} "
        f"exceeding robust z-score threshold (z > 3.5)."
    )

    warning = (
        "Demonstration data notice: These metrics are derived from synthetic development records and do not reflect physical kitchen operations."
        if is_synthetic == 1
        else "Real pilot operations: Verified against actual kitchen weight measurements and entrance counts."
    )

    return WeeklyOperationalBrief(
        report_title="Weekly Operational Intelligence Brief",
        date_range_label=date_label,
        environment_label=env_label,
        total_meals_logged=kpi.total_meals_count,
        total_headcount_served=kpi.total_headcount_served,
        total_cooked_kg=round(kpi.total_cooked_kg, 1),
        total_leftover_kg=round(kpi.total_leftover_kg, 1),
        overall_waste_pct=round(kpi.waste_percentage, 1),
        service_level_achieved=round(kpi.service_level_achieved, 4),
        shortage_incidents=kpi.shortage_incidents_count,
        forecast_wape_display=wape_str,
        anomalies_detected_count=len(flagged_anomalies),
        top_wasted_dishes=top_dishes,
        chief_operational_hypotheses=hypotheses_list[:4],
        brief_narrative=narrative,
        data_quality_warning=warning,
        is_synthetic=is_synthetic,
    )

