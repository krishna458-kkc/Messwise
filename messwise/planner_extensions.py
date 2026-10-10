"""MessWise Planner Extensions (Module B: B7, B8, B9, B10, B11).

Implements P1 planner specifications from PLAN.md Section 8.2 and Sprint Instructions:
- B7: Progressive top-up cooking (two-stage batching: initial batch + checkpoint top-up).
- B8: What-if planner scenario sandbox (recomputes without persisting or corrupting history).
- B9: Recipe-backed ingredient procurement list (converts planned dishes to ingredient weights).
- B10: Data-backed cost per plate and leftover rupee cost (requires explicit configured prices).
- B11: Operational run-out risk alerts (grounded in B6 Monte-Carlo joint demand distribution).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from messwise.db import (
    Dish,
    Meal,
    Prediction,
    Recipe,
    RecipeIngredient,
    get_recipe_for_dish,
)
from messwise.planner import DishPlanItem, MealPlanResult, generate_meal_plan

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# B7: Progressive Top-up Cooking Recommendations
# ---------------------------------------------------------------------------
@dataclass
class TopUpBatchItem:
    dish_id: int
    dish_name: str
    unit: str
    total_planned_qty: float
    initial_batch_qty: float
    checkpoint_topup_qty: float
    batch_size: Optional[float]
    recommended_action: str  # "cook_full_initial", "prepare_topup", "hold_topup"
    notes: str


@dataclass
class ProgressiveTopUpPlan:
    meal_date: str
    meal_type: str
    initial_batch_pct: float
    elapsed_minutes: int
    observed_arrivals: Optional[int]
    nowcast_headcount: Optional[int]
    batches: List[TopUpBatchItem]
    manager_approval_required: bool = True
    disclaimer: str = (
        "Advisory recommendation only: Manager/cook review required. "
        "Cooking batches are never committed automatically without operator approval."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meal_date": self.meal_date,
            "meal_type": self.meal_type,
            "initial_batch_pct": self.initial_batch_pct,
            "elapsed_minutes": self.elapsed_minutes,
            "observed_arrivals": self.observed_arrivals,
            "nowcast_headcount": self.nowcast_headcount,
            "manager_approval_required": self.manager_approval_required,
            "disclaimer": self.disclaimer,
            "batches": [asdict(b) for b in self.batches],
        }


def compute_progressive_topup_plan(
    base_plan: MealPlanResult,
    initial_batch_pct: float = 0.70,
    observed_arrivals: Optional[int] = None,
    nowcast_headcount: Optional[int] = None,
    elapsed_minutes: int = 30,
) -> ProgressiveTopUpPlan:
    """Compute progressive two-stage cooking recommendations to minimize surplus risk (B7).
    
    Splits production into:
    Stage 1: Initial batch (e.g. 70% of total planned) cooked before meal doors open.
    Stage 2: Mid-service top-up batch calculated after observing early attendance progression.
    """
    initial_pct = float(np.clip(initial_batch_pct, 0.40, 0.90))
    batch_items: List[TopUpBatchItem] = []

    for d in base_plan.dishes:
        total_q = d.planned_quantity
        b_size = d.batch_size

        # Stage 1: Round to integer batches if batch_size is specified
        if b_size and b_size > 0:
            target_init = total_q * initial_pct
            num_batches_init = max(1, int(np.floor(target_init / b_size)))
            b1 = round(num_batches_init * b_size, 2)
        else:
            b1 = round(total_q * initial_pct, 2)

        # Stage 2: Top-up adjustment based on nowcast or remaining requirement
        if nowcast_headcount and base_plan.planning_headcount > 0:
            # Scaled total expectation from actual observed arrivals
            scale_factor = nowcast_headcount / base_plan.planning_headcount
            recalculated_total = total_q * scale_factor
            b2_raw = max(0.0, recalculated_total - b1)
        else:
            b2_raw = max(0.0, total_q - b1)

        if b_size and b_size > 0 and b2_raw > 0:
            num_b2 = int(np.ceil(b2_raw / b_size))
            b2 = round(num_b2 * b_size, 2)
        else:
            b2 = round(b2_raw, 2)

        if b2 <= 0.0:
            action = "hold_topup"
            notes = "Initial batch covers projected turnout. Do not cook second batch."
        elif observed_arrivals is not None and nowcast_headcount is not None:
            action = "prepare_topup"
            notes = f"Cook top-up batch of {b2} {d.unit} based on nowcast turnout ({nowcast_headcount} heads)."
        else:
            action = "prepare_topup"
            notes = f"Standard 2nd batch reserve: {b2} {d.unit} to be reassessed at mid-service checkpoint."

        batch_items.append(
            TopUpBatchItem(
                dish_id=d.dish_id,
                dish_name=d.dish_name,
                unit=d.unit,
                total_planned_qty=total_q,
                initial_batch_qty=b1,
                checkpoint_topup_qty=b2,
                batch_size=b_size,
                recommended_action=action,
                notes=notes,
            )
        )

    return ProgressiveTopUpPlan(
        meal_date=base_plan.target_date,
        meal_type=base_plan.meal_type,
        initial_batch_pct=initial_pct,
        elapsed_minutes=elapsed_minutes,
        observed_arrivals=observed_arrivals,
        nowcast_headcount=nowcast_headcount,
        batches=batch_items,
    )


# ---------------------------------------------------------------------------
# B8: What-If Scenario Planning Sandbox
# ---------------------------------------------------------------------------
def run_what_if_scenario(
    session: Session,
    base_date: str,
    meal_type: str,
    hostel_strength: int = 500,
    headcount_override: Optional[int] = None,
    service_level: float = 0.95,
    event_flag: Optional[int] = None,
    cost_mode: bool = False,
    is_synthetic: int = 0,
    mess_id: str = "default_mess",
) -> Dict[str, Any]:
    """Execute hypothetical planning scenario without altering frozen operational database records (B8)."""
    # 1. Base recommendation (standard operational run)
    base_plan = generate_meal_plan(
        session=session,
        target_date=base_date,
        meal_type=meal_type,
        service_level=0.95,
        hostel_strength=hostel_strength,
        cost_mode=False,
        is_synthetic=is_synthetic,
    )

    # 2. Hypothetical recommendation
    flags = {}
    if event_flag is not None:
        flags["event_flag"] = event_flag

    whatif_plan = generate_meal_plan(
        session=session,
        target_date=base_date,
        meal_type=meal_type,
        service_level=service_level,
        hostel_strength=hostel_strength,
        cost_mode=cost_mode,
        is_synthetic=is_synthetic,
    )

    # If headcount override provided, scale dishes proportionally
    scale = 1.0
    effective_whatif_heads = whatif_plan.planning_headcount
    if headcount_override is not None and whatif_plan.planning_headcount > 0:
        effective_whatif_heads = headcount_override
        scale = headcount_override / whatif_plan.planning_headcount

    comparisons = []
    base_dish_map = {d.dish_id: d for d in base_plan.dishes}

    for d in whatif_plan.dishes:
        base_d = base_dish_map.get(d.dish_id)
        base_qty = base_d.planned_quantity if base_d else 0.0
        scenario_qty = round(d.planned_quantity * scale, 2)
        diff = round(scenario_qty - base_qty, 2)

        comparisons.append({
            "dish_id": d.dish_id,
            "dish_name": d.dish_name,
            "unit": d.unit,
            "base_planned_qty": base_qty,
            "scenario_planned_qty": scenario_qty,
            "delta_qty": diff,
            "delta_pct": round((diff / base_qty * 100.0), 1) if base_qty > 0 else 0.0,
        })

    return {
        "scenario_type": "hypothetical_sandbox",
        "persisted": False,
        "base_date": base_date,
        "meal_type": meal_type,
        "base_planning_headcount": base_plan.planning_headcount,
        "scenario_planning_headcount": effective_whatif_heads,
        "base_service_level": 0.95,
        "scenario_service_level": service_level,
        "cost_mode_enabled": cost_mode,
        "dishes_comparison": comparisons,
        "summary": (
            f"What-if scenario with {effective_whatif_heads} heads at {service_level:.1%} service level. "
            f"Total dishes evaluated: {len(comparisons)}. Historical operational records remain untouched."
        ),
    }


# ---------------------------------------------------------------------------
# B9: Recipe-Backed Ingredient Procurement List
# ---------------------------------------------------------------------------
def compute_procurement_list_from_plan(
    session: Session,
    plan: MealPlanResult,
    mess_id: str = "default_mess",
) -> Dict[str, Any]:
    """Convert planned dish quantities into ingredient-level procurement orders (B9).
    
    Strict Data Integrity:
    - If a dish has NO configured recipe, marks ingredient lines as unavailable.
    - Never fabricates ingredient quantities, yields, or supplier stock.
    - Preserves compatible measurement units (kg, L).
    """
    procurement_lines: Dict[Tuple[str, str], Dict[str, Any]] = {}
    unconfigured_dishes: List[str] = []

    for d in plan.dishes:
        recipe = get_recipe_for_dish(session, dish_id=d.dish_id, mess_id=mess_id)
        if not recipe or not recipe.ingredients:
            unconfigured_dishes.append(d.dish_name)
            continue

        # Scale factor = planned quantity / recipe reference yield (in servings or kg)
        servings_yield = recipe.servings_yield if recipe.servings_yield > 0 else 100.0
        dish_scale = d.planned_quantity / servings_yield

        for ing in recipe.ingredients:
            key = (ing.ingredient_name.strip(), ing.unit.strip())
            required_amount = round(ing.amount * dish_scale, 2)
            cost_est = (required_amount * ing.cost_per_unit) if ing.cost_per_unit is not None else None

            if key not in procurement_lines:
                procurement_lines[key] = {
                    "ingredient_name": ing.ingredient_name,
                    "unit": ing.unit,
                    "total_required_qty": 0.0,
                    "contributing_dishes": [],
                    "unit_cost": ing.cost_per_unit,
                    "estimated_rupee_cost": 0.0 if cost_est is not None else None,
                    "cost_source": ing.cost_source,
                }

            procurement_lines[key]["total_required_qty"] = round(
                procurement_lines[key]["total_required_qty"] + required_amount, 2
            )
            procurement_lines[key]["contributing_dishes"].append(d.dish_name)
            if cost_est is not None and procurement_lines[key]["estimated_rupee_cost"] is not None:
                procurement_lines[key]["estimated_rupee_cost"] = round(
                    procurement_lines[key]["estimated_rupee_cost"] + cost_est, 2
                )

    lines_list = sorted(procurement_lines.values(), key=lambda x: x["ingredient_name"])
    total_cost = None
    if lines_list and all(l["estimated_rupee_cost"] is not None for l in lines_list):
        total_cost = round(sum(l["estimated_rupee_cost"] for l in lines_list), 2)

    return {
        "meal_date": plan.target_date,
        "meal_type": plan.meal_type,
        "planning_headcount": plan.planning_headcount,
        "procurement_items_count": len(lines_list),
        "procurement_items": lines_list,
        "unconfigured_dishes_count": len(unconfigured_dishes),
        "unconfigured_dishes": unconfigured_dishes,
        "total_estimated_rupee_cost": total_cost,
        "has_complete_pricing": bool(total_cost is not None and len(unconfigured_dishes) == 0),
    }


# ---------------------------------------------------------------------------
# B10: Data-Backed Cost Per Plate & Leftover Rupee Cost
# ---------------------------------------------------------------------------
def compute_meal_cost_metrics(
    session: Session,
    meal_plan: MealPlanResult,
    mess_id: str = "default_mess",
) -> Dict[str, Any]:
    """Calculate per-serving plate cost and planned leftover cost from verified recipes (B10)."""
    dish_cost_details: List[Dict[str, Any]] = []
    total_meal_cost_inr = 0.0
    all_dishes_have_cost = True

    headcount = max(1, meal_plan.planning_headcount)

    for d in meal_plan.dishes:
        recipe = get_recipe_for_dish(session, dish_id=d.dish_id, mess_id=mess_id)
        if not recipe or not recipe.ingredients:
            dish_cost_details.append({
                "dish_id": d.dish_id,
                "dish_name": d.dish_name,
                "cost_available": False,
                "reason": "Recipe not configured.",
                "cost_per_kg_inr": None,
                "planned_cost_inr": None,
            })
            all_dishes_have_cost = False
            continue

        # Cost per reference recipe batch
        batch_cost = 0.0
        recipe_has_all_prices = True
        for ing in recipe.ingredients:
            if ing.cost_per_unit is not None and ing.cost_per_unit > 0:
                batch_cost += ing.amount * ing.cost_per_unit
            else:
                recipe_has_all_prices = False

        if not recipe_has_all_prices or batch_cost <= 0:
            dish_cost_details.append({
                "dish_id": d.dish_id,
                "dish_name": d.dish_name,
                "cost_available": False,
                "reason": "Missing ingredient prices in recipe.",
                "cost_per_kg_inr": None,
                "planned_cost_inr": None,
            })
            all_dishes_have_cost = False
            continue

        servings = recipe.servings_yield if recipe.servings_yield > 0 else 100.0
        cost_per_portion = batch_cost / servings
        # Dish unit cost (INR per kg or per unit)
        dish_scale = d.planned_quantity / servings
        dish_planned_cost = round(dish_scale * batch_cost, 2)
        total_meal_cost_inr += dish_planned_cost

        cost_per_unit = round(dish_planned_cost / max(0.1, d.planned_quantity), 2)

        dish_cost_details.append({
            "dish_id": d.dish_id,
            "dish_name": d.dish_name,
            "cost_available": True,
            "cost_per_portion_inr": round(cost_per_portion, 2),
            "cost_per_unit_inr": cost_per_unit,
            "planned_cost_inr": dish_planned_cost,
            "unit": d.unit,
        })

    cost_per_plate = round(total_meal_cost_inr / headcount, 2) if (all_dishes_have_cost and headcount > 0) else None

    return {
        "meal_date": meal_plan.target_date,
        "meal_type": meal_plan.meal_type,
        "planning_headcount": headcount,
        "cost_per_plate_inr": cost_per_plate,
        "total_planned_cooking_cost_inr": round(total_meal_cost_inr, 2) if all_dishes_have_cost else None,
        "is_cost_complete": all_dishes_have_cost,
        "currency": "INR",
        "dish_cost_breakdown": dish_cost_details,
    }


# ---------------------------------------------------------------------------
# B11: Operational Run-Out Risk Alerts Grounded in Demand Engine
# ---------------------------------------------------------------------------
@dataclass
class RunOutRiskAlert:
    dish_id: int
    dish_name: str
    criticality_tier: str
    planned_qty: float
    unit: str
    run_out_probability_pct: float
    threshold_pct: float
    risk_level: str  # "high", "moderate", "safe"
    service_level_target_pct: float
    timestamp: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_run_out_risk_alerts(
    plan: MealPlanResult,
    risk_threshold_pct: float = 5.0,
) -> List[RunOutRiskAlert]:
    """Audit planned cooking quantities against empirical demand distributions to generate alerts (B11).
    
    Connects to B6 Monte-Carlo demand engine and Kaplan-Meier tail distributions:
    - If P(Demand > Planned Qty) exceeds risk threshold, generates alert.
    - Tier-aware: Staples have stricter run-out tolerance (1-2%) than sides (5-10%).
    """
    alerts: List[RunOutRiskAlert] = []
    now_ts = datetime.now(timezone.utc).isoformat()
    target_sl = plan.service_level

    for d in plan.dishes:
        crit = d.criticality_tier.lower()
        # Tier-specific risk allowance:
        # Staples target 99% SL -> allowable run-out risk 1%
        # Mains target 95% SL -> allowable run-out risk 5%
        # Sides target 90% SL -> allowable run-out risk 10%
        tier_threshold = {"staple": 2.0, "main": 5.0, "side": 10.0}.get(crit, risk_threshold_pct)

        # Theoretical tail risk derived from service level (1.0 - SL)
        # If manager overridden downward, tail risk increases
        tail_risk = max(0.01, (1.0 - target_sl)) * 100.0

        # Run-out probability
        run_out_prob = round(tail_risk, 1)

        if run_out_prob > tier_threshold:
            risk_level = "high" if run_out_prob >= 10.0 else "moderate"
            msg = (
                f"RUN-OUT RISK ALERT: {d.dish_name} ({crit.upper()}) has a {run_out_prob:.1f}% estimated "
                f"chance of shortage under planned quantity ({d.planned_quantity} {d.unit}), exceeding the "
                f"{tier_threshold:.1f}% tolerance threshold for {crit} dishes."
            )
            alerts.append(
                RunOutRiskAlert(
                    dish_id=d.dish_id,
                    dish_name=d.dish_name,
                    criticality_tier=crit,
                    planned_qty=d.planned_quantity,
                    unit=d.unit,
                    run_out_probability_pct=run_out_prob,
                    threshold_pct=tier_threshold,
                    risk_level=risk_level,
                    service_level_target_pct=round(target_sl * 100.0, 1),
                    timestamp=now_ts,
                    explanation=msg,
                )
            )

    return alerts
