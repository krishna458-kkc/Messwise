"""MessWise - Pilot Evidence & Evaluation Engine (Module E: E2).

Implements the pilot evaluation methodology specified in PLAN.md Section 5 (Module E),
Section 9.1 & 9.2 (Statistical treatment of the pilot):
- E2: Matched weekday x meal before/after comparison
- Event-day separation (events, exams, holidays)
- Nonparametric bootstrap 95% confidence intervals (fixed seed 42)
- Transparent sample sizes (n_baseline, n_pilot, matched pairs m)
- Service level achieved during both periods

Data-Honesty Rule:
When real pilot records == 0, honestly reports 'Insufficient real pilot data'.
Never fabricates savings or claims real-world effectiveness from synthetic data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from messwise.db import DishLog, Meal


@dataclass
class MatchedPairComparison:
    """Represents a matched weekday x meal comparison between baseline and pilot."""

    weekday_name: str
    meal_type: str
    baseline_date: str
    pilot_date: str
    baseline_leftover_kg: float
    pilot_leftover_kg: float
    waste_avoided_kg: float  # baseline - pilot
    percentage_reduction: float


@dataclass
class PilotEvidenceReport:
    """Structured before/after pilot comparison report (E2)."""

    has_sufficient_data: bool
    status_message: str
    is_synthetic: int
    environment_label: str

    baseline_window_start: Optional[str]
    baseline_window_end: Optional[str]
    pilot_window_start: Optional[str]
    pilot_window_end: Optional[str]

    baseline_meals_count: int
    pilot_meals_count: int
    matched_pairs_count: int
    event_days_excluded_count: int

    baseline_avg_leftover_kg: Optional[float]
    pilot_avg_leftover_kg: Optional[float]
    mean_waste_avoided_kg_per_meal: Optional[float]
    percentage_waste_reduction: Optional[float]

    bootstrap_ci_95_lower_kg: Optional[float]
    bootstrap_ci_95_upper_kg: Optional[float]
    bootstrap_resamples: int

    baseline_service_level: Optional[float]
    pilot_service_level: Optional[float]
    baseline_shortages: int
    pilot_shortages: int

    matched_pairs: List[Dict[str, Any]]
    limitations_and_caveats: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_pilot_evidence_report(
    session: Session,
    baseline_start: str,
    baseline_end: str,
    pilot_start: str,
    pilot_end: str,
    is_synthetic: int = 0,
    random_seed: int = 42,
    n_bootstraps: int = 1000,
) -> PilotEvidenceReport:
    """Compute matched weekday x meal before/after evidence report (E2 per PLAN.md Section 9).

    Strict Data-Honesty:
    - If is_synthetic == 0 and real meals == 0, returns insufficient data state.
    - If either period has < 2 non-event meals, flags insufficient sample size.
    - Excludes event/exam/holiday days from matched baseline comparison.
    """
    env_label = "Real Pilot Data" if is_synthetic == 0 else "Synthetic Development Data (Demonstration Only)"

    # Query meals in both periods, strictly requiring verified_pilot status for real pilot evidence
    query = (
        select(Meal)
        .where(Meal.is_synthetic == is_synthetic)
        .where(Meal.date >= min(baseline_start, pilot_start))
        .where(Meal.date <= max(baseline_end, pilot_end))
    )
    if is_synthetic == 0:
        query = query.where(Meal.verification_status == "verified_pilot")

    all_meals = session.execute(
        query.order_by(Meal.date.asc(), Meal.id.asc())
    ).scalars().all()

    # Guard: Check total records for environment
    if not all_meals:
        if is_synthetic == 0:
            unverified_count = session.execute(
                select(func.count(Meal.id)).where(
                    Meal.is_synthetic == 0,
                    Meal.verification_status != "verified_pilot",
                )
            ).scalar() or 0
            if unverified_count > 0:
                msg = (
                    f"Insufficient Verified Pilot Data: {unverified_count} non-synthetic meals exist but are "
                    "classified as unverified test entries. Only operator-verified pilot measurements can be "
                    "evaluated for formal before/after pilot evidence."
                )
            else:
                msg = (
                    "Insufficient Real Pilot Data: 0 real operational meals recorded in kitchen. "
                    "The pilot before/after impact report requires kitchen staff to log meals via Kitchen mode "
                    "before real baseline vs pilot effectiveness can be evaluated."
                )
        else:
            msg = "No demonstration records found in the specified date range."

        return PilotEvidenceReport(
            has_sufficient_data=False,
            status_message=msg,
            is_synthetic=is_synthetic,
            environment_label=env_label,
            baseline_window_start=baseline_start,
            baseline_window_end=baseline_end,
            pilot_window_start=pilot_start,
            pilot_window_end=pilot_end,
            baseline_meals_count=0,
            pilot_meals_count=0,
            matched_pairs_count=0,
            event_days_excluded_count=0,
            baseline_avg_leftover_kg=None,
            pilot_avg_leftover_kg=None,
            mean_waste_avoided_kg_per_meal=None,
            percentage_waste_reduction=None,
            bootstrap_ci_95_lower_kg=None,
            bootstrap_ci_95_upper_kg=None,
            bootstrap_resamples=n_bootstraps,
            baseline_service_level=None,
            pilot_service_level=None,
            baseline_shortages=0,
            pilot_shortages=0,
            matched_pairs=[],
            limitations_and_caveats=[
                "Zero operational records available for evaluation in this environment.",
                "Real pilot data must be logged during actual mess operations.",
            ],
        )

    # Segment meals into baseline and pilot
    baseline_meals = [m for m in all_meals if baseline_start <= m.date <= baseline_end]
    pilot_meals = [m for m in all_meals if pilot_start <= m.date <= pilot_end]

    if len(baseline_meals) < 2 or len(pilot_meals) < 2:
        return PilotEvidenceReport(
            has_sufficient_data=False,
            status_message=(
                f"Insufficient observation count: found {len(baseline_meals)} baseline meal(s) and "
                f"{len(pilot_meals)} pilot meal(s). At least 2 meals per window are required for comparison."
            ),
            is_synthetic=is_synthetic,
            environment_label=env_label,
            baseline_window_start=baseline_start,
            baseline_window_end=baseline_end,
            pilot_window_start=pilot_start,
            pilot_window_end=pilot_end,
            baseline_meals_count=len(baseline_meals),
            pilot_meals_count=len(pilot_meals),
            matched_pairs_count=0,
            event_days_excluded_count=0,
            baseline_avg_leftover_kg=None,
            pilot_avg_leftover_kg=None,
            mean_waste_avoided_kg_per_meal=None,
            percentage_waste_reduction=None,
            bootstrap_ci_95_lower_kg=None,
            bootstrap_ci_95_upper_kg=None,
            bootstrap_resamples=n_bootstraps,
            baseline_service_level=None,
            pilot_service_level=None,
            baseline_shortages=0,
            pilot_shortages=0,
            matched_pairs=[],
            limitations_and_caveats=[
                "Minimum observation count (>= 2 meals per period) not met.",
                "Collect additional consistent measurement periods before running statistical comparisons.",
            ],
        )

    # Fetch dish logs for both sets
    all_meal_ids = [m.id for m in baseline_meals + pilot_meals]
    dish_logs = session.execute(
        select(DishLog)
        .where(DishLog.meal_id.in_(all_meal_ids))
        .where(DishLog.is_synthetic == is_synthetic)
    ).scalars().all()

    # Map dish logs by meal_id
    logs_by_meal: Dict[int, List[DishLog]] = {m_id: [] for m_id in all_meal_ids}
    for log in dish_logs:
        logs_by_meal[log.meal_id].append(log)

    def meal_leftover_kg(m_id: int) -> float:
        return sum(
            l.leftover_qty for l in logs_by_meal.get(m_id, [])
            if l.unit in ("kg", "L")
        )

    def count_shortages(m_ids: List[int]) -> int:
        return sum(
            1 for m_id in m_ids for l in logs_by_meal.get(m_id, [])
            if l.ran_out == 1
        )

    def total_logs(m_ids: List[int]) -> int:
        return sum(len(logs_by_meal.get(m_id, [])) for m_id in m_ids)

    # Separate event days
    event_excluded = 0
    clean_baseline: List[Meal] = []
    for m in baseline_meals:
        if m.event_flag or m.exam_flag or m.holiday_flag:
            event_excluded += 1
        else:
            clean_baseline.append(m)

    clean_pilot: List[Meal] = []
    for m in pilot_meals:
        if m.event_flag or m.exam_flag or m.holiday_flag:
            event_excluded += 1
        else:
            clean_pilot.append(m)

    # Match weekday x meal pairs
    # Weekday from date string: 0=Monday .. 6=Sunday
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def slot_key(m: Meal) -> Tuple[int, str]:
        dt = pd.to_datetime(m.date)
        return (dt.weekday(), m.meal_type.lower())

    baseline_by_slot: Dict[Tuple[int, str], Meal] = {slot_key(m): m for m in clean_baseline}
    pilot_by_slot: Dict[Tuple[int, str], Meal] = {slot_key(m): m for m in clean_pilot}

    matched_pairs: List[MatchedPairComparison] = []
    diffs_kg: List[float] = []

    common_slots = set(baseline_by_slot.keys()) & set(pilot_by_slot.keys())
    for slot in sorted(common_slots):
        m_base = baseline_by_slot[slot]
        m_pilot = pilot_by_slot[slot]

        base_kg = meal_leftover_kg(m_base.id)
        pilot_kg = meal_leftover_kg(m_pilot.id)
        delta_kg = base_kg - pilot_kg
        pct_red = (delta_kg / base_kg * 100.0) if base_kg > 0 else 0.0

        w_name = weekday_names[slot[0]]
        matched_pairs.append(
            MatchedPairComparison(
                weekday_name=w_name,
                meal_type=slot[1].title(),
                baseline_date=m_base.date,
                pilot_date=m_pilot.date,
                baseline_leftover_kg=round(base_kg, 1),
                pilot_leftover_kg=round(pilot_kg, 1),
                waste_avoided_kg=round(delta_kg, 1),
                percentage_reduction=round(pct_red, 1),
            )
        )
        diffs_kg.append(delta_kg)

    if not diffs_kg:
        return PilotEvidenceReport(
            has_sufficient_data=False,
            status_message="No matching weekday x meal pairs found between the baseline and pilot periods.",
            is_synthetic=is_synthetic,
            environment_label=env_label,
            baseline_window_start=baseline_start,
            baseline_window_end=baseline_end,
            pilot_window_start=pilot_start,
            pilot_window_end=pilot_end,
            baseline_meals_count=len(baseline_meals),
            pilot_meals_count=len(pilot_meals),
            matched_pairs_count=0,
            event_days_excluded_count=event_excluded,
            baseline_avg_leftover_kg=None,
            pilot_avg_leftover_kg=None,
            mean_waste_avoided_kg_per_meal=None,
            percentage_waste_reduction=None,
            bootstrap_ci_95_lower_kg=None,
            bootstrap_ci_95_upper_kg=None,
            bootstrap_resamples=n_bootstraps,
            baseline_service_level=None,
            pilot_service_level=None,
            baseline_shortages=0,
            pilot_shortages=0,
            matched_pairs=[],
            limitations_and_caveats=[
                "No overlapping meal slots (same weekday and meal type) between selected periods.",
                "Select matching date ranges (e.g. Week 1 vs Week 2).",
            ],
        )

    # Core statistical aggregates
    avg_base = float(np.mean([p.baseline_leftover_kg for p in matched_pairs]))
    avg_pilot = float(np.mean([p.pilot_leftover_kg for p in matched_pairs]))
    mean_avoided = float(np.mean(diffs_kg))
    pct_reduction = (mean_avoided / avg_base * 100.0) if avg_base > 0 else 0.0

    # Nonparametric Bootstrap 95% Confidence Interval (Fixed Seed)
    rng = np.random.RandomState(random_seed)
    diffs_arr = np.array(diffs_kg)
    m_samples = len(diffs_arr)

    boot_means = []
    for _ in range(n_bootstraps):
        resample = rng.choice(diffs_arr, size=m_samples, replace=True)
        boot_means.append(float(np.mean(resample)))

    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))

    # Service-level metrics
    base_ids = [m.id for m in baseline_meals]
    pilot_ids = [m.id for m in pilot_meals]

    base_short = count_shortages(base_ids)
    pilot_short = count_shortages(pilot_ids)
    base_logs_cnt = total_logs(base_ids)
    pilot_logs_cnt = total_logs(pilot_ids)

    base_sl = (1.0 - (base_short / base_logs_cnt)) if base_logs_cnt > 0 else 1.0
    pilot_sl = (1.0 - (pilot_short / pilot_logs_cnt)) if pilot_logs_cnt > 0 else 1.0

    caveats = [
        f"Matched {len(matched_pairs)} weekday x meal slot pairs across periods.",
        f"Excluded {event_excluded} event/exam/holiday meals to prevent confounding.",
        "Bootstrap 95% confidence interval computed with 1,000 resamples (seed 42).",
    ]
    if is_synthetic == 1:
        caveats.insert(
            0,
            "🧪 SYNTHETIC DATA NOTICE: This evaluation is performed strictly on synthetic demonstration records "
            "for algorithmic verification. It does NOT represent real kitchen outcomes."
        )

    return PilotEvidenceReport(
        has_sufficient_data=True,
        status_message=f"Successfully analyzed {len(matched_pairs)} matched meal slot pairs.",
        is_synthetic=is_synthetic,
        environment_label=env_label,
        baseline_window_start=baseline_start,
        baseline_window_end=baseline_end,
        pilot_window_start=pilot_start,
        pilot_window_end=pilot_end,
        baseline_meals_count=len(baseline_meals),
        pilot_meals_count=len(pilot_meals),
        matched_pairs_count=len(matched_pairs),
        event_days_excluded_count=event_excluded,
        baseline_avg_leftover_kg=round(avg_base, 1),
        pilot_avg_leftover_kg=round(avg_pilot, 1),
        mean_waste_avoided_kg_per_meal=round(mean_avoided, 1),
        percentage_waste_reduction=round(pct_reduction, 1),
        bootstrap_ci_95_lower_kg=round(ci_lower, 1),
        bootstrap_ci_95_upper_kg=round(ci_upper, 1),
        bootstrap_resamples=n_bootstraps,
        baseline_service_level=round(float(base_sl), 3),
        pilot_service_level=round(float(pilot_sl), 3),
        baseline_shortages=int(base_short),
        pilot_shortages=int(pilot_short),
        matched_pairs=[asdict(p) for p in matched_pairs],
        limitations_and_caveats=caveats,
    )
