"""MessWise Data Validation Module.

Provides reusable validation logic and Pydantic schemas shared by:
- FastAPI API endpoints
- Streamlit application forms
- Synthetic data generator
- Automated test suites

Rejects invalid meal and dish records as specified in PLAN.md.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Canonical domain choices
VALID_MEAL_TYPES = ("breakfast", "lunch", "snacks", "dinner")
VALID_UNITS = ("kg", "L", "count")
VALID_WASTE_STAGES = ("serving_surplus", "plate_waste", "preparation")
VALID_REASON_TAGS = (
    "none",
    "overproduction",
    "low_popularity",
    "quality",
    "timing",
    "portioning",
    "other",
)
VALID_SOURCES = ("tally", "register", "manual", "synthetic")
VALID_ENTRY_METHODS = ("form", "voice", "photo", "scale", "synthetic", "manual")
VALID_CRITICALITY_TIERS = ("staple", "main", "side")
VALID_VERIFICATION_STATUSES = ("synthetic", "unverified_test", "verified_pilot")
VALID_EVENT_TYPES = ("holiday", "exam", "fest", "vacation", "normal", "other")
VALID_CHECKIN_RESPONSES = ("yes", "no", "maybe")

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_unit(unit: str) -> str:
    """Normalize unit strings to 'kg', 'L', or 'count'."""
    u = unit.strip()
    u_lower = u.lower()
    if u_lower in ("kg", "kgs", "kilogram", "kilograms", "kilo", "kilolu"):
        return "kg"
    if u_lower in ("l", "liter", "liters", "litre", "litres"):
        return "L"
    if u_lower in ("count", "counts", "nos", "pieces", "units", "rotis"):
        return "count"
    return u


def normalize_meal_type(meal_type: str) -> str:
    """Normalize meal type to lower case."""
    return meal_type.strip().lower()


class MealCreate(BaseModel):
    """Schema for creating a meal record."""

    date: str = Field(..., description="Meal date in YYYY-MM-DD format")
    meal_type: str = Field(..., description="Meal type: breakfast, lunch, snacks, dinner")
    headcount: int = Field(..., description="Actual or tally headcount (must be >= 0)")
    hostel_strength: int = Field(..., description="Total hostel strength/capacity (must be >= 0)")
    event_flag: int = Field(0, description="Flag for special event/fest (0 or 1)")
    exam_flag: int = Field(0, description="Flag for examination period (0 or 1)")
    holiday_flag: int = Field(0, description="Flag for holiday/weekend (0 or 1)")
    temp_c: Optional[float] = Field(None, description="Ambient temperature in Celsius")
    rain_mm: Optional[float] = Field(None, description="Rainfall in millimeters (must be >= 0)")
    source: str = Field("manual", description="Data source: tally, register, manual, synthetic")
    is_synthetic: int = Field(0, description="0 for real pilot data, 1 for synthetic demo data")
    verification_status: str = Field("unverified_test", description="Data provenance: synthetic, unverified_test, verified_pilot")
    mess_id: str = Field("default_mess", description="Site or campus mess identifier")

    model_config = ConfigDict(extra="forbid")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Meal date is required and cannot be empty.")
        if not DATE_REGEX.match(v):
            raise ValueError(f"Date '{v}' must be in YYYY-MM-DD format.")
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date '{v}' is not a valid calendar date.")
        return v

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, v: str) -> str:
        v_norm = normalize_meal_type(v)
        if v_norm not in VALID_MEAL_TYPES:
            raise ValueError(
                f"Invalid meal type '{v}'. Allowed types: {', '.join(VALID_MEAL_TYPES)}."
            )
        return v_norm

    @field_validator("headcount")
    @classmethod
    def validate_headcount(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"Headcount cannot be negative (got {v}).")
        return v

    @field_validator("hostel_strength")
    @classmethod
    def validate_hostel_strength(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"Hostel strength cannot be negative (got {v}).")
        return v

    @field_validator("event_flag", "exam_flag", "holiday_flag", "is_synthetic")
    @classmethod
    def validate_flags(cls, v: int, info) -> int:
        if v not in (0, 1):
            raise ValueError(f"{info.field_name} must be 0 or 1 (got {v}).")
        return v

    @field_validator("rain_mm")
    @classmethod
    def validate_rain(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"Rainfall cannot be negative (got {v}).")
        return v

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification_status '{v}'. Allowed: {', '.join(VALID_VERIFICATION_STATUSES)}."
            )
        return v_norm

    @model_validator(mode="after")
    def sync_synthetic_verification(self) -> MealCreate:
        if self.is_synthetic == 1 and self.verification_status != "synthetic":
            self.verification_status = "synthetic"
        return self


class DishCreate(BaseModel):
    """Schema for registering a dish."""

    name: str = Field(..., min_length=1, description="Dish name")
    category: str = Field("main", description="Category: staple, main, side, etc.")
    unit: str = Field("kg", description="Measurement unit: kg, L, count")
    standard_portion: Optional[float] = Field(None, description="Standard portion per person")
    prep_loss_pct: float = Field(0.0, description="Preparation loss percentage (0.0 to 1.0)")
    criticality_tier: str = Field("main", description="Criticality tier: staple, main, side")
    batch_size: Optional[float] = Field(None, description="Practical batch size (must be > 0 if specified)")
    shortage_cost_cu: Optional[float] = Field(None, description="Manager-configured shortage cost per unit (must be > 0)")
    waste_cost_co: Optional[float] = Field(None, description="Manager-configured overage/waste cost per unit (must be > 0)")
    cost_ratio_k: Optional[float] = Field(None, description="Manager-configured cost ratio Cu / Co (must be > 0)")
    is_synthetic: int = Field(0, description="0 for real, 1 for synthetic")
    mess_id: str = Field("default_mess", description="Mess or campus site identifier")

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Dish name cannot be empty.")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        u_norm = normalize_unit(v)
        if u_norm not in VALID_UNITS:
            raise ValueError(f"Invalid unit '{v}'. Allowed units: {', '.join(VALID_UNITS)}.")
        return u_norm

    @field_validator("prep_loss_pct")
    @classmethod
    def validate_prep_loss(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError(f"Prep loss percentage must be between 0.0 and 1.0 (got {v}).")
        return v

    @field_validator("criticality_tier")
    @classmethod
    def validate_criticality(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in VALID_CRITICALITY_TIERS:
            raise ValueError(
                f"Invalid criticality tier '{v}'. Allowed: {', '.join(VALID_CRITICALITY_TIERS)}."
            )
        return v_norm

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError(f"Batch size must be greater than 0 (got {v}).")
        return v

    @field_validator("shortage_cost_cu", "waste_cost_co", "cost_ratio_k")
    @classmethod
    def validate_cost_params(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError(f"Cost parameter must be positive (> 0, got {v}).")
        return v

    @field_validator("is_synthetic")
    @classmethod
    def validate_synth_flag(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"is_synthetic must be 0 or 1 (got {v}).")
        return v


class PlanRequest(BaseModel):
    """Schema for cooking quantity plan request (B1-B5)."""

    date: str = Field(..., description="Target meal date in YYYY-MM-DD format")
    meal_type: str = Field(..., description="Meal type: breakfast, lunch, snacks, dinner")
    service_level: float = Field(0.95, description="Target service level between 0.50 and 0.999")
    prep_loss_pct: float = Field(0.03, description="Preparation loss allowance (0.0 to 0.25)")
    hostel_strength: int = Field(500, description="Total hostel strength capacity")
    is_synthetic: int = Field(0, description="0 for real pilot data, 1 for synthetic demo data")
    batch_sizes: Optional[Dict[str, float]] = Field(None, description="Optional custom batch sizes keyed by dish name or ID")
    cost_mode: bool = Field(False, description="Enable B4 Cost-Aware Newsvendor optimiser")
    safety_floor: float = Field(0.90, description="Minimum service level floor for cost-aware planner (default 0.90)")
    cost_configs: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Optional per-dish or per-category cost configs (Cu, Co, k)")
    manager_overrides: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Optional per-dish manager overrides (service_level, reason)")

    model_config = ConfigDict(extra="forbid")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        v = v.strip()
        if not v or not DATE_REGEX.match(v):
            raise ValueError(f"Date '{v}' must be in YYYY-MM-DD format.")
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date '{v}' is not a valid calendar date.")
        return v

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, v: str) -> str:
        v_norm = normalize_meal_type(v)
        if v_norm not in VALID_MEAL_TYPES:
            raise ValueError(f"Invalid meal type '{v}'. Allowed types: {', '.join(VALID_MEAL_TYPES)}.")
        return v_norm

    @field_validator("service_level")
    @classmethod
    def validate_service_level(cls, v: float) -> float:
        if v < 0.50 or v > 0.999:
            raise ValueError(f"Service level must be between 0.50 and 0.999 (got {v}).")
        return v

    @field_validator("safety_floor")
    @classmethod
    def validate_safety_floor(cls, v: float) -> float:
        if v < 0.50 or v > 0.999:
            raise ValueError(f"Safety floor must be between 0.50 and 0.999 (got {v}).")
        return v

    @field_validator("prep_loss_pct")
    @classmethod
    def validate_prep_loss(cls, v: float) -> float:
        if v < 0.0 or v > 0.25:
            raise ValueError(f"Preparation loss allowance must be between 0.0 and 0.25 (got {v}).")
        return v

    @field_validator("hostel_strength")
    @classmethod
    def validate_strength(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Hostel strength must be greater than 0 (got {v}).")
        return v

    @field_validator("is_synthetic")
    @classmethod
    def validate_synthetic(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"is_synthetic must be 0 or 1 (got {v}).")
        return v


class SimulationRequest(BaseModel):
    """Schema for running historical savings simulation (E3)."""

    is_synthetic: int = Field(0, description="0 for real pilot data, 1 for synthetic demo data")
    start_date: Optional[str] = Field(None, description="Optional start date YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="Optional end date YYYY-MM-DD")
    meal_type: Optional[str] = Field(None, description="breakfast, lunch, dinner, or all")
    service_level: float = Field(0.95, description="Target service level between 0.50 and 0.999")
    hostel_strength: int = Field(500, description="Hostel capacity")

    model_config = ConfigDict(extra="forbid")

    @field_validator("is_synthetic")
    @classmethod
    def validate_synthetic(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"is_synthetic must be 0 or 1 (got {v}).")
        return v

    @field_validator("service_level")
    @classmethod
    def validate_service_level(cls, v: float) -> float:
        if v < 0.50 or v > 0.999:
            raise ValueError(f"Service level must be between 0.50 and 0.999 (got {v}).")
        return v

    @field_validator("hostel_strength")
    @classmethod
    def validate_strength(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Hostel strength must be greater than 0 (got {v}).")
        return v


class BlindForecastRequest(BaseModel):
    """Schema for requesting a blind forecast (E4)."""

    meal_id: int = Field(..., gt=0, description="ID of the historical meal record")
    service_level: float = Field(0.95, description="Target service level between 0.50 and 0.999")
    hostel_strength: int = Field(500, description="Hostel capacity")

    model_config = ConfigDict(extra="forbid")

    @field_validator("service_level")
    @classmethod
    def validate_service_level(cls, v: float) -> float:
        if v < 0.50 or v > 0.999:
            raise ValueError(f"Service level must be between 0.50 and 0.999 (got {v}).")
        return v

    @field_validator("hostel_strength")
    @classmethod
    def validate_strength(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Hostel strength must be greater than 0 (got {v}).")
        return v


class DishLogCreate(BaseModel):
    """Schema for logging dish consumption and leftover per meal."""

    meal_id: int = Field(..., description="ID of the parent meal record")
    dish_id: int = Field(..., description="ID of the dish")
    cooked_qty: float = Field(..., description="Quantity cooked in specified unit (>= 0)")
    leftover_qty: float = Field(..., description="Quantity leftover in specified unit (>= 0)")
    unit: str = Field("kg", description="Unit of measurement: kg, L, count")
    ran_out: int = Field(0, description="1 if dish ran out during meal, 0 otherwise")
    waste_stage: str = Field("serving_surplus", description="Stage: serving_surplus, plate_waste, preparation")
    reason_tag: str = Field("none", description="Reason for leftover/waste")
    entry_method: str = Field("form", description="Entry method: form, voice, photo, scale, synthetic")
    photo_ref: Optional[str] = Field(None, description="Optional photo identifier or path")
    is_synthetic: int = Field(0, description="0 for real pilot data, 1 for synthetic demo data")
    verification_status: str = Field("unverified_test", description="Data provenance: synthetic, unverified_test, verified_pilot")
    mess_id: str = Field("default_mess", description="Site or campus mess identifier")

    model_config = ConfigDict(extra="forbid")

    @field_validator("cooked_qty")
    @classmethod
    def validate_cooked_qty(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Cooked quantity cannot be negative (got {v}).")
        return v

    @field_validator("leftover_qty")
    @classmethod
    def validate_leftover_qty(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Leftover quantity cannot be negative (got {v}).")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        u_norm = normalize_unit(v)
        if u_norm not in VALID_UNITS:
            raise ValueError(f"Invalid unit '{v}'. Allowed units: {', '.join(VALID_UNITS)}.")
        return u_norm

    @field_validator("ran_out", "is_synthetic")
    @classmethod
    def validate_binary_flags(cls, v: int, info) -> int:
        if v not in (0, 1):
            raise ValueError(f"{info.field_name} must be 0 or 1 (got {v}).")
        return v

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification_status '{v}'. Allowed: {', '.join(VALID_VERIFICATION_STATUSES)}."
            )
        return v_norm

    @field_validator("waste_stage")
    @classmethod
    def validate_waste_stage(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in VALID_WASTE_STAGES:
            raise ValueError(
                f"Invalid waste stage '{v}'. Allowed: {', '.join(VALID_WASTE_STAGES)}."
            )
        return v_norm

    @field_validator("reason_tag")
    @classmethod
    def validate_reason_tag(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in VALID_REASON_TAGS:
            raise ValueError(
                f"Invalid reason tag '{v}'. Allowed: {', '.join(VALID_REASON_TAGS)}."
            )
        return v_norm

    @model_validator(mode="after")
    def validate_leftover_not_exceeding_cooked(self) -> DishLogCreate:
        if self.is_synthetic == 1 and self.verification_status != "synthetic":
            self.verification_status = "synthetic"
        if self.leftover_qty > self.cooked_qty:
            raise ValueError(
                f"Leftover quantity ({self.leftover_qty}) cannot be greater than "
                f"cooked quantity ({self.cooked_qty})."
            )
        return self


class DishEntryItem(BaseModel):
    """Convenience schema for dish items entered alongside a meal in UI forms."""

    dish_name: str = Field(..., description="Name of dish")
    cooked_qty: float = Field(..., description="Cooked quantity (>= 0)")
    leftover_qty: float = Field(..., description="Leftover quantity (>= 0)")
    unit: str = Field("kg", description="Unit: kg, L, count")
    ran_out: int = Field(0, description="Ran-out flag (0 or 1)")
    waste_stage: str = Field("serving_surplus", description="Waste stage")
    reason_tag: str = Field("none", description="Reason tag")

    model_config = ConfigDict(extra="forbid")

    @field_validator("dish_name")
    @classmethod
    def validate_dish_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Dish name cannot be empty.")
        return v

    @field_validator("cooked_qty")
    @classmethod
    def validate_cooked(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Cooked quantity cannot be negative (got {v}).")
        return v

    @field_validator("leftover_qty")
    @classmethod
    def validate_leftover(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Leftover quantity cannot be negative (got {v}).")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        u_norm = normalize_unit(v)
        if u_norm not in VALID_UNITS:
            raise ValueError(f"Invalid unit '{v}'. Allowed: {', '.join(VALID_UNITS)}.")
        return u_norm

    @field_validator("ran_out")
    @classmethod
    def validate_ran_out(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"ran_out must be 0 or 1 (got {v}).")
        return v

    @model_validator(mode="after")
    def validate_leftover_vs_cooked(self) -> DishEntryItem:
        if self.leftover_qty > self.cooked_qty:
            raise ValueError(
                f"Leftover quantity ({self.leftover_qty}) cannot be greater than "
                f"cooked quantity ({self.cooked_qty})."
            )
        return self


# Reusable plain dictionary validation functions for UI forms
def validate_meal_dict(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate meal dictionary and return (is_valid, error_list) without raising exceptions."""
    errors: List[str] = []

    # Required fields
    date_val = str(data.get("date", "")).strip()
    if not date_val:
        errors.append("Meal date is required.")
    elif not DATE_REGEX.match(date_val):
        errors.append(f"Meal date '{date_val}' must be in YYYY-MM-DD format.")
    else:
        try:
            datetime.strptime(date_val, "%Y-%m-%d")
        except ValueError:
            errors.append(f"Meal date '{date_val}' is invalid.")

    meal_type = normalize_meal_type(str(data.get("meal_type", "")))
    if meal_type not in VALID_MEAL_TYPES:
        errors.append(
            f"Invalid meal type '{data.get('meal_type')}'. Must be one of: {', '.join(VALID_MEAL_TYPES)}."
        )

    try:
        headcount = int(data.get("headcount", -1))
        if headcount < 0:
            errors.append(f"Headcount cannot be negative (got {headcount}).")
    except (ValueError, TypeError):
        errors.append("Headcount must be a valid integer.")

    try:
        hostel_strength = int(data.get("hostel_strength", -1))
        if hostel_strength < 0:
            errors.append(f"Hostel strength cannot be negative (got {hostel_strength}).")
    except (ValueError, TypeError):
        errors.append("Hostel strength must be a valid integer.")

    for flag_name in ("event_flag", "exam_flag", "holiday_flag", "is_synthetic"):
        flag_val = data.get(flag_name, 0)
        if flag_val not in (0, 1, False, True):
            errors.append(f"{flag_name} must be 0 or 1 (got {flag_val}).")

    rain_mm = data.get("rain_mm")
    if rain_mm is not None and rain_mm != "":
        try:
            if float(rain_mm) < 0:
                errors.append(f"Rainfall cannot be negative (got {rain_mm}).")
        except (ValueError, TypeError):
            errors.append(f"Rainfall must be a numeric value.")

    temp_c = data.get("temp_c")
    if temp_c is not None and temp_c != "":
        try:
            float(temp_c)
        except (ValueError, TypeError):
            errors.append("Temperature must be a numeric value.")

    return len(errors) == 0, errors


def validate_dish_log_dict(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate dish log dictionary and return (is_valid, error_list) without raising exceptions."""
    errors: List[str] = []

    dish_name = str(data.get("dish_name", data.get("name", ""))).strip()
    dish_id = data.get("dish_id")
    if not dish_name and dish_id is None:
        errors.append("Dish name or dish_id is required.")

    cooked_qty: Optional[float] = None
    try:
        cooked_qty = float(data.get("cooked_qty", -1))
        if cooked_qty < 0:
            errors.append(f"Cooked quantity cannot be negative (got {cooked_qty}).")
    except (ValueError, TypeError):
        errors.append("Cooked quantity must be a valid number.")

    leftover_qty: Optional[float] = None
    try:
        leftover_qty = float(data.get("leftover_qty", -1))
        if leftover_qty < 0:
            errors.append(f"Leftover quantity cannot be negative (got {leftover_qty}).")
    except (ValueError, TypeError):
        errors.append("Leftover quantity must be a valid number.")

    if cooked_qty is not None and leftover_qty is not None and cooked_qty >= 0 and leftover_qty >= 0:
        if leftover_qty > cooked_qty:
            errors.append(
                f"Leftover quantity ({leftover_qty}) cannot be greater than cooked quantity ({cooked_qty})."
            )

    unit = normalize_unit(str(data.get("unit", "kg")))
    if unit not in VALID_UNITS:
        errors.append(f"Invalid unit '{data.get('unit')}'. Must be one of: {', '.join(VALID_UNITS)}.")

    for flag_name in ("ran_out", "is_synthetic"):
        flag_val = data.get(flag_name, 0)
        if flag_val not in (0, 1, False, True):
            errors.append(f"{flag_name} must be 0 or 1 (got {flag_val}).")

    waste_stage = str(data.get("waste_stage", "serving_surplus")).strip().lower()
    if waste_stage and waste_stage not in VALID_WASTE_STAGES:
        errors.append(
            f"Invalid waste stage '{waste_stage}'. Must be one of: {', '.join(VALID_WASTE_STAGES)}."
        )

    reason_tag = str(data.get("reason_tag", "none")).strip().lower()
    if reason_tag and reason_tag not in VALID_REASON_TAGS:
        errors.append(
            f"Invalid reason tag '{reason_tag}'. Must be one of: {', '.join(VALID_REASON_TAGS)}."
        )

    return len(errors) == 0, errors


class PredictedSurplusGenerateRequest(BaseModel):
    """Schema for requesting G1 predicted-surplus alert generation from meal plan."""

    date: str = Field(..., description="Target meal date in YYYY-MM-DD format")
    meal_type: str = Field(..., description="Meal type: breakfast, lunch, snacks, dinner")
    threshold_kg: float = Field(2.0, ge=0.1, description="Minimum surplus threshold to trigger an alert")
    service_level: float = Field(0.95, ge=0.50, le=0.999, description="Service level for planning")
    is_synthetic: int = Field(0, description="0 for real pilot data, 1 for synthetic demo data")

    model_config = ConfigDict(extra="forbid")


class MeasuredSurplusGenerateRequest(BaseModel):
    """Schema for requesting G1 measured-surplus alert generation from recorded meal logs."""

    meal_id: int = Field(..., ge=1, description="Meal ID with recorded dish logs")
    threshold_kg: float = Field(1.0, ge=0.1, description="Minimum leftover threshold to trigger an alert")
    cooking_completed_at: Optional[str] = Field(None, description="ISO timestamp when cooking completed")

    model_config = ConfigDict(extra="forbid")


class SafetyObservationCreate(BaseModel):
    """Schema for recording a G2 time/temperature observation."""

    temp_c: float = Field(..., ge=-20.0, le=120.0, description="Recorded temperature in Celsius")
    temp_unit: str = Field("C", description="Temperature unit ('C' or 'F')")
    hold_type: str = Field("hot", description="Holding type: 'hot', 'ambient', or 'cold'")
    observed_at: Optional[str] = Field(None, description="ISO timestamp of observation")
    observed_by: str = Field("cook", description="Staff identifier recording the observation")
    cooking_completed_at: Optional[str] = Field(None, description="ISO timestamp when cooking completed")
    suspected_contamination: bool = Field(False, description="Flag for suspected contamination or spoilage")
    notes: str = Field("", description="Optional observation notes")

    model_config = ConfigDict(extra="forbid")


class ManagerDecisionRequest(BaseModel):
    """Schema for manager review decision on a surplus alert."""

    action: str = Field(..., description="Decision action: 'approve' or 'dismiss'")
    manager_who: str = Field("manager", description="Kitchen manager identifier")
    manager_reason: Optional[str] = Field(None, description="Reason for decision / dismissal")
    partner_name: Optional[str] = Field(None, description="Optional registered partner NGO name")
    partner_phone: Optional[str] = Field(None, description="Optional partner contact phone for WhatsApp draft")

    model_config = ConfigDict(extra="forbid")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        act = v.strip().lower()
        if act not in ("approve", "dismiss"):
            raise ValueError("Action must be either 'approve' or 'dismiss'.")
        return act


class VoiceParseRequest(BaseModel):
    """Schema for voice utterance parsing request (C5)."""

    transcript: str = Field(..., min_length=1, description="Speech transcript text to parse")
    language: str = Field("auto", description="Language hint: auto, en-IN, hi-IN, te-IN")

    model_config = ConfigDict(extra="forbid")


class EntranceTallyCreate(BaseModel):
    """Schema for recording aggregate attendance check-ins (C7)."""

    meal_id: int = Field(..., description="Target meal ID")
    time_bucket: str = Field(..., min_length=1, description="15-minute service checkpoint bucket")
    headcount_count: int = Field(..., ge=0, description="Aggregate headcount arrivals in bucket")
    recorded_by: str = Field("staff", description="Staff / monitor recorder identifier")
    is_synthetic: int = Field(0, ge=0, le=1, description="0 for real, 1 for synthetic")

    model_config = ConfigDict(extra="forbid")


class PhotoEstimateRequest(BaseModel):
    """Schema for calibrated photo waste estimation request (C6)."""

    dish_name: str = Field("Rice", description="Dish category name in container")
    container_type: str = Field("20L_standard_bin", description="Profile of calibrated collection container")
    fill_percentage: float = Field(50.0, ge=0.0, le=100.0, description="Graduation marker fill level percentage")

    model_config = ConfigDict(extra="forbid")


class SmartScalePayload(BaseModel):
    """Schema for digital scale payload (C8)."""

    device_id: str = Field("HX711-ESP32-SCALE01", description="Scale hardware identifier")
    gross_weight_kg: float = Field(..., ge=0.0, description="Gross scale weight in kg")
    tare_weight_kg: float = Field(0.0, ge=0.0, description="Tare container weight in kg")
    net_weight_kg: Optional[float] = Field(None, description="Net weight in kg")
    unit: str = Field("kg", description="Measurement unit (must be kg)")
    is_stable: bool = Field(True, description="Whether reading has stabilized")

    model_config = ConfigDict(extra="forbid")


class CampusEventCreate(BaseModel):
    """Schema for adding a campus or academic calendar event (A7)."""

    event_name: str = Field(..., min_length=1, description="Event or exam name")
    event_type: str = Field("holiday", description="Event type: holiday, exam, fest, vacation, normal, other")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    expected_attendance_factor: float = Field(1.0, ge=0.1, le=2.0, description="Multiplier effect on baseline attendance")
    notes: Optional[str] = Field(None, description="Optional context or notes")
    mess_id: str = Field("default_mess", description="Target mess or campus scope")

    model_config = ConfigDict(extra="forbid")

    @field_validator("event_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type '{v}'. Allowed: {', '.join(VALID_EVENT_TYPES)}.")
        return v_norm

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates(cls, v: str) -> str:
        v = v.strip()
        if not DATE_REGEX.match(v):
            raise ValueError(f"Date '{v}' must be YYYY-MM-DD.")
        return v


class MealCheckInCreate(BaseModel):
    """Schema for anonymous aggregate student meal check-in (A9, F1)."""

    meal_date: str = Field(..., description="Target meal date YYYY-MM-DD")
    meal_type: str = Field(..., description="Meal type: breakfast, lunch, snacks, dinner")
    response: str = Field(..., description="'yes', 'no', or 'maybe'")
    device_hash: Optional[str] = Field(None, description="Privacy-preserving anonymous client hash")
    mess_id: str = Field("default_mess", description="Mess scope")
    is_synthetic: int = Field(0, description="0 for real, 1 for synthetic")

    model_config = ConfigDict(extra="forbid")

    @field_validator("meal_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        v = v.strip()
        if not DATE_REGEX.match(v):
            raise ValueError(f"Date '{v}' must be YYYY-MM-DD.")
        return v

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, v: str) -> str:
        v_norm = normalize_meal_type(v)
        if v_norm not in VALID_MEAL_TYPES:
            raise ValueError(f"Invalid meal_type '{v}'. Allowed: {', '.join(VALID_MEAL_TYPES)}.")
        return v_norm

    @field_validator("response")
    @classmethod
    def validate_response(cls, v: str) -> str:
        v_norm = v.strip().lower()
        if v_norm not in VALID_CHECKIN_RESPONSES:
            raise ValueError(f"Invalid check-in response '{v}'. Allowed: {', '.join(VALID_CHECKIN_RESPONSES)}.")
        return v_norm


class MealRatingCreate(BaseModel):
    """Schema for anonymous one-tap dish rating (A8, F2)."""

    meal_date: str = Field(..., description="Meal date YYYY-MM-DD")
    meal_type: str = Field(..., description="Meal type")
    dish_id: int = Field(..., gt=0, description="ID of rated dish")
    rating: int = Field(..., ge=1, le=5, description="Score 1 (poor) to 5 (excellent)")
    comment: Optional[str] = Field(None, max_length=255, description="Optional brief feedback")
    device_hash: Optional[str] = Field(None, description="Privacy-preserving anonymous client hash")
    mess_id: str = Field("default_mess", description="Mess scope")
    is_synthetic: int = Field(0, description="0 for real, 1 for synthetic")

    model_config = ConfigDict(extra="forbid")

    @field_validator("meal_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        v = v.strip()
        if not DATE_REGEX.match(v):
            raise ValueError(f"Date '{v}' must be YYYY-MM-DD.")
        return v

    @field_validator("meal_type")
    @classmethod
    def validate_meal_type(cls, v: str) -> str:
        v_norm = normalize_meal_type(v)
        if v_norm not in VALID_MEAL_TYPES:
            raise ValueError(f"Invalid meal_type '{v}'. Allowed: {', '.join(VALID_MEAL_TYPES)}.")
        return v_norm


class RecipeIngredientCreate(BaseModel):
    """Schema for ingredient line in a dish recipe (B9, B10)."""

    ingredient_name: str = Field(..., min_length=1, description="Ingredient name (e.g. Basmati Rice)")
    amount: float = Field(..., gt=0.0, description="Required amount for reference servings batch")
    unit: str = Field("kg", description="Unit of measurement (kg, L, etc.)")
    cost_per_unit: Optional[float] = Field(None, ge=0.0, description="Rupees per unit")
    cost_source: str = Field("configured", description="'configured', 'invoice', or 'unspecified'")

    model_config = ConfigDict(extra="forbid")


class RecipeCreate(BaseModel):
    """Schema for registering or updating a recipe (B9, B10)."""

    dish_id: int = Field(..., gt=0, description="ID of registered dish")
    servings_yield: float = Field(100.0, gt=0.0, description="Reference batch size (portions)")
    ingredients: List[RecipeIngredientCreate] = Field(default_factory=list, description="Ingredient breakdown")
    instructions: Optional[str] = Field(None, description="Preparation instructions")
    version: str = Field("v1.0", description="Recipe version")
    mess_id: str = Field("default_mess", description="Mess scope")

    model_config = ConfigDict(extra="forbid")


class ModelRetrainRequest(BaseModel):
    """Schema for triggering model retraining & champion-challenger registry evaluation (A11)."""

    mess_id: str = Field("default_mess", description="Mess scope to train on")
    is_synthetic: int = Field(0, description="0 for real data, 1 for synthetic demo data")
    force_promote: bool = Field(False, description="Promote challenger even if safety margins are equal")
    min_samples: int = Field(14, ge=7, description="Minimum training records required")

    model_config = ConfigDict(extra="forbid")


class WhatIfPlanRequest(BaseModel):
    """Schema for what-if scenario planning sandbox (B8)."""

    base_date: str = Field(..., description="Target meal date")
    meal_type: str = Field(..., description="Meal type")
    headcount_override: Optional[int] = Field(None, ge=0, description="Hypothetical headcount")
    service_level: float = Field(0.95, ge=0.50, le=0.999, description="Target service level")
    event_flag: Optional[int] = Field(None, ge=0, le=1, description="Simulate campus event")
    cost_mode: bool = Field(False, description="Enable B4 Newsvendor cost optimization")
    mess_id: str = Field("default_mess", description="Mess scope")
    is_synthetic: int = Field(0, description="0 for real, 1 for synthetic")

    model_config = ConfigDict(extra="forbid")


class TopUpPlanRequest(BaseModel):
    """Schema for progressive two-stage top-up cooking recommendations (B7)."""

    meal_id: Optional[int] = Field(None, description="Active meal ID if already started")
    date: str = Field(..., description="Target meal date")
    meal_type: str = Field(..., description="Meal type")
    initial_batch_pct: float = Field(0.70, ge=0.40, le=0.90, description="Initial batch share (40-90%)")
    elapsed_minutes: int = Field(30, ge=0, le=180, description="Minutes elapsed since service start")
    current_headcount_observed: Optional[int] = Field(None, ge=0, description="Observed arrivals so far")
    service_level: float = Field(0.95, ge=0.50, le=0.999)
    mess_id: str = Field("default_mess")
    is_synthetic: int = Field(0)

    model_config = ConfigDict(extra="forbid")



