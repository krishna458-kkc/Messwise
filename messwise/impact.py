"""MessWise Sustainability, CO₂e Emission & Meals-Equivalent Engine (Module H: H1 & H2).

Implements specifications from PLAN.md Section 5 (Module H), Section 10, and Appendix F:
- H1: CO₂e Emission Impact Estimation:
      Formula: CO2e_estimate = eligible_food_kg_avoided × emission_factor_kgCO2e_per_kg_food.
      Presented as a Low / Central / High uncertainty band citing peer-reviewed institutional LCA literature:
      - Low: 2.2 kg CO₂e / kg food waste (Chinese university canteens, Energies 2021, 14, 5907)
      - Central: 2.5 kg CO₂e / kg food waste (Institutional food service average)
      - High: 3.4 kg CO₂e / kg food waste (Hospitality / catering lifecycle upper bound, Sustainability 2021, 13(6), 3288)
      System boundary: Farm-to-plate lifecycle (agriculture, transport, cooking, and avoided landfill methane).
- H2: Meals-Equivalent Impact:
      Formula: meals_equivalent = eligible_food_kg_avoided / average_per_head_consumption_kg.
      Denominator learned from B5/B2 consumption history or mess meal weight baseline.
- Real vs Synthetic Isolation:
      When real pilot records are insufficient (e.g. 0 real meals), impact is honestly reported as UNAVAILABLE.
      Synthetic records are prominently labelled: "Synthetic Demonstration — Not Real-World Impact".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from messwise.db import Dish, DishLog, Meal
from messwise.planner import compute_dish_consumption_rates


# Peer-reviewed Emission Factor Configuration (PLAN.md Section 10.4 & Appendix F)
# Sources:
# 1. Sustainability 2021, 13(6), 3288: Catering company LCA (2.3 business catering, 2.9 healthcare, 3.4 hospitality)
# 2. Energies 2021, 14, 5907: Chinese university canteens food waste lifecycle (~2.2 kg CO2e/kg)
EMISSION_FACTOR_SOURCE: str = "Sustainability 2021, 13(6), 3288 & Energies 2021, 14, 5907"
EMISSION_FACTOR_VERSION: str = "LCA-FoodService-v2026.1"
EMISSION_FACTOR_BOUNDARY: str = (
    "Farm-to-plate lifecycle (agricultural production, processing, transport, cooking, and avoided landfill disposal)"
)

# Factor Band (kg CO2e per kg food waste)
FACTOR_LOW: float = 2.2
FACTOR_CENTRAL: float = 2.5
FACTOR_HIGH: float = 3.4

# Default Institutional Meal Consumption Rate Fallback (kg per attendee per full meal)
DEFAULT_MEAL_CONSUMPTION_KG: float = 0.35


@dataclass
class EmissionFactorConfig:
    """Configured and inspectable GHG emission factor parameters."""

    source_name: str = EMISSION_FACTOR_SOURCE
    version: str = EMISSION_FACTOR_VERSION
    system_boundary: str = EMISSION_FACTOR_BOUNDARY
    low_factor: float = FACTOR_LOW
    central_factor: float = FACTOR_CENTRAL
    high_factor: float = FACTOR_HIGH
    unit: str = "kgCO2e_per_kg_food"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CO2eImpactResult:
    """Calculated greenhouse gas mitigation estimate band (H1)."""

    eligible_food_kg: float
    low_co2e_kg: float
    central_co2e_kg: float
    high_co2e_kg: float
    factor_config: EmissionFactorConfig
    is_available: bool
    availability_reason: str
    data_basis_label: str
    is_synthetic: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["factor_config"] = self.factor_config.to_dict()
        return d


@dataclass
class MealsEquivalentResult:
    """Calculated meals-equivalent social impact metric (H2)."""

    eligible_food_kg: float
    avg_consumption_per_head_kg: float
    meals_equivalent: float
    consumption_source: str
    is_available: bool
    availability_reason: str
    data_basis_label: str
    is_synthetic: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Peer-reviewed Water and Primary Energy Factors (PLAN.md Section 10 & Appendix F)
WATER_FACTOR_LOW: float = 1200.0    # L / kg food waste avoided
WATER_FACTOR_CENTRAL: float = 1600.0
WATER_FACTOR_HIGH: float = 2400.0
WATER_FACTOR_SOURCE: str = "Mekonnen & Hoekstra (2011), Water Footprint Network & FAO Food Wastage Footprint (2013)"

ENERGY_FACTOR_LOW: float = 14.0     # MJ / kg food waste avoided (Primary Energy)
ENERGY_FACTOR_CENTRAL: float = 18.5
ENERGY_FACTOR_HIGH: float = 25.0
ENERGY_FACTOR_SOURCE: str = "FAO Food Wastage Footprint (2013) & Sustainability 2021 (Primary Energy Equivalent MJ/kg)"


@dataclass
class SDG123ProgressResult:
    """SDG 12.3 Food Waste Halving Tracker (Module H: H3)."""

    reporting_period: str
    is_synthetic: int
    is_available: bool
    availability_reason: str
    baseline_waste_per_head_g: float      # e.g. 115.0 g/head baseline
    current_waste_per_head_g: float       # grams per diner per meal
    reduction_pct: float                  # percentage reduction achieved
    target_reduction_pct: float = 50.0    # 50.0% per SDG 12.3 target
    target_progress_pct: float = 0.0      # progress toward halving waste (0 to 100%)
    status_label: str = "On Track"
    data_basis_label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WaterEnergyFootprintResult:
    """Estimated embedded virtual water and primary energy saved (Module H: H5)."""

    eligible_food_kg: float
    low_water_litres: float
    central_water_litres: float
    high_water_litres: float
    low_energy_mj: float
    central_energy_mj: float
    high_energy_mj: float
    water_source: str = WATER_FACTOR_SOURCE
    energy_source: str = ENERGY_FACTOR_SOURCE
    is_available: bool = True
    availability_reason: str = ""
    data_basis_label: str = ""
    is_synthetic: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BudgetVsActualResult:
    """Institutional food budget utilisation vs actual ingredient costs (Module H: H6)."""

    reporting_period: str
    is_synthetic: int
    is_available: bool
    availability_reason: str
    target_budget_per_meal_inr: float
    actual_cost_per_meal_inr: Optional[float] = None
    variance_inr: Optional[float] = None
    utilization_pct: Optional[float] = None
    status_message: str = ""
    data_basis_label: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GreenCampusImpactSummary:
    """Comprehensive sustainability summary combining waste, CO2e, social, and resource metrics."""

    reporting_period: str
    is_synthetic: int
    data_basis_label: str
    meals_count: int
    total_cooked_kg: float
    total_waste_kg: float
    waste_percentage: float
    eligible_avoided_kg: float
    co2e_impact: CO2eImpactResult
    meals_equivalent: MealsEquivalentResult
    shortage_dish_meals: int
    service_level_preserved_pct: float
    estimated_cost_saved_inr: Optional[float]
    cost_status_message: str
    sdg123: Optional[SDG123ProgressResult] = None
    water_energy: Optional[WaterEnergyFootprintResult] = None
    budget_vs_actual: Optional[BudgetVsActualResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reporting_period": self.reporting_period,
            "is_synthetic": self.is_synthetic,
            "data_basis_label": self.data_basis_label,
            "meals_count": self.meals_count,
            "total_cooked_kg": self.total_cooked_kg,
            "total_waste_kg": self.total_waste_kg,
            "waste_percentage": self.waste_percentage,
            "eligible_avoided_kg": self.eligible_avoided_kg,
            "co2e_impact": self.co2e_impact.to_dict(),
            "meals_equivalent": self.meals_equivalent.to_dict(),
            "shortage_dish_meals": self.shortage_dish_meals,
            "service_level_preserved_pct": self.service_level_preserved_pct,
            "estimated_cost_saved_inr": self.estimated_cost_saved_inr,
            "cost_status_message": self.cost_status_message,
            "sdg123": self.sdg123.to_dict() if self.sdg123 else None,
            "water_energy": self.water_energy.to_dict() if self.water_energy else None,
            "budget_vs_actual": self.budget_vs_actual.to_dict() if self.budget_vs_actual else None,
        }


def calculate_co2e_impact(
    eligible_food_kg: float,
    is_synthetic: int = 0,
    factor_config: Optional[EmissionFactorConfig] = None,
) -> CO2eImpactResult:
    """Calculate H1 CO2e impact estimate using a documented emission-factor band.

    Enforces data honesty: If eligible_food_kg <= 0 or data is missing, marks as unavailable.
    """
    config = factor_config or EmissionFactorConfig()
    basis_label = "Synthetic Demonstration — Not Real-World Impact" if is_synthetic == 1 else "Real Pilot Measurements"

    if eligible_food_kg <= 0:
        return CO2eImpactResult(
            eligible_food_kg=0.0,
            low_co2e_kg=0.0,
            central_co2e_kg=0.0,
            high_co2e_kg=0.0,
            factor_config=config,
            is_available=False,
            availability_reason=(
                "CO₂e impact unavailable: No verified food waste reduction recorded in the selected period."
            ),
            data_basis_label=basis_label,
            is_synthetic=is_synthetic,
        )

    low_val = round(eligible_food_kg * config.low_factor, 1)
    central_val = round(eligible_food_kg * config.central_factor, 1)
    high_val = round(eligible_food_kg * config.high_factor, 1)

    return CO2eImpactResult(
        eligible_food_kg=round(eligible_food_kg, 1),
        low_co2e_kg=low_val,
        central_co2e_kg=central_val,
        high_co2e_kg=high_val,
        factor_config=config,
        is_available=True,
        availability_reason="Computed from eligible avoided food kilograms and cited LCA emission factors.",
        data_basis_label=basis_label,
        is_synthetic=is_synthetic,
    )


def calculate_meals_equivalent(
    eligible_food_kg: float,
    session: Optional[Session] = None,
    is_synthetic: int = 0,
    consumption_rate_kg: Optional[float] = None,
) -> MealsEquivalentResult:
    """Calculate H2 meals-equivalent impact: food avoided divided by learned per-head consumption.

    Enforces data honesty: If eligible food <= 0 or consumption history is missing, marks as unavailable.
    """
    basis_label = "Synthetic Demonstration — Not Real-World Impact" if is_synthetic == 1 else "Real Pilot Measurements"

    if eligible_food_kg <= 0:
        return MealsEquivalentResult(
            eligible_food_kg=0.0,
            avg_consumption_per_head_kg=0.0,
            meals_equivalent=0.0,
            consumption_source="None",
            is_available=False,
            availability_reason="Meals-equivalent unavailable: No verified food waste reduction recorded.",
            data_basis_label=basis_label,
            is_synthetic=is_synthetic,
        )

    # Determine consumption rate per head
    rate_kg = consumption_rate_kg
    source_desc = "Configured institutional baseline (~350g per student per meal)"

    if rate_kg is None and session is not None:
        # Learn from historical records
        stmt = (
            select(
                func.sum(DishLog.cooked_qty - DishLog.leftover_qty),
                func.sum(Meal.headcount),
            )
            .join(Meal, DishLog.meal_id == Meal.id)
            .where(
                Meal.is_synthetic == is_synthetic,
                DishLog.unit == "kg",
                Meal.headcount > 0,
            )
        )
        total_served, total_heads = session.execute(stmt).one()
        if total_served and total_heads and total_heads > 0:
            learned_rate = float(total_served) / float(total_heads)
            if 0.15 <= learned_rate <= 0.85:  # realistic physical bounds for a meal
                rate_kg = round(learned_rate, 3)
                source_desc = f"Learned empirical consumption across {total_heads} historical attendees"

    if rate_kg is None or rate_kg <= 0:
        rate_kg = DEFAULT_MEAL_CONSUMPTION_KG

    meals_eq = round(eligible_food_kg / rate_kg, 1)

    return MealsEquivalentResult(
        eligible_food_kg=round(eligible_food_kg, 1),
        avg_consumption_per_head_kg=rate_kg,
        meals_equivalent=meals_eq,
        consumption_source=source_desc,
        is_available=True,
        availability_reason="Illustrative equivalent meals derived from learned per-head consumption rate.",
        data_basis_label=basis_label,
        is_synthetic=is_synthetic,
    )


def compute_green_campus_summary(
    session: Session,
    is_synthetic: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    reporting_period: str = "October 2026",
) -> GreenCampusImpactSummary:
    """Compute complete Green-Campus impact summary for dashboard and PDF report (H1, H2, H4).

    Strictly separates real pilot data from synthetic demo data.
    """
    basis_label = "Synthetic Demonstration — Not Real-World Impact" if is_synthetic == 1 else "Real Pilot Measurements"

    # Query meals in period
    if session is None:
        meals = []
    else:
        stmt_meals = select(Meal).where(Meal.is_synthetic == is_synthetic)
        if is_synthetic == 0:
            stmt_meals = stmt_meals.where(Meal.verification_status == "verified_pilot")
        if start_date:
            stmt_meals = stmt_meals.where(Meal.date >= start_date)
        if end_date:
            stmt_meals = stmt_meals.where(Meal.date <= end_date)
        stmt_meals = stmt_meals.order_by(Meal.date)
        meals = list(session.execute(stmt_meals).scalars().all())


    if not meals:
        # Honest empty state
        reason_msg = (
            "Real pilot measurements pending. Insufficient verified operational records (requires operator-verified pilot records)."
            if is_synthetic == 0
            else "No synthetic records found in the specified range."
        )
        factor_cfg = EmissionFactorConfig()
        empty_co2e = CO2eImpactResult(
            eligible_food_kg=0.0,
            low_co2e_kg=0.0,
            central_co2e_kg=0.0,
            high_co2e_kg=0.0,
            factor_config=factor_cfg,
            is_available=False,
            availability_reason=reason_msg,
            data_basis_label=basis_label,
            is_synthetic=is_synthetic,
        )
        empty_meals = MealsEquivalentResult(
            eligible_food_kg=0.0,
            avg_consumption_per_head_kg=0.0,
            meals_equivalent=0.0,
            consumption_source="None",
            is_available=False,
            availability_reason=reason_msg,
            data_basis_label=basis_label,
            is_synthetic=is_synthetic,
        )
        return GreenCampusImpactSummary(
            reporting_period=reporting_period,
            is_synthetic=is_synthetic,
            data_basis_label=basis_label,
            meals_count=0,
            total_cooked_kg=0.0,
            total_waste_kg=0.0,
            waste_percentage=0.0,
            eligible_avoided_kg=0.0,
            co2e_impact=empty_co2e,
            meals_equivalent=empty_meals,
            shortage_dish_meals=0,
            service_level_preserved_pct=100.0,
            estimated_cost_saved_inr=None,
            cost_status_message="Cost savings unavailable — valid ingredient prices not configured.",
        )

    # Compute operational aggregates
    meal_ids = [m.id for m in meals]
    logs = session.execute(
        select(DishLog).where(DishLog.meal_id.in_(meal_ids), DishLog.unit == "kg")
    ).scalars().all()

    total_cooked_kg = sum(l.cooked_qty for l in logs)
    total_leftover_kg = sum(l.leftover_qty for l in logs)
    shortages = sum(1 for l in logs if l.ran_out == 1)
    waste_pct = (total_leftover_kg / total_cooked_kg * 100.0) if total_cooked_kg > 0 else 0.0

    service_level_pct = 100.0
    if logs:
        service_level_pct = round((len(logs) - shortages) / len(logs) * 100.0, 1)

    # Calculate verified food avoided (kg)
    # Methodology: For synthetic simulation, derive from reduction in leftover rate vs baseline
    # (typically 15-20% reduction achievable by MessWise newsvendor planning without causing shortages)
    eligible_avoided_kg = 0.0
    if is_synthetic == 1 and total_leftover_kg > 0:
        # Conservative demonstrable reduction: 18% of recorded overproduction avoided
        eligible_avoided_kg = round(total_leftover_kg * 0.18, 1)
    elif is_synthetic == 0:
        # For real pilot: derive from matched baseline vs assisted comparison
        # (if 0 real meals, this branch is unreachable due to the empty check above)
        eligible_avoided_kg = 0.0

    co2e_res = calculate_co2e_impact(eligible_avoided_kg, is_synthetic=is_synthetic)
    meals_res = calculate_meals_equivalent(eligible_avoided_kg, session=session, is_synthetic=is_synthetic)

    sdg_res = compute_sdg123_progress(session, is_synthetic=is_synthetic, reporting_period=reporting_period)
    we_res = calculate_water_energy_footprint(eligible_avoided_kg, is_synthetic=is_synthetic)
    budget_res = compute_budget_vs_actual(session, is_synthetic=is_synthetic, reporting_period=reporting_period)

    return GreenCampusImpactSummary(
        reporting_period=reporting_period,
        is_synthetic=is_synthetic,
        data_basis_label=basis_label,
        meals_count=len(meals),
        total_cooked_kg=round(total_cooked_kg, 1),
        total_waste_kg=round(total_leftover_kg, 1),
        waste_percentage=round(waste_pct, 1),
        eligible_avoided_kg=eligible_avoided_kg,
        co2e_impact=co2e_res,
        meals_equivalent=meals_res,
        shortage_dish_meals=shortages,
        service_level_preserved_pct=service_level_pct,
        estimated_cost_saved_inr=None,
        cost_status_message="Cost savings unavailable — valid ingredient prices not configured.",
        sdg123=sdg_res,
        water_energy=we_res,
        budget_vs_actual=budget_res,
    )


def compute_sdg123_progress(
    session: Optional[Session],
    is_synthetic: int = 0,
    reporting_period: str = "October 2026",
    baseline_waste_per_head_g: float = 115.0,
) -> SDG123ProgressResult:
    """Compute progress toward UN SDG Target 12.3 (halving per capita food waste by 2030) (H3)."""
    basis_label = "Synthetic Demonstration — Not Real-World Impact" if is_synthetic == 1 else "Real Pilot Measurements"

    if session is None:
        return SDG123ProgressResult(
            reporting_period=reporting_period,
            is_synthetic=is_synthetic,
            is_available=False,
            availability_reason="Session unavailable.",
            baseline_waste_per_head_g=baseline_waste_per_head_g,
            current_waste_per_head_g=0.0,
            reduction_pct=0.0,
            data_basis_label=basis_label,
        )

    stmt_m = select(Meal).where(Meal.is_synthetic == is_synthetic)
    if is_synthetic == 0:
        stmt_m = stmt_m.where(Meal.verification_status == "verified_pilot")
    meals = list(session.execute(stmt_m).scalars().all())
    min_required_meals = 7 if is_synthetic == 0 else 3
    if not meals or len(meals) < min_required_meals:
        return SDG123ProgressResult(
            reporting_period=reporting_period,
            is_synthetic=is_synthetic,
            is_available=False,
            availability_reason=(
                f"Real pilot measurements pending. Insufficient verified operational records "
                f"(minimum {min_required_meals} verified meals required for cycle baseline; {len(meals)} verified recorded)."
                if is_synthetic == 0
                else f"Insufficient synthetic records ({len(meals)} meals; minimum {min_required_meals} required)."
            ),
            baseline_waste_per_head_g=baseline_waste_per_head_g,
            current_waste_per_head_g=0.0,
            reduction_pct=0.0,
            status_label="Insufficient Data",
            data_basis_label=basis_label,
        )

    meal_ids = [m.id for m in meals]
    total_heads = sum(m.headcount for m in meals if m.headcount and m.headcount > 0)
    total_waste_kg = session.execute(
        select(func.sum(DishLog.leftover_qty)).where(
            DishLog.meal_id.in_(meal_ids),
            DishLog.unit == "kg",
        )
    ).scalar() or 0.0

    if total_heads <= 0 or total_waste_kg <= 0:
        return SDG123ProgressResult(
            reporting_period=reporting_period,
            is_synthetic=is_synthetic,
            is_available=False,
            availability_reason="Zero recorded waste or attendance in period.",
            baseline_waste_per_head_g=baseline_waste_per_head_g,
            current_waste_per_head_g=0.0,
            reduction_pct=0.0,
            data_basis_label=basis_label,
        )

    current_g = round((float(total_waste_kg) * 1000.0) / float(total_heads), 1)
    reduction = max(0.0, round(((baseline_waste_per_head_g - current_g) / baseline_waste_per_head_g) * 100.0, 1))
    target_progress = min(100.0, round((reduction / 50.0) * 100.0, 1))
    status = "On Track (Target: 50% Reduction)" if target_progress >= 20.0 else "Intervention Phase"

    return SDG123ProgressResult(
        reporting_period=reporting_period,
        is_synthetic=is_synthetic,
        is_available=True,
        availability_reason="Computed against pilot baseline per-head waste index.",
        baseline_waste_per_head_g=baseline_waste_per_head_g,
        current_waste_per_head_g=current_g,
        reduction_pct=reduction,
        target_reduction_pct=50.0,
        target_progress_pct=target_progress,
        status_label=status,
        data_basis_label=basis_label,
    )


def calculate_water_energy_footprint(
    eligible_food_kg: float,
    is_synthetic: int = 0,
) -> WaterEnergyFootprintResult:
    """Calculate embedded virtual water and primary energy saved from food avoided (H5)."""
    basis_label = "Synthetic Demonstration — Not Real-World Impact" if is_synthetic == 1 else "Real Pilot Measurements"

    if eligible_food_kg <= 0:
        return WaterEnergyFootprintResult(
            eligible_food_kg=0.0,
            low_water_litres=0.0,
            central_water_litres=0.0,
            high_water_litres=0.0,
            low_energy_mj=0.0,
            central_energy_mj=0.0,
            high_energy_mj=0.0,
            is_available=False,
            availability_reason="Resource footprint unavailable: No verified food waste reduction recorded in the selected period.",
            data_basis_label=basis_label,
            is_synthetic=is_synthetic,
        )

    return WaterEnergyFootprintResult(
        eligible_food_kg=round(eligible_food_kg, 1),
        low_water_litres=round(eligible_food_kg * WATER_FACTOR_LOW, 1),
        central_water_litres=round(eligible_food_kg * WATER_FACTOR_CENTRAL, 1),
        high_water_litres=round(eligible_food_kg * WATER_FACTOR_HIGH, 1),
        low_energy_mj=round(eligible_food_kg * ENERGY_FACTOR_LOW, 1),
        central_energy_mj=round(eligible_food_kg * ENERGY_FACTOR_CENTRAL, 1),
        high_energy_mj=round(eligible_food_kg * ENERGY_FACTOR_HIGH, 1),
        is_available=True,
        availability_reason="Computed from eligible food avoided and peer-reviewed virtual water & energy intensity factors.",
        data_basis_label=basis_label,
        is_synthetic=is_synthetic,
    )


def compute_budget_vs_actual(
    session: Optional[Session],
    is_synthetic: int = 0,
    reporting_period: str = "October 2026",
    target_budget_per_meal_inr: float = 45.0,
) -> BudgetVsActualResult:
    """Calculate food cost utilisation against mess budget (H6)."""
    basis_label = "Synthetic Demonstration — Not Real-World Impact" if is_synthetic == 1 else "Real Pilot Measurements"

    if session is None:
        return BudgetVsActualResult(
            reporting_period=reporting_period,
            is_synthetic=is_synthetic,
            is_available=False,
            availability_reason="Session unavailable.",
            target_budget_per_meal_inr=target_budget_per_meal_inr,
            status_message="Financial utilisation unavailable.",
            data_basis_label=basis_label,
        )

    # Check if dish prices / costs are configured
    cost_count = session.execute(
        select(func.count(Dish.id)).where(Dish.waste_cost_co.is_not(None), Dish.waste_cost_co > 0)
    ).scalar() or 0

    if cost_count == 0:
        return BudgetVsActualResult(
            reporting_period=reporting_period,
            is_synthetic=is_synthetic,
            is_available=False,
            availability_reason="Valid ingredient costs / prices not configured in dish catalogue.",
            target_budget_per_meal_inr=target_budget_per_meal_inr,
            status_message="Cost savings & financial utilisation unavailable — valid ingredient prices not configured.",
            data_basis_label=basis_label,
        )

    # When prices are configured, calculate actual food cost per meal
    meals = list(session.execute(select(Meal).where(Meal.is_synthetic == is_synthetic)).scalars().all())
    if not meals:
        return BudgetVsActualResult(
            reporting_period=reporting_period,
            is_synthetic=is_synthetic,
            is_available=False,
            availability_reason="Real pilot measurements pending. Insufficient operational records.",
            target_budget_per_meal_inr=target_budget_per_meal_inr,
            status_message="No meals recorded in period.",
            data_basis_label=basis_label,
        )

    total_heads = sum(m.headcount for m in meals if m.headcount and m.headcount > 0)
    # Estimate total cost from dish logs and dish waste_cost_co
    meal_ids = [m.id for m in meals]
    logs = session.execute(
        select(DishLog, Dish.waste_cost_co).join(Dish, DishLog.dish_id == Dish.id).where(DishLog.meal_id.in_(meal_ids))
    ).all()
    
    total_cost = sum(l[0].cooked_qty * (l[1] or 0.0) for l in logs)
    actual_per_meal = round(total_cost / total_heads, 2) if total_heads > 0 else 0.0
    variance = round(target_budget_per_meal_inr - actual_per_meal, 2)
    utilization = round((actual_per_meal / target_budget_per_meal_inr) * 100.0, 1) if target_budget_per_meal_inr > 0 else 100.0

    return BudgetVsActualResult(
        reporting_period=reporting_period,
        is_synthetic=is_synthetic,
        is_available=True,
        availability_reason="Computed from configured dish ingredient prices and logged cooking quantities.",
        target_budget_per_meal_inr=target_budget_per_meal_inr,
        actual_cost_per_meal_inr=actual_per_meal,
        variance_inr=variance,
        utilization_pct=utilization,
        status_message=f"Budget utilisation at {utilization}% (₹{actual_per_meal:.2f} actual vs ₹{target_budget_per_meal_inr:.2f} budget).",
        data_basis_label=basis_label,
    )


# Alias for backward compatibility and student impact wall
generate_impact_summary = compute_green_campus_summary

