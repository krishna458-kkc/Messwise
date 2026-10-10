"""MessWise Cooking Quantity Planner & Consumption Learning Engine (Module B: B1-B5).

Implements specifications from PLAN.md Section 5 (Module B), Section 8.2, 8.3, and Appendix C:
- B1: Per-dish quantity plan: Quantity_d = H_q * r_d * (1 + prep_loss), with practical batch rounding.
- B2: Per-head consumption learning: served = cooked - leftover, rate = served / headcount.
      Robust median over recent meals (default last 10), split by meal type.
- B3: Service-level slider: Manager selects safety level (90%, 95%, 99%), driving planning
      headcount H_q deterministically from Step 2 forecast empirical residuals.
- B4: Cost-Aware Optimiser (Newsvendor logic): Service level derived from the ratio of shortage
      penalty to waste cost (q* = Cu / (Cu + Co) = k / (k + 1)). Dish criticality tiers:
      staples 99% (k=99), main curries 95% (k=19), sides/salads 90% (k=9). Safety floor: default 90%.
      Manager override with recorded reason.
- B5: Kaplan-Meier Shortage-Aware Consumption Learning: Historical meals where a dish ran out
      are treated as right-censored lower bounds on appetite rather than exact demand. Non-parametric
      product-limit estimator yields appetite quantile r_q where S(r_q) <= 1 - q. Fallback rules
      for small history (n < 3, n < 6) or heavy censoring.

Reusable Python business logic for Streamlit Planner UI, FastAPI /plan endpoint, and test suites.
Never fabricates data. Strictly separates synthetic (is_synthetic=1) and real pilot (is_synthetic=0) records.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from messwise.db import (
    Dish,
    DishLog,
    Meal,
    get_or_create_dish,
)
from messwise.forecast import (
    DEFAULT_HOSTEL_STRENGTH,
    ForecastResult,
    HeadcountForecaster,
    get_trained_forecaster,
)
from messwise.validation import normalize_meal_type, normalize_unit

# Standard institutional portion defaults (used only as fallback when history is insufficient)
DEFAULT_CATEGORY_PORTIONS: Dict[Tuple[str, str], float] = {
    ("staple", "kg"): 0.085,     # Rice: ~85g per student
    ("staple", "count"): 2.5,    # Roti/Puri: ~2.5 pieces per student
    ("main", "kg"): 0.110,       # Sabzi/Paneer/Chicken: ~110g per student
    ("main", "L"): 0.120,        # Dal/Sambar/Curry: ~120ml per student
    ("side", "kg"): 0.050,       # Chutney/Salad: ~50g per student
    ("side", "L"): 0.075,        # Curd/Raita: ~75ml per student
    ("side", "count"): 1.0,      # Fruit/Egg/Sweet: ~1 count per student
}

# Standard practical batch sizes by unit (manager configurable)
DEFAULT_BATCH_SIZES: Dict[str, float] = {
    "kg": 5.0,    # Cook in 5 kg batches/pots
    "L": 5.0,     # Cook in 5 L vessels
    "count": 10.0 # Cook in batches of 10
}

# Documented Dish Criticality Policy Tiers (PLAN.md Section 8.3 & Appendix C)
DEFAULT_CRITICALITY_TIERS: Dict[str, Dict[str, Any]] = {
    "staple": {
        "k": 99.0,
        "service_level": 0.99,
        "description": "Staples (rice, roti): near-zero shortage tolerance (99% target, k=99)",
    },
    "main": {
        "k": 19.0,
        "service_level": 0.95,
        "description": "Main curries / dal: balanced operational protection (95% target, k=19)",
    },
    "side": {
        "k": 9.0,
        "service_level": 0.90,
        "description": "Sides / salads / raita: lean protection (90% target, k=9)",
    },
}

DEFAULT_SAFETY_FLOOR: float = 0.90


@dataclass
class DishCostConfig:
    """Manager-configured cost parameters or overrides for a dish (B4)."""

    shortage_cost_cu: Optional[float] = None
    waste_cost_co: Optional[float] = None
    cost_ratio_k: Optional[float] = None
    safety_floor: float = DEFAULT_SAFETY_FLOOR
    manager_override: Optional[float] = None
    override_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NewsvendorResult:
    """Outcome of B4 Newsvendor cost-aware optimisation for a dish or category."""

    category: str
    criticality_tier: str
    cu: Optional[float]
    co: Optional[float]
    cost_ratio_k: float
    economic_service_level: float
    safety_floor: float
    effective_service_level: float
    is_policy_default: bool
    is_floor_applied: bool
    manager_override: Optional[float]
    override_reason: Optional[str]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KaplanMeierResult:
    """Non-parametric Kaplan-Meier consumption estimation result (B5)."""

    dish_id: int
    dish_name: str
    category: str
    meal_type: str
    unit: str
    estimated_rate: float
    target_quantile: float
    method: str  # "kaplan_meier_quantile", "uncensored_median_bump", "censored_lower_bound_bump", "portion_default_fallback", "kaplan_meier_tail_bump"
    confidence_status: str  # "high", "moderate", "low"
    num_observations: int
    num_exact: int
    num_censored: int
    num_ambiguous: int
    is_fallback: bool
    fallback_reason: Optional[str]
    timeline: List[float] = field(default_factory=list)
    survival_curve: List[float] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DishObservation:
    """Historical record of consumption for a specific meal and dish."""

    meal_date: str
    meal_id: int
    headcount: int
    cooked_qty: float
    leftover_qty: float
    served_qty: float
    rate: float
    ran_out: bool
    is_censored: bool  # True when dish ran out (lower bound for B5 Kaplan-Meier)
    is_synthetic: int
    is_ambiguous: bool = False  # True when leftover==0 but ran_out==0 (not explicitly flagged)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsumptionRateRecord:
    """Learned consumption rate and data sufficiency metrics for a dish (B2 & B5)."""

    dish_id: int
    dish_name: str
    category: str
    meal_type: str
    unit: str
    estimated_rate: float
    num_observations: int
    num_usable_observations: int
    num_ran_out: int
    latest_rate: Optional[float]
    confidence_status: str  # "high", "moderate", "low"
    is_fallback: bool
    fallback_reason: Optional[str]
    batch_size: Optional[float]
    target_quantile: float = 0.95
    estimation_method: str = "kaplan_meier"
    num_exact: int = 0
    num_ambiguous: int = 0
    criticality_tier: str = "main"
    km_result: Optional[KaplanMeierResult] = None
    newsvendor_result: Optional[NewsvendorResult] = None
    observations: List[DishObservation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["observations"] = [o.to_dict() for o in self.observations]
        if self.km_result:
            d["km_result"] = self.km_result.to_dict()
        if self.newsvendor_result:
            d["newsvendor_result"] = self.newsvendor_result.to_dict()
        return d


@dataclass
class MonteCarloDemandResult:
    """Joint Monte-Carlo demand simulation result combining headcount & appetite (B6)."""

    dish_id: int
    dish_name: str
    unit: str
    service_level: float
    num_simulations: int
    theo_cook_quantity: float
    planned_cook_quantity: float
    expected_demand: float
    demand_p10: float
    demand_p50: float
    demand_p90: float
    demand_p95: float
    demand_p99: float
    p_runout: float
    expected_surplus: float
    is_fallback: bool
    fallback_reason: Optional[str]
    method: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DishPlanItem:
    """Per-dish cooking quantity recommendation (B1, B4, B5, B6)."""

    dish_id: int
    dish_name: str
    category: str
    unit: str
    per_head_rate: float
    prep_loss_pct: float
    batch_size: Optional[float]
    theo_quantity: float
    planned_quantity: float
    expected_served_qty: float
    expected_surplus_qty: float
    run_out_risk_label: str  # "Low", "Moderate", "Elevated"
    confidence_status: str  # "high", "moderate", "low"
    is_fallback_rate: bool
    explanation: str
    criticality_tier: str = "main"
    effective_service_level: float = 0.95
    planning_headcount: int = 0
    estimation_method: str = "kaplan_meier_quantile"
    num_observations: int = 0
    num_exact: int = 0
    num_censored: int = 0
    is_cost_aware: bool = False
    cost_ratio_k: Optional[float] = None
    safety_floor: float = DEFAULT_SAFETY_FLOOR
    is_floor_applied: bool = False
    manager_override: Optional[float] = None
    override_reason: Optional[str] = None
    newsvendor_explanation: Optional[str] = None
    km_explanation: Optional[str] = None
    mc_demand: Optional[MonteCarloDemandResult] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.mc_demand:
            d["mc_demand"] = self.mc_demand.to_dict()
        return d


@dataclass
class MealPlanResult:
    """Complete operational cooking plan for an upcoming meal (B1-B6)."""

    target_date: str
    meal_type: str
    service_level: float
    forecast_h_hat: int
    planning_headcount: int
    hostel_strength: int
    prep_loss_pct: float
    headcount_buffer: int
    run_out_risk_pct: float
    dishes: List[DishPlanItem]
    total_planned_kg: float
    total_expected_surplus_kg: float
    data_basis_label: str  # "Real pilot data", "Synthetic development data", "Mixed data"
    real_obs_count: int
    synthetic_obs_count: int
    summary_explanation: str
    is_synthetic: int
    plan_mode: str = "manual"  # "manual" (B3) or "cost_aware" (B4)
    safety_floor: float = DEFAULT_SAFETY_FLOOR
    cost_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dishes"] = [dish.to_dict() for dish in self.dishes]
        return d


def get_fallback_rate_for_dish(category: str, unit: str, standard_portion: Optional[float] = None) -> float:
    """Determine safe portion default when history is absent or insufficient."""
    if standard_portion is not None and standard_portion > 0:
        return float(standard_portion)

    clean_unit = normalize_unit(unit)
    clean_cat = (category or "").strip().lower()
    if (clean_cat, clean_unit) in DEFAULT_CATEGORY_PORTIONS:
        return DEFAULT_CATEGORY_PORTIONS[(clean_cat, clean_unit)]

    # Fallback by unit
    if clean_unit == "kg":
        return 0.100
    elif clean_unit == "L":
        return 0.120
    else:
        return 1.0


def calculate_newsvendor_service_level(
    category: str,
    cu: Optional[float] = None,
    co: Optional[float] = None,
    k: Optional[float] = None,
    safety_floor: float = DEFAULT_SAFETY_FLOOR,
    manager_override: Optional[float] = None,
    override_reason: Optional[str] = None,
) -> NewsvendorResult:
    """Calculate cost-minimizing Newsvendor service level q* (B4).

    Formula (PLAN.md Section 8.3):
        q* = Cu / (Cu + Co)
    Or equivalently with k = Cu / Co:
        q* = k / (k + 1)

    Order of operations:
    1. Calculate economic target q* if valid positive costs/ratio exist.
       If invalid, non-positive, or missing, fall back to documented criticality tiers:
       - staple: 99% (k = 99)
       - main: 95% (k = 19)
       - side: 90% (k = 9)
       - other/unknown: fallback to main (95%)
    2. Apply documented safety floor (default 0.90).
    3. Apply manager override if supplied (with recorded reason).
    """
    clean_cat = (category or "main").strip().lower()

    # Identify criticality tier
    if clean_cat in DEFAULT_CRITICALITY_TIERS:
        crit_tier = clean_cat
    elif any(s in clean_cat for s in ["rice", "roti", "chapati", "puri", "bread", "staple"]):
        crit_tier = "staple"
    elif any(s in clean_cat for s in ["salad", "chutney", "papad", "pickle", "curd", "raita", "side"]):
        crit_tier = "side"
    else:
        crit_tier = "main"

    tier_default = DEFAULT_CRITICALITY_TIERS[crit_tier]
    safe_floor = float(np.clip(safety_floor if safety_floor is not None else DEFAULT_SAFETY_FLOOR, 0.50, 0.999))

    valid_cu_co = (
        cu is not None
        and co is not None
        and isinstance(cu, (int, float))
        and isinstance(co, (int, float))
        and cu > 0
        and co > 0
    )
    valid_k = k is not None and isinstance(k, (int, float)) and k > 0

    if valid_cu_co:
        calc_k = float(cu / co)
        raw_econ_q = float(cu / (cu + co))
        is_policy = False
        cost_basis = f"Configured cost estimates: shortage Cu={cu:g}, waste Co={co:g} (ratio k={calc_k:.1f})"
    elif valid_k:
        calc_k = float(k)
        raw_econ_q = float(calc_k / (calc_k + 1.0))
        is_policy = False
        cost_basis = f"Configured cost ratio k={calc_k:.1f}"
    else:
        # Policy default honest fallback
        calc_k = float(tier_default["k"])
        raw_econ_q = float(tier_default["service_level"])
        is_policy = True
        cost_basis = f"Policy criticality default for '{crit_tier}' tier (k={calc_k:g})"

    raw_econ_q = float(np.clip(raw_econ_q, 0.50, 0.999))

    # Apply safety floor
    if raw_econ_q < safe_floor:
        floored_q = safe_floor
        floor_applied = True
    else:
        floored_q = raw_econ_q
        floor_applied = False

    # Apply manager override
    if manager_override is not None and isinstance(manager_override, (int, float)):
        eff_q = float(np.clip(manager_override, 0.50, 0.999))
        active_override = eff_q
        clean_reason = (override_reason or "Manager manual override").strip()
    else:
        eff_q = floored_q
        active_override = None
        clean_reason = None

    # Construct plain-language explanation
    explanation_parts = []
    if is_policy:
        explanation_parts.append(
            f"{clean_cat.title()} is classified in the '{crit_tier}' criticality tier. "
            f"No verified economic cost inputs are configured, so the {raw_econ_q:.0%} target "
            f"comes from documented criticality policy defaults rather than measured ingredient prices."
        )
    else:
        explanation_parts.append(
            f"For {clean_cat.title()}, {cost_basis} yields an unconstrained Newsvendor target of {raw_econ_q:.1%}."
        )

    if floor_applied:
        explanation_parts.append(
            f"Safety protection floor ({safe_floor:.0%}) raised the economic target from {raw_econ_q:.1%} to {floored_q:.0%}."
        )

    if active_override is not None:
        explanation_parts.append(
            f"Manager applied an explicit override to {active_override:.1%} (Reason: {clean_reason})."
        )
    else:
        explanation_parts.append(f"Effective service level: {eff_q:.1%}.")

    return NewsvendorResult(
        category=clean_cat,
        criticality_tier=crit_tier,
        cu=float(cu) if valid_cu_co else None,
        co=float(co) if valid_cu_co else None,
        cost_ratio_k=round(calc_k, 2),
        economic_service_level=round(raw_econ_q, 4),
        safety_floor=round(safe_floor, 4),
        effective_service_level=round(eff_q, 4),
        is_policy_default=is_policy,
        is_floor_applied=floor_applied,
        manager_override=round(active_override, 4) if active_override is not None else None,
        override_reason=clean_reason,
        explanation=" ".join(explanation_parts),
    )


def fit_kaplan_meier_consumption(
    rates: List[float],
    exact_flags: List[bool],
    target_quantile: float = 0.95,
    standard_portion: Optional[float] = None,
    category: str = "main",
    unit: str = "kg",
    dish_id: int = 0,
    dish_name: str = "Dish",
    meal_type: str = "lunch",
) -> KaplanMeierResult:
    """Fit Kaplan-Meier non-parametric appetite distribution accounting for right-censored shortages (B5).

    Mathematical basis (PLAN.md Section 8.2):
        r_i = served_i / headcount_i
        exact_i = ~ran_out_i (False => right-censored lower bound)
        km = KaplanMeierFitter().fit(r, event_observed=exact)
        r_q = quantile where S(r_q) <= 1 - q

    Pure-Python / NumPy product-limit implementation avoids C-extension DLL blocks under Windows App Control.

    Fallbacks:
    - n < 3: Standard portion default (confidence: low)
    - Heavy censoring (n_exact < 2 when n >= 3): Median + 10% shortage bump (confidence: low)
    - 3 <= n < 6: Uncensored median * (1 + bump) (confidence: moderate)
    - n >= 6 and KM defined: KM quantile (confidence: high if n >= 8 and n_exact >= 5 else moderate)
    - n >= 6 and KM tail undefined: Adjusted highest rate with bump (confidence: moderate)
    """
    clean_cat = (category or "main").strip().lower()
    clean_unit = normalize_unit(unit)
    clamped_q = float(np.clip(target_quantile, 0.50, 0.999))

    # Pair and filter invalid rates (must be > 0 and finite)
    valid_pairs: List[Tuple[float, bool]] = []
    for r, e in zip(rates, exact_flags):
        if r is not None and not math.isnan(r) and not math.isinf(r) and r > 0.0:
            valid_pairs.append((float(r), bool(e)))

    n = len(valid_pairs)
    n_exact = sum(1 for _, e in valid_pairs if e)
    n_censored = n - n_exact
    num_ambiguous = 0  # Provided by caller if tracking zero-leftover non-shortage records

    # 1. Fallback Rule: n < 3 (insufficient historical data)
    if n < 3:
        fallback_rate = get_fallback_rate_for_dish(clean_cat, clean_unit, standard_portion)
        portion_note = (
            f"registered portion ({standard_portion:g} {clean_unit})"
            if standard_portion and standard_portion > 0
            else f"standard institutional {clean_cat} portion ({fallback_rate:g} {clean_unit})"
        )
        reason = f"Insufficient history ({n} observations, minimum 3 required). Using {portion_note}."
        return KaplanMeierResult(
            dish_id=dish_id,
            dish_name=dish_name,
            category=clean_cat,
            meal_type=meal_type,
            unit=clean_unit,
            estimated_rate=round(fallback_rate, 4),
            target_quantile=clamped_q,
            method="portion_default_fallback",
            confidence_status="low",
            num_observations=n,
            num_exact=n_exact,
            num_censored=n_censored,
            num_ambiguous=num_ambiguous,
            is_fallback=True,
            fallback_reason=reason,
            timeline=[],
            survival_curve=[],
            explanation=reason,
        )

    # 2. Fallback Rule: Heavy Censoring (fewer than 2 exact observations out of >= 3)
    if n_exact < 2:
        all_rates = [r for r, _ in valid_pairs]
        base_rate = float(np.median(all_rates))
        bump = 0.10  # +10% shortage allowance for lower-bound observations
        adj_rate = base_rate * (1.0 + bump)
        reason = (
            f"Dish ran out in {n_censored}/{n} recent meals (heavy shortage censoring). "
            f"Observed median rate ({base_rate:.3f} {clean_unit}) is a known lower bound; "
            f"applied +{bump:.0%} shortage adjustment."
        )
        return KaplanMeierResult(
            dish_id=dish_id,
            dish_name=dish_name,
            category=clean_cat,
            meal_type=meal_type,
            unit=clean_unit,
            estimated_rate=round(adj_rate, 4),
            target_quantile=clamped_q,
            method="censored_lower_bound_bump",
            confidence_status="low",
            num_observations=n,
            num_exact=n_exact,
            num_censored=n_censored,
            num_ambiguous=num_ambiguous,
            is_fallback=True,
            fallback_reason=reason,
            timeline=[],
            survival_curve=[],
            explanation=reason,
        )

    # 3. Fallback Rule: Moderate sample size (3 <= n < 6)
    if n < 6:
        uncensored_rates = [r for r, e in valid_pairs if e]
        base_rate = float(np.median(uncensored_rates))
        # Shortage bump from history (PLAN.md Section 8.2)
        # If no meals ran out in history (n_censored == 0), bump is 0.0 (exact observations)
        if n_censored > 0:
            bump = (float(n_censored) / float(n)) * 0.10 * ((clamped_q - 0.50) / 0.49 if clamped_q > 0.50 else 1.0)
        else:
            bump = 0.0
        adj_rate = base_rate * (1.0 + bump)
        reason = (
            f"Moderate history ({n} observations < 6 threshold for full Kaplan-Meier). "
            f"Using uncensored median ({base_rate:.3f} {clean_unit})"
            + (f" with +{bump:.1%} shortage allowance from {n_censored}/{n} ran-out meals." if bump > 0 else ".")
        )
        return KaplanMeierResult(
            dish_id=dish_id,
            dish_name=dish_name,
            category=clean_cat,
            meal_type=meal_type,
            unit=clean_unit,
            estimated_rate=round(adj_rate, 4),
            target_quantile=clamped_q,
            method="uncensored_median_bump" if bump > 0 else "robust_median",
            confidence_status="moderate",
            num_observations=n,
            num_exact=n_exact,
            num_censored=n_censored,
            num_ambiguous=num_ambiguous,
            is_fallback=bool(bump > 0),
            fallback_reason=reason if bump > 0 else None,
            timeline=[],
            survival_curve=[],
            explanation=reason,
        )

    # 4. Standard Kaplan-Meier Product-Limit Estimator (n >= 6)
    # Sort distinct observation times
    sorted_pairs = sorted(valid_pairs, key=lambda x: (x[0], -int(x[1])))
    times: List[float] = []
    n_at_risk: List[int] = []
    n_events: List[int] = []

    total_pts = len(sorted_pairs)
    idx = 0
    while idx < total_pts:
        t_val = sorted_pairs[idx][0]
        events = 0
        at_risk = total_pts - idx
        while idx < total_pts and abs(sorted_pairs[idx][0] - t_val) < 1e-9:
            if sorted_pairs[idx][1]:
                events += 1
            idx += 1
        if events > 0:
            times.append(t_val)
            n_at_risk.append(at_risk)
            n_events.append(events)

    # Step-down survival function: S(t) = Prod_{t_k <= t} (1 - d_k / n_k)
    surv = 1.0
    timeline: List[float] = []
    survival_curve: List[float] = []
    for t_step, n_k, d_k in zip(times, n_at_risk, n_events):
        surv *= (1.0 - float(d_k) / float(n_k))
        timeline.append(round(t_step, 4))
        survival_curve.append(round(surv, 4))

    target_surv = 1.0 - clamped_q  # For q=0.95, target survival probability is S(r) <= 0.05
    km_quantile_val: Optional[float] = None
    for t_step, s_val in zip(timeline, survival_curve):
        if s_val <= target_surv:
            km_quantile_val = t_step
            break

    if km_quantile_val is not None:
        # Quantile successfully estimated from empirical KM curve
        conf = "high" if n >= 8 and n_exact >= 5 else "moderate"
        explanation = (
            f"Kaplan-Meier shortage-aware estimation ({n} meals, {n_exact} exact, {n_censored} ran out). "
            f"Appetite rate at {clamped_q:.0%} service level is {km_quantile_val:.3f} {clean_unit}/head."
        )
        return KaplanMeierResult(
            dish_id=dish_id,
            dish_name=dish_name,
            category=clean_cat,
            meal_type=meal_type,
            unit=clean_unit,
            estimated_rate=round(km_quantile_val, 4),
            target_quantile=clamped_q,
            method="kaplan_meier_quantile",
            confidence_status=conf,
            num_observations=n,
            num_exact=n_exact,
            num_censored=n_censored,
            num_ambiguous=num_ambiguous,
            is_fallback=False,
            fallback_reason=None,
            timeline=timeline,
            survival_curve=survival_curve,
            explanation=explanation,
        )
    else:
        # Upper tail of survival function is undefined because S(t_max) > 1 - q (censoring at upper end)
        uncensored_rates = [r for r, e in valid_pairs if e]
        base_rate = max(uncensored_rates) if uncensored_rates else float(np.median([r for r, _ in valid_pairs]))
        bump = 0.08 * ((clamped_q - 0.50) / 0.49)
        adj_rate = base_rate * (1.0 + bump)
        reason = (
            f"Kaplan-Meier survival curve upper tail undefined at q={clamped_q:.0%} due to right-censoring "
            f"(dish ran out in highest-consumption meals). Adjusted highest verified rate ({base_rate:.3f} {clean_unit}) "
            f"with +{bump:.1%} margin."
        )
        return KaplanMeierResult(
            dish_id=dish_id,
            dish_name=dish_name,
            category=clean_cat,
            meal_type=meal_type,
            unit=clean_unit,
            estimated_rate=round(adj_rate, 4),
            target_quantile=clamped_q,
            method="kaplan_meier_tail_bump",
            confidence_status="moderate",
            num_observations=n,
            num_exact=n_exact,
            num_censored=n_censored,
            num_ambiguous=num_ambiguous,
            is_fallback=True,
            fallback_reason=reason,
            timeline=timeline,
            survival_curve=survival_curve,
            explanation=reason,
        )


def compute_dish_consumption_rates(
    session: Session,
    meal_type: str,
    is_synthetic: int = 0,
    window_size: int = 10,
    dish_ids: Optional[List[int]] = None,
    before_date: Optional[str] = None,
    before_meal_id: Optional[int] = None,
    service_level: float = 0.95,
    dish_service_levels: Optional[Dict[int, float]] = None,
    **kwargs: Any,
) -> Dict[int, ConsumptionRateRecord]:
    """Compute per-head consumption rates for dishes using Kaplan-Meier shortage-aware learning (B2 & B5).

    Calculates:
        served_qty = cooked_qty - leftover_qty
        per_head_rate = served_qty / headcount

    Over recent history (default last 10 meals) split by meal_type.
    Authoritative shortage detection:
        - dl.ran_out == 1 -> right-censored observation (event_observed = False).
        - dl.ran_out == 0 -> exact observation (event_observed = True).
        - dl.leftover_qty == 0.0 with dl.ran_out == 0 -> exact observation, tracked as ambiguous.

    If before_date or before_meal_id is supplied, strictly excludes future data to prevent leakage.
    """
    norm_meal = normalize_meal_type(meal_type)

    # Fetch dish catalog
    dish_query = select(Dish)
    if dish_ids:
        dish_query = dish_query.where(Dish.id.in_(dish_ids))
    dish_catalog = session.execute(dish_query).scalars().all()
    if not dish_catalog:
        return {}

    # Query dish logs joined with meals for this meal_type and synthetic environment
    stmt = (
        select(DishLog, Meal)
        .join(Meal, DishLog.meal_id == Meal.id)
        .where(
            Meal.meal_type == norm_meal,
            DishLog.is_synthetic == is_synthetic,
            Meal.is_synthetic == is_synthetic,
        )
    )
    if before_date:
        stmt = stmt.where(Meal.date < before_date)
    elif before_meal_id:
        stmt = stmt.where(Meal.id < before_meal_id)
    stmt = stmt.order_by(Meal.date.desc(), Meal.id.desc(), DishLog.id.desc())
    logs_and_meals = session.execute(stmt).all()

    # Group valid observations by dish_id
    obs_by_dish: Dict[int, List[DishObservation]] = {d.id: [] for d in dish_catalog}

    for dl, m in logs_and_meals:
        if dl.dish_id not in obs_by_dish:
            continue

        # Data validation guards (P0 safety)
        if m.headcount <= 0:
            continue
        if dl.cooked_qty is None or dl.leftover_qty is None:
            continue
        if dl.cooked_qty < 0 or dl.leftover_qty < 0:
            continue
        if dl.leftover_qty > dl.cooked_qty:
            continue

        served = float(dl.cooked_qty - dl.leftover_qty)
        rate = float(served / m.headcount)

        # Authoritative shortage signal: ran_out == 1 is right-censored
        is_ran_out = bool(dl.ran_out == 1)
        is_censored = is_ran_out
        is_ambiguous = bool(dl.leftover_qty == 0.0 and dl.cooked_qty > 0.0 and dl.ran_out == 0)

        obs = DishObservation(
            meal_date=m.date,
            meal_id=m.id,
            headcount=m.headcount,
            cooked_qty=float(dl.cooked_qty),
            leftover_qty=float(dl.leftover_qty),
            served_qty=served,
            rate=rate,
            ran_out=is_ran_out,
            is_censored=is_censored,
            is_synthetic=dl.is_synthetic,
            is_ambiguous=is_ambiguous,
        )

        if len(obs_by_dish[dl.dish_id]) < window_size:
            obs_by_dish[dl.dish_id].append(obs)

    # Compute Kaplan-Meier shortage-aware consumption rates
    records: Dict[int, ConsumptionRateRecord] = {}

    for dish in dish_catalog:
        all_obs = obs_by_dish.get(dish.id, [])
        total_obs = len(all_obs)
        ran_out_count = sum(1 for o in all_obs if o.ran_out)
        exact_count = sum(1 for o in all_obs if not o.ran_out)
        ambiguous_count = sum(1 for o in all_obs if o.is_ambiguous)
        latest_obs_rate = all_obs[0].rate if all_obs else None

        # Determine target quantile for this dish
        target_q = (
            dish_service_levels.get(dish.id, service_level)
            if dish_service_levels is not None
            else service_level
        )

        # Fit Kaplan-Meier estimator for target quantile (B5)
        rates_list = [o.rate for o in all_obs]
        exact_flags = [not o.ran_out for o in all_obs]

        km_res = fit_kaplan_meier_consumption(
            rates=rates_list,
            exact_flags=exact_flags,
            target_quantile=target_q,
            standard_portion=dish.standard_portion,
            category=dish.category,
            unit=dish.unit,
            dish_id=dish.id,
            dish_name=dish.name,
            meal_type=norm_meal,
        )
        km_res.num_ambiguous = ambiguous_count

        # Also fit median (q=0.50) for robust per-head appetite baseline
        km_median = fit_kaplan_meier_consumption(
            rates=rates_list,
            exact_flags=exact_flags,
            target_quantile=0.50,
            standard_portion=dish.standard_portion,
            category=dish.category,
            unit=dish.unit,
            dish_id=dish.id,
            dish_name=dish.name,
            meal_type=norm_meal,
        )
        km_median.num_ambiguous = ambiguous_count

        use_quantile = kwargs.get("use_quantile_rate", False)
        chosen_rate = km_res.estimated_rate if use_quantile else km_median.estimated_rate

        records[dish.id] = ConsumptionRateRecord(
            dish_id=dish.id,
            dish_name=dish.name,
            category=dish.category,
            meal_type=norm_meal,
            unit=dish.unit,
            estimated_rate=chosen_rate,
            num_observations=total_obs,
            num_usable_observations=exact_count if exact_count > 0 else total_obs,
            num_ran_out=ran_out_count,
            latest_rate=round(latest_obs_rate, 4) if latest_obs_rate is not None else None,
            confidence_status=km_res.confidence_status,
            is_fallback=km_res.is_fallback,
            fallback_reason=km_res.fallback_reason,
            batch_size=dish.batch_size,
            target_quantile=km_res.target_quantile,
            estimation_method=km_res.method,
            num_exact=exact_count,
            num_ambiguous=ambiguous_count,
            criticality_tier=dish.criticality_tier or "main",
            km_result=km_res,
            observations=all_obs,
        )

    return records


def calculate_service_headcount(
    forecaster: HeadcountForecaster,
    forecast: ForecastResult,
    service_level: float = 0.95,
) -> Tuple[int, Dict[str, Any]]:
    """Derive planning headcount H_q from forecast uncertainty and service level (B3).

    Deterministic and testable:
    - Service level q in [0.50, 0.999] represents target coverage probability.
    - Uses empirical rolling-origin residuals from Step 2 forecasting engine.
    - Guarantees monotonicity: higher service level NEVER produces a lower planning quantity.
    """
    q = float(np.clip(service_level, 0.50, 0.999))
    h_hat = forecast.h_hat
    strength = forecast.hostel_strength if forecast.hostel_strength > 0 else DEFAULT_HOSTEL_STRENGTH

    # Check for empirical residuals from forecaster
    meal_residuals = forecaster.residuals_by_meal.get(forecast.meal_type, [])
    all_residuals = forecaster.all_residuals

    if len(meal_residuals) >= 5:
        # Empirical residual quantile specific to this meal type
        residual_margin = float(np.percentile(meal_residuals, q * 100.0))
        empirical_basis = f"{len(meal_residuals)} meal-specific residuals"
    elif len(all_residuals) >= 5:
        # Cross-meal empirical residual quantile
        residual_margin = float(np.percentile(all_residuals, q * 100.0))
        empirical_basis = f"{len(all_residuals)} cross-meal residuals"
    else:
        # Cold start: monotonic scaling based on conformal 80% interval
        z_scores = {
            0.50: 0.0,
            0.80: 1.282,
            0.90: 1.645,
            0.95: 1.960,
            0.98: 2.326,
            0.99: 2.576,
        }
        q_keys = sorted(z_scores.keys())
        z_val = float(np.interp(q, q_keys, [z_scores[k] for k in q_keys]))
        base_spread = max(15.0, strength * 0.10)
        residual_margin = float(base_spread * (z_val / 1.282))
        empirical_basis = "cold-start conformal heuristic"

    # Planning headcount H_q bounded by capacity
    raw_hq = h_hat + residual_margin
    h_q = int(min(strength, max(1, round(raw_hq))))

    headcount_buffer = max(0, h_q - h_hat)
    run_out_risk_pct = round(max(0.1, (1.0 - q) * 100.0), 1)

    trade_off = {
        "service_level": q,
        "h_hat": h_hat,
        "h_q": h_q,
        "headcount_buffer": headcount_buffer,
        "residual_margin": round(residual_margin, 1),
        "run_out_risk_pct": run_out_risk_pct,
        "empirical_basis": empirical_basis,
        "explanation": (
            f"At {q:.0%} service level, planning for {h_q} students buffers +{headcount_buffer} "
            f"over central forecast ({h_hat}). Run-out risk is ~{run_out_risk_pct}%."
        ),
    }

    return h_q, trade_off


def apply_batch_rounding(quantity: float, batch_size: Optional[float], unit: str) -> float:
    """Round theoretical cooking quantity to a practical kitchen batch size."""
    if quantity <= 0:
        return 0.0

    if batch_size is not None and batch_size > 0:
        batches = math.ceil(quantity / batch_size)
        return round(batches * batch_size, 2)

    # If unit is count, round up to whole unit
    if unit == "count":
        return float(math.ceil(quantity))

    # Default: round to 1 decimal place
    return round(quantity, 1)


def simulate_joint_demand_monte_carlo(
    h_hat: int,
    hostel_strength: int,
    residuals: List[float],
    dish_id: int,
    dish_name: str,
    unit: str,
    service_level: float,
    prep_loss_pct: float,
    learned_rate: float,
    dish_observations: Optional[List[DishObservation]] = None,
    batch_size: Optional[float] = None,
    num_simulations: int = 5000,
    random_seed: int = 42,
) -> MonteCarloDemandResult:
    """Simulate joint demand D = H * r under headcount and appetite uncertainty (B6).

    Specification from PLAN.md lines 1162-1167:
    H = H_hat + resample(conformal_residuals[meal_type], n=5000)
    r = draw(appetite_distribution[dish, meal_type], n=5000)
    D = H * r
    Q = quantile(D, q_dish) * (1 + prep_loss)
    Q = round_to_batch(Q, pot_or_tray_size)
    P_runout = mean(D > Q / (1 + prep_loss))
    E_surplus = mean(max(Q / (1 + prep_loss) - D, 0))

    Parameters:
    - random_seed: Ensures fully deterministic, reproducible output.
    - Fallback: Clearly reports when appetite observations are insufficient (< 3 observations).
    """
    rng = np.random.default_rng(random_seed)
    q = float(np.clip(service_level, 0.50, 0.999))
    prep_loss = float(np.clip(prep_loss_pct, 0.0, 0.25))
    clean_unit = normalize_unit(unit)

    # 1. Headcount uncertainty sampling (H = H_hat + conformal residuals)
    if residuals and len(residuals) >= 5:
        res_sample = rng.choice(residuals, size=num_simulations, replace=True)
        # Symmetrically signed perturbation from empirical errors
        signs = rng.choice([-1.0, 1.0], size=num_simulations)
        h_draws = h_hat + (res_sample * signs)
        h_method = "empirical_conformal_resampling"
    else:
        # Fallback normal spread from conformal cold-start heuristic
        spread = max(15.0, h_hat * 0.12)
        h_draws = rng.normal(loc=h_hat, scale=spread / 1.282, size=num_simulations)
        h_method = "conformal_heuristic_normal"

    # Headcount bounded by physical mess capacity [1, hostel_strength]
    h_draws = np.clip(h_draws, 1.0, float(max(h_hat, hostel_strength)))

    # 2. Per-head appetite distribution sampling (r)
    obs = dish_observations or []
    exact_rates = [o.rate for o in obs if not o.ran_out and o.rate > 0]
    all_rates = [o.rate for o in obs if o.rate > 0]

    is_fallback = False
    fallback_reason = None

    if len(exact_rates) >= 3:
        # Non-parametric empirical bootstrap with kernel smoothing
        base_draws = rng.choice(exact_rates, size=num_simulations, replace=True)
        std_val = float(np.std(exact_rates)) if len(exact_rates) > 1 else 0.005
        jitter_sd = max(0.002, std_val * 0.20)
        r_draws = base_draws + rng.normal(0, jitter_sd, size=num_simulations)
        r_draws = np.maximum(r_draws, 0.001)
        r_method = f"empirical_bootstrap (n={len(exact_rates)})"
    elif len(all_rates) >= 2:
        # Some observations censored (ran out): treat as lower bounds with right-tail expansion
        base_draws = rng.choice(all_rates, size=num_simulations, replace=True)
        r_draws = base_draws * rng.uniform(0.98, 1.15, size=num_simulations)
        r_method = f"shortage_censored_bootstrap (n={len(all_rates)})"
        is_fallback = True
        fallback_reason = f"Small sample with shortages ({len(all_rates)} obs); applied lower-bound tail expansion."
    else:
        # Cold start fallback: lognormal prior centered at learned_rate
        mu = max(0.005, learned_rate)
        cv = 0.15  # 15% appetite coefficient of variation
        sigma_log = np.sqrt(np.log(1.0 + cv ** 2))
        mu_log = np.log(mu) - 0.5 * (sigma_log ** 2)
        r_draws = rng.lognormal(mean=mu_log, sigma=sigma_log, size=num_simulations)
        r_method = "lognormal_prior_fallback"
        is_fallback = True
        fallback_reason = f"Insufficient dish history ({len(obs)} obs < 3 threshold). Used lognormal prior around learned rate."

    # 3. Joint Demand D = H * r
    demand_draws = h_draws * r_draws

    # 4. Cook quantity: Q = quantile(D, q_dish) * (1 + prep_loss)
    demand_at_q = float(np.percentile(demand_draws, q * 100.0))
    theo_q = demand_at_q * (1.0 + prep_loss)
    planned_q = apply_batch_rounding(theo_q, batch_size, clean_unit)

    # 5. Risk & Surplus: under practical batch quantity
    effective_served_cap = planned_q / (1.0 + prep_loss) if planned_q > 0 else 0.0
    p_runout = float(np.mean(demand_draws > effective_served_cap))
    expected_surplus = float(np.mean(np.maximum(effective_served_cap - demand_draws, 0.0)))
    exp_demand = float(np.mean(demand_draws))

    # Demand quantiles
    d_p10 = float(np.percentile(demand_draws, 10.0))
    d_p50 = float(np.percentile(demand_draws, 50.0))
    d_p90 = float(np.percentile(demand_draws, 90.0))
    d_p95 = float(np.percentile(demand_draws, 95.0))
    d_p99 = float(np.percentile(demand_draws, 99.0))

    explanation = (
        f"Monte-Carlo joint demand ({num_simulations} draws; {h_method} x {r_method}). "
        f"Median demand is {d_p50:.1f} {clean_unit}; {q:.0%} demand target is {demand_at_q:.1f} {clean_unit}. "
        f"Planned {planned_q:.1f} {clean_unit} (with {prep_loss:.1%} prep loss and batching) "
        f"yields ~{p_runout * 100.0:.1f}% run-out risk and {expected_surplus:.1f} {clean_unit} expected surplus."
    )

    return MonteCarloDemandResult(
        dish_id=dish_id,
        dish_name=dish_name,
        unit=clean_unit,
        service_level=q,
        num_simulations=num_simulations,
        theo_cook_quantity=round(theo_q, 2),
        planned_cook_quantity=planned_q,
        expected_demand=round(exp_demand, 2),
        demand_p10=round(d_p10, 2),
        demand_p50=round(d_p50, 2),
        demand_p90=round(d_p90, 2),
        demand_p95=round(d_p95, 2),
        demand_p99=round(d_p99, 2),
        p_runout=round(p_runout, 4),
        expected_surplus=round(expected_surplus, 2),
        is_fallback=is_fallback,
        fallback_reason=fallback_reason,
        method=f"{h_method}+{r_method}",
        explanation=explanation,
    )


def generate_meal_plan(
    session: Session,
    target_date: str,
    meal_type: str,
    service_level: float = 0.95,
    prep_loss_pct: float = 0.03,
    hostel_strength: int = DEFAULT_HOSTEL_STRENGTH,
    batch_sizes: Optional[Dict[Union[int, str], float]] = None,
    is_synthetic: int = 0,
    before_date: Optional[str] = None,
    before_meal_id: Optional[int] = None,
    custom_forecaster: Optional[HeadcountForecaster] = None,
    custom_df_history: Optional[pd.DataFrame] = None,
    cost_mode: bool = False,
    safety_floor: float = DEFAULT_SAFETY_FLOOR,
    dish_cost_configs: Optional[Dict[Union[int, str], Any]] = None,
    manager_overrides: Optional[Dict[Union[int, str], Any]] = None,
    **kwargs: Any,
) -> MealPlanResult:
    """Generate per-dish cooking quantity plan integrating B1-B5.

    Integrates:
    1. Step 2 Headcount Forecast & Uncertainty Engine.
    2. B4 Cost-Aware Optimiser (Newsvendor logic) & Policy Criticality defaults when cost_mode=True.
    3. B3 Service-level planning headcount derivation H_q.
    4. B5 Kaplan-Meier Shortage-Aware Consumption Learning r_d.
    5. B1 Cooking Quantity Formula: Quantity_d = H_q * r_d * (1 + prep_loss) with batch rounding.
    6. Practical batch sizing and expected surplus trade-offs.
    """
    norm_meal = normalize_meal_type(meal_type)
    clamped_manual_service_level = float(np.clip(service_level, 0.50, 0.999))
    clamped_prep_loss = float(np.clip(prep_loss_pct, 0.0, 0.25))
    safe_strength = hostel_strength if hostel_strength > 0 else DEFAULT_HOSTEL_STRENGTH
    safe_floor = float(np.clip(safety_floor if safety_floor is not None else DEFAULT_SAFETY_FLOOR, 0.50, 0.999))

    # 1. Obtain headcount forecast from Step 2 engine (strictly prior to cutoff if specified)
    if custom_forecaster is not None and custom_df_history is not None:
        forecaster = custom_forecaster
        df_history = custom_df_history
    else:
        forecaster, df_history = get_trained_forecaster(
            session=session,
            is_synthetic=is_synthetic,
            before_date=before_date,
            before_meal_id=before_meal_id,
        )
    forecast = forecaster.predict_slot(
        df_history=df_history,
        target_date_str=target_date,
        meal_type=norm_meal,
        hostel_strength=safe_strength,
        is_synthetic=is_synthetic,
    )

    # Fetch registered dish catalog
    dish_catalog = session.execute(select(Dish)).scalars().all()
    custom_configs = dish_cost_configs or {}
    overrides_dict = manager_overrides or {}

    # 2. Determine per-dish service levels (B4 Cost-Aware vs B3 Manual)
    dish_newsvendor_results: Dict[int, NewsvendorResult] = {}
    dish_service_levels: Dict[int, float] = {}

    for dish in dish_catalog:
        # Check for custom cost configuration
        cfg_entry = custom_configs.get(dish.id) or custom_configs.get(dish.name) or {}
        if isinstance(cfg_entry, DishCostConfig):
            cu_val = cfg_entry.shortage_cost_cu
            co_val = cfg_entry.waste_cost_co
            k_val = cfg_entry.cost_ratio_k
            dish_floor = cfg_entry.safety_floor
            ov_val = cfg_entry.manager_override
            ov_reason = cfg_entry.override_reason
        elif isinstance(cfg_entry, dict):
            cu_val = cfg_entry.get("shortage_cost_cu")
            co_val = cfg_entry.get("waste_cost_co")
            k_val = cfg_entry.get("cost_ratio_k")
            dish_floor = cfg_entry.get("safety_floor", safe_floor)
            ov_val = cfg_entry.get("manager_override")
            ov_reason = cfg_entry.get("override_reason")
        else:
            cu_val = dish.shortage_cost_cu
            co_val = dish.waste_cost_co
            k_val = dish.cost_ratio_k
            dish_floor = safe_floor
            ov_val = None
            ov_reason = None

        # Check explicit manager override passed in manager_overrides
        direct_ov = overrides_dict.get(dish.id) or overrides_dict.get(dish.name)
        if direct_ov is not None:
            if isinstance(direct_ov, dict):
                ov_val = direct_ov.get("service_level", direct_ov.get("override_q"))
                ov_reason = direct_ov.get("reason", "Manager explicit override")
            elif isinstance(direct_ov, (int, float)):
                ov_val = float(direct_ov)
                ov_reason = "Manager explicit override"

        if cost_mode:
            # B4 Cost-Aware Optimisation
            d_cat = (dish.category or "").strip().lower()
            d_crit = (dish.criticality_tier or "").strip().lower()
            if d_crit in DEFAULT_CRITICALITY_TIERS and d_crit != "main":
                target_crit = d_crit
            elif d_cat in DEFAULT_CRITICALITY_TIERS and d_cat != "main":
                target_crit = d_cat
            elif any(s in dish.name.lower() for s in ["rice", "roti", "chapati", "puri", "bread"]):
                target_crit = "staple"
            elif any(s in dish.name.lower() for s in ["salad", "chutney", "papad", "curd", "raita"]):
                target_crit = "side"
            else:
                target_crit = d_crit or d_cat or "main"

            nv_res = calculate_newsvendor_service_level(
                category=target_crit,
                cu=cu_val,
                co=co_val,
                k=k_val,
                safety_floor=dish_floor,
                manager_override=ov_val,
                override_reason=ov_reason,
            )
            dish_newsvendor_results[dish.id] = nv_res
            dish_service_levels[dish.id] = nv_res.effective_service_level
        else:
            # B3 Manual slider mode (with optional direct manager override)
            if ov_val is not None:
                eff_q = float(np.clip(ov_val, 0.50, 0.999))
            else:
                eff_q = clamped_manual_service_level
            dish_service_levels[dish.id] = eff_q

    # Primary headline service level
    headline_service_level = (
        float(np.mean(list(dish_service_levels.values())))
        if (cost_mode and dish_service_levels)
        else clamped_manual_service_level
    )

    # 3. Derive global planning headcount H_q for headline service level (B3)
    global_h_q, global_trade_off = calculate_service_headcount(
        forecaster=forecaster,
        forecast=forecast,
        service_level=headline_service_level,
    )

    # 4. Compute per-head consumption rates using Kaplan-Meier (B5, strictly prior to cutoff)
    rates_by_dish = compute_dish_consumption_rates(
        session=session,
        meal_type=norm_meal,
        is_synthetic=is_synthetic,
        before_date=before_date,
        before_meal_id=before_meal_id,
        service_level=headline_service_level,
        dish_service_levels=dish_service_levels,
    )

    # 5. Generate per-dish quantity recommendations (B1-B5)
    dish_items: List[DishPlanItem] = []
    total_planned_kg = 0.0
    total_expected_surplus_kg = 0.0
    custom_batches = batch_sizes or {}

    for dish_id, rate_rec in rates_by_dish.items():
        r_d = rate_rec.estimated_rate
        dish_q = dish_service_levels.get(dish_id, headline_service_level)
        nv_info = dish_newsvendor_results.get(dish_id)

        # Dish-specific planning headcount matching its effective service level
        if cost_mode:
            dish_hq, _ = calculate_service_headcount(
                forecaster=forecaster,
                forecast=forecast,
                service_level=dish_q,
            )
        else:
            dish_hq = global_h_q

        # B1 Formula: Quantity_d = H_q * r_d * (1 + prep_loss)
        base_served_req = dish_hq * r_d
        theo_qty = base_served_req * (1.0 + clamped_prep_loss)

        # Batch size configuration
        b_size = None
        if dish_id in custom_batches:
            b_size = float(custom_batches[dish_id])
        elif rate_rec.dish_name in custom_batches:
            b_size = float(custom_batches[rate_rec.dish_name])
        elif rate_rec.batch_size is not None and rate_rec.batch_size > 0:
            b_size = float(rate_rec.batch_size)
        else:
            b_size = DEFAULT_BATCH_SIZES.get(rate_rec.unit)

        planned_qty = apply_batch_rounding(theo_qty, b_size, rate_rec.unit)

        # Expected served turnout vs buffer
        expected_served = forecast.h_hat * r_d
        expected_surplus = max(
            0.0,
            round((planned_qty / (1.0 + clamped_prep_loss)) - expected_served, 2),
        )

        if rate_rec.unit == "kg":
            total_planned_kg += planned_qty
            total_expected_surplus_kg += expected_surplus

        # Run-out risk indicator
        if dish_q >= 0.95:
            risk_label = "Low"
        elif dish_q >= 0.90:
            risk_label = "Moderate"
        else:
            risk_label = "Elevated"

        # Plain-language explanation for this dish
        batch_note = f", rounded to {b_size:g} {rate_rec.unit} batch size" if (b_size and b_size > 0) else ""

        if cost_mode and nv_info:
            policy_desc = (
                f"B4 Cost-Aware ({nv_info.criticality_tier.title()} policy target {nv_info.effective_service_level:.0%})"
                if nv_info.is_policy_default
                else f"B4 Cost-Aware (Configured cost target {nv_info.effective_service_level:.1%}, k={nv_info.cost_ratio_k:g})"
            )
        else:
            policy_desc = f"B3 Manual target {dish_q:.0%}"

        dish_explanation = (
            f"Under {policy_desc}, MessWise plans for {dish_hq} students. "
            f"{rate_rec.dish_name} appetite is estimated at {r_d:.3f} {rate_rec.unit}/student "
            f"via {rate_rec.estimation_method.replace('_', ' ')} ({rate_rec.num_usable_observations} exact, {rate_rec.num_ran_out} ran out). "
            f"Base requirement is {base_served_req:.1f} {rate_rec.unit}, plus {clamped_prep_loss:.1%} prep-loss "
            f"gives {theo_qty:.1f} {rate_rec.unit}{batch_note}."
        )

        # B6 Joint Demand Monte Carlo simulation (PLAN.md Section 8.3 & Appendix C)
        residuals_list = forecaster.residuals_by_meal.get(norm_meal, []) or forecaster.all_residuals
        mc_res = simulate_joint_demand_monte_carlo(
            h_hat=forecast.h_hat,
            hostel_strength=safe_strength,
            residuals=residuals_list,
            dish_id=dish_id,
            dish_name=rate_rec.dish_name,
            unit=rate_rec.unit,
            service_level=dish_q,
            prep_loss_pct=clamped_prep_loss,
            learned_rate=r_d,
            dish_observations=rate_rec.observations,
            batch_size=b_size,
            num_simulations=5000,
            random_seed=42,
        )

        dish_items.append(
            DishPlanItem(
                dish_id=dish_id,
                dish_name=rate_rec.dish_name,
                category=rate_rec.category,
                unit=rate_rec.unit,
                per_head_rate=r_d,
                prep_loss_pct=clamped_prep_loss,
                batch_size=b_size,
                theo_quantity=round(theo_qty, 2),
                planned_quantity=planned_qty,
                expected_served_qty=round(expected_served, 2),
                expected_surplus_qty=expected_surplus,
                run_out_risk_label=risk_label,
                confidence_status=rate_rec.confidence_status,
                is_fallback_rate=rate_rec.is_fallback,
                explanation=dish_explanation,
                criticality_tier=rate_rec.criticality_tier,
                effective_service_level=round(dish_q, 4),
                planning_headcount=dish_hq,
                estimation_method=rate_rec.estimation_method,
                num_observations=rate_rec.num_observations,
                num_exact=rate_rec.num_exact,
                num_censored=rate_rec.num_ran_out,
                is_cost_aware=cost_mode,
                cost_ratio_k=nv_info.cost_ratio_k if nv_info else None,
                safety_floor=nv_info.safety_floor if nv_info else safe_floor,
                is_floor_applied=nv_info.is_floor_applied if nv_info else False,
                manager_override=nv_info.manager_override if nv_info else None,
                override_reason=nv_info.override_reason if nv_info else None,
                newsvendor_explanation=nv_info.explanation if nv_info else None,
                km_explanation=rate_rec.km_result.explanation if rate_rec.km_result else None,
                mc_demand=mc_res,
            )
        )

    # Count real vs synthetic observations used across all dishes
    all_obs_flat = [obs for r in rates_by_dish.values() for obs in r.observations]
    real_count = sum(1 for o in all_obs_flat if o.is_synthetic == 0)
    synth_count = sum(1 for o in all_obs_flat if o.is_synthetic == 1)

    if real_count > 0 and synth_count == 0:
        data_basis = f"Real pilot data ({real_count} observations from kitchen logs)"
    elif synth_count > 0 and real_count == 0:
        data_basis = f"Synthetic development data ({synth_count} observations — demonstration only)"
    elif real_count > 0 and synth_count > 0:
        data_basis = f"Mixed data ({real_count} real / {synth_count} synthetic)"
    else:
        if is_synthetic == 0:
            data_basis = "Real pilot environment (0 historical records available; using portion defaults)"
        else:
            data_basis = "Synthetic development environment (0 historical records; using portion defaults)"

    mode_title = "B4 Cost-Aware Newsvendor Policy" if cost_mode else "B3 Manual Service-Level"
    summary_exp = (
        f"Cooking plan for {target_date} {norm_meal.title()} under {mode_title}: "
        f"Forecast attendance is {forecast.h_hat} students; planning for {global_h_q} students "
        f"(buffer +{global_trade_off['headcount_buffer']}). Preparation loss allowance is {clamped_prep_loss:.1%}. "
        f"Estimated run-out risk is ~{global_trade_off['run_out_risk_pct']}%. "
        f"Appetite learned via Kaplan-Meier shortage-aware estimation (B5). "
        f"Data basis: {data_basis}."
    )

    return MealPlanResult(
        target_date=target_date,
        meal_type=norm_meal,
        service_level=round(headline_service_level, 4),
        forecast_h_hat=forecast.h_hat,
        planning_headcount=global_h_q,
        hostel_strength=safe_strength,
        prep_loss_pct=clamped_prep_loss,
        headcount_buffer=global_trade_off["headcount_buffer"],
        run_out_risk_pct=global_trade_off["run_out_risk_pct"],
        dishes=dish_items,
        total_planned_kg=round(total_planned_kg, 2),
        total_expected_surplus_kg=round(total_expected_surplus_kg, 2),
        data_basis_label=data_basis,
        real_obs_count=real_count,
        synthetic_obs_count=synth_count,
        summary_explanation=summary_exp,
        is_synthetic=is_synthetic,
        plan_mode="cost_aware" if cost_mode else "manual",
        safety_floor=round(safe_floor, 4),
        cost_mode=cost_mode,
    )
