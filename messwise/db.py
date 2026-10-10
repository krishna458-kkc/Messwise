"""MessWise Database Layer using SQLAlchemy and SQLite.

Implements the core tables specified in PLAN.md:
- meals: meal attendance and context features
- dishes: dish registry and metadata
- dish_log: per-meal cooked and leftover measurements
- predictions: prediction log frozen before outcomes
- overrides: human-in-the-loop decisions and reasons
- audit_log: audit trail for governance

Privacy-first: No student names, personal IDs, or biometric data are stored.
Synthetic separation: All tables supporting demo data include is_synthetic flag.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    relationship,
    sessionmaker,
)

from messwise.validation import (
    DishCreate,
    DishLogCreate,
    MealCreate,
    normalize_meal_type,
    normalize_unit,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class Meal(Base):
    """Meals table: stores meal-level attendance, strength, and environmental context."""

    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    meal_type = Column(String(20), nullable=False, index=True)  # breakfast, lunch, snacks, dinner
    headcount = Column(Integer, nullable=False)
    hostel_strength = Column(Integer, nullable=False)
    event_flag = Column(Integer, default=0, nullable=False)
    exam_flag = Column(Integer, default=0, nullable=False)
    holiday_flag = Column(Integer, default=0, nullable=False)
    temp_c = Column(Float, nullable=True)
    rain_mm = Column(Float, nullable=True)
    source = Column(String(50), default="manual", nullable=False)  # tally, register, manual, synthetic
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    verification_status = Column(
        String(30),
        default="unverified_test",
        nullable=False,
        index=True,
    )
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=False,
        index=True,
    )
    created_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )

    # Relationships
    dish_logs = relationship(
        "DishLog",
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="DishLog.id",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "meal_type": self.meal_type,
            "headcount": self.headcount,
            "hostel_strength": self.hostel_strength,
            "event_flag": self.event_flag,
            "exam_flag": self.exam_flag,
            "holiday_flag": self.holiday_flag,
            "temp_c": self.temp_c,
            "rain_mm": self.rain_mm,
            "source": self.source,
            "is_synthetic": self.is_synthetic,
            "verification_status": self.verification_status,
            "mess_id": self.mess_id,
            "created_at": self.created_at,
        }


class Dish(Base):
    """Dishes table: catalog of dishes with measurement units and properties."""

    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), default="main", nullable=False)  # staple, main, side, etc.
    unit = Column(String(20), default="kg", nullable=False)  # kg, L, count
    standard_portion = Column(Float, nullable=True)
    prep_loss_pct = Column(Float, default=0.0, nullable=False)
    criticality_tier = Column(String(20), default="main", nullable=False)  # staple, main, side
    batch_size = Column(Float, nullable=True, default=None)  # practical batch size (e.g. 5.0 kg)
    shortage_cost_cu = Column(Float, nullable=True, default=None)  # manager-configured shortage cost per unit
    waste_cost_co = Column(Float, nullable=True, default=None)  # manager-configured overage/waste cost per unit
    cost_ratio_k = Column(Float, nullable=True, default=None)  # manager-configured cost ratio Cu / Co
    is_synthetic = Column(Integer, default=0, nullable=False)
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=False,
        index=True,
    )

    dish_logs = relationship("DishLog", back_populates="dish")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit": self.unit,
            "standard_portion": self.standard_portion,
            "prep_loss_pct": self.prep_loss_pct,
            "criticality_tier": self.criticality_tier,
            "batch_size": self.batch_size,
            "shortage_cost_cu": self.shortage_cost_cu,
            "waste_cost_co": self.waste_cost_co,
            "cost_ratio_k": self.cost_ratio_k,
            "is_synthetic": self.is_synthetic,
            "mess_id": self.mess_id,
        }


class DishLog(Base):
    """Dish log table: per-meal cooked, leftover, and run-out records."""

    __tablename__ = "dish_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False, index=True)
    cooked_qty = Column(Float, nullable=False)
    leftover_qty = Column(Float, nullable=False)
    unit = Column(String(20), default="kg", nullable=False)
    ran_out = Column(Integer, default=0, nullable=False)
    waste_stage = Column(String(50), default="serving_surplus", nullable=False)
    reason_tag = Column(String(50), default="none", nullable=False)
    entry_method = Column(String(50), default="form", nullable=False)
    photo_ref = Column(String(255), nullable=True)
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    verification_status = Column(
        String(30),
        default="unverified_test",
        nullable=False,
        index=True,
    )
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=False,
        index=True,
    )
    created_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )

    # Relationships
    meal = relationship("Meal", back_populates="dish_logs")
    dish = relationship("Dish", back_populates="dish_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meal_id": self.meal_id,
            "dish_id": self.dish_id,
            "dish_name": self.dish.name if self.dish else None,
            "cooked_qty": self.cooked_qty,
            "leftover_qty": self.leftover_qty,
            "unit": self.unit,
            "ran_out": self.ran_out,
            "waste_stage": self.waste_stage,
            "reason_tag": self.reason_tag,
            "entry_method": self.entry_method,
            "photo_ref": self.photo_ref,
            "is_synthetic": self.is_synthetic,
            "verification_status": self.verification_status,
            "mess_id": self.mess_id,
            "created_at": self.created_at,
        }


class Prediction(Base):
    """Predictions table: logs frozen forecasts before outcomes for accountability."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
    meal_date = Column(String(10), nullable=False)
    meal_type = Column(String(20), nullable=False)
    model_version = Column(String(50), default="v0.1.0-baseline", nullable=False)
    h_hat = Column(Float, nullable=False)
    h_lo = Column(Float, nullable=False)
    h_hi = Column(Float, nullable=False)
    service_level = Column(Float, default=0.95, nullable=False)
    plan_json = Column(Text, nullable=True)
    actual_headcount = Column(Integer, nullable=True)
    baseline_last_week = Column(Float, nullable=True)
    baseline_trailing_avg = Column(Float, nullable=True)
    forecast_error = Column(Float, nullable=True)  # actual - h_hat
    abs_error = Column(Float, nullable=True)       # |actual - h_hat|
    status = Column(String(20), default="pending", nullable=False)  # pending | evaluated
    explanation = Column(Text, nullable=True)
    context_json = Column(Text, nullable=True)
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "meal_date": self.meal_date,
            "meal_type": self.meal_type,
            "model_version": self.model_version,
            "h_hat": self.h_hat,
            "h_lo": self.h_lo,
            "h_hi": self.h_hi,
            "service_level": self.service_level,
            "plan_json": self.plan_json,
            "actual_headcount": self.actual_headcount,
            "baseline_last_week": self.baseline_last_week,
            "baseline_trailing_avg": self.baseline_trailing_avg,
            "forecast_error": self.forecast_error,
            "abs_error": self.abs_error,
            "status": self.status,
            "explanation": self.explanation,
            "context_json": self.context_json,
            "is_synthetic": self.is_synthetic,
            "mess_id": self.mess_id,
        }


class Override(Base):
    """Overrides table: records staff changes to recommendations with reasons."""

    __tablename__ = "overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
    role = Column(String(50), default="cook", nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=True)
    recommended_qty = Column(Float, nullable=False)
    final_qty = Column(Float, nullable=False)
    reason = Column(String(255), nullable=False)
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ts": self.ts,
            "role": self.role,
            "dish_id": self.dish_id,
            "meal_id": self.meal_id,
            "recommended_qty": self.recommended_qty,
            "final_qty": self.final_qty,
            "reason": self.reason,
            "is_synthetic": self.is_synthetic,
            "mess_id": self.mess_id,
        }


class AuditLog(Base):
    """Audit log table: tracks administrative actions and data modifications."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
    who = Column(String(100), default="system", nullable=False)
    action = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=True,
        index=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ts": self.ts,
            "who": self.who,
            "action": self.action,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "mess_id": self.mess_id,
        }


class SurplusEvent(Base):
    """Surplus events table: stores predicted and measured surplus alerts, safety clock, and eligibility."""

    __tablename__ = "surplus_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(
        String(35),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=True, index=True)
    meal_date = Column(String(10), nullable=False, index=True)
    meal_type = Column(String(20), nullable=False, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False, index=True)
    surplus_type = Column(String(20), nullable=False)  # "predicted" | "measured"
    estimated_qty = Column(Float, nullable=False)
    unit = Column(String(20), default="kg", nullable=False)
    uncertainty_range = Column(String(100), nullable=True)  # e.g. "6.0 – 9.0 kg"

    # G2 Food-Safety Clock fields
    cooking_completed_at = Column(String(35), nullable=True)
    hold_type = Column(String(20), default="hot", nullable=False)  # "hot" | "ambient" | "cold"
    safe_window_hours = Column(Float, default=4.0, nullable=False)
    safe_cutoff_at = Column(String(35), nullable=True)
    current_temp_c = Column(Float, nullable=True)
    temp_recorded_at = Column(String(35), nullable=True)
    temp_log_json = Column(Text, nullable=True)  # JSON serialized list of temperature observations
    suspected_contamination = Column(Integer, default=0, nullable=False)

    # Eligibility & G1/G2 states
    eligibility_status = Column(
        String(50),
        default="pending_inspection",
        nullable=False,
    )  # "eligible" | "pending_inspection" | "blocked_expired" | "blocked_temperature" | "blocked_missing_data" | "blocked_contamination" | "dismissed"
    blocking_reason = Column(Text, nullable=True)
    policy_version = Column(String(50), default="FSSAI-2019-Reg4-Sched2", nullable=False)

    # Manager review
    manager_status = Column(String(20), default="pending", nullable=False)  # "pending" | "approved" | "dismissed"
    manager_who = Column(String(100), nullable=True)
    manager_reason = Column(Text, nullable=True)
    manager_action_at = Column(String(35), nullable=True)

    # Partner & communication draft
    partner_name = Column(String(100), nullable=True)
    partner_phone = Column(String(50), nullable=True)
    communication_draft = Column(Text, nullable=True)

    # Synthetic separation
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=False,
        index=True,
    )

    # Relationships
    meal = relationship("Meal")
    dish = relationship("Dish")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "meal_id": self.meal_id,
            "meal_date": self.meal_date,
            "meal_type": self.meal_type,
            "dish_id": self.dish_id,
            "dish_name": self.dish.name if self.dish else None,
            "surplus_type": self.surplus_type,
            "estimated_qty": self.estimated_qty,
            "unit": self.unit,
            "uncertainty_range": self.uncertainty_range,
            "cooking_completed_at": self.cooking_completed_at,
            "hold_type": self.hold_type,
            "safe_window_hours": self.safe_window_hours,
            "safe_cutoff_at": self.safe_cutoff_at,
            "current_temp_c": self.current_temp_c,
            "temp_recorded_at": self.temp_recorded_at,
            "temp_log_json": self.temp_log_json,
            "suspected_contamination": bool(self.suspected_contamination),
            "eligibility_status": self.eligibility_status,
            "blocking_reason": self.blocking_reason,
            "policy_version": self.policy_version,
            "manager_status": self.manager_status,
            "manager_who": self.manager_who,
            "manager_reason": self.manager_reason,
            "manager_action_at": self.manager_action_at,
            "partner_name": self.partner_name,
            "partner_phone": self.partner_phone,
            "communication_draft": self.communication_draft,
            "is_synthetic": self.is_synthetic,
            "mess_id": self.mess_id,
        }


class EntranceTally(Base):
    """Entrance tally table: stores privacy-preserving aggregate check-in tallies in 15-minute buckets (C7)."""

    __tablename__ = "entrance_tallies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False, index=True)
    time_bucket = Column(String(50), nullable=False)  # e.g. "19:30-19:45"
    headcount_count = Column(Integer, nullable=False)
    recorded_by = Column(String(100), default="staff", nullable=False)
    created_at = Column(
        String(35),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    mess_id = Column(
        String(50),
        default="default_mess",
        nullable=False,
        index=True,
    )

    meal = relationship("Meal")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meal_id": self.meal_id,
            "time_bucket": self.time_bucket,
            "headcount_count": self.headcount_count,
            "recorded_by": self.recorded_by,
            "created_at": self.created_at,
            "is_synthetic": self.is_synthetic,
            "mess_id": self.mess_id,
        }


class CampusEvent(Base):
    """Campus events and exam calendar (A7)."""

    __tablename__ = "campus_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(100), nullable=False)
    event_type = Column(String(50), default="holiday", nullable=False)  # exam, holiday, fest, vacation, normal, other
    start_date = Column(String(10), nullable=False, index=True)
    end_date = Column(String(10), nullable=False, index=True)
    expected_attendance_factor = Column(Float, default=1.0, nullable=False)
    notes = Column(Text, nullable=True)
    mess_id = Column(String(50), default="default_mess", nullable=False, index=True)
    created_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_name": self.event_name,
            "event_type": self.event_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "expected_attendance_factor": self.expected_attendance_factor,
            "notes": self.notes,
            "mess_id": self.mess_id,
            "created_at": self.created_at,
        }


class MealCheckIn(Base):
    """Anonymous aggregate student meal check-in responses (A9, F1)."""

    __tablename__ = "meal_checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_date = Column(String(10), nullable=False, index=True)
    meal_type = Column(String(20), nullable=False, index=True)
    response = Column(String(10), nullable=False)  # yes, no, maybe
    device_hash = Column(String(64), nullable=True, index=True)
    mess_id = Column(String(50), default="default_mess", nullable=False, index=True)
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    created_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meal_date": self.meal_date,
            "meal_type": self.meal_type,
            "response": self.response,
            "device_hash": self.device_hash,
            "mess_id": self.mess_id,
            "is_synthetic": self.is_synthetic,
            "created_at": self.created_at,
        }


class MealRating(Base):
    """Anonymous dish-level ratings for menu popularity (A8, F2)."""

    __tablename__ = "meal_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_date = Column(String(10), nullable=False, index=True)
    meal_type = Column(String(20), nullable=False, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(String(255), nullable=True)
    device_hash = Column(String(64), nullable=True, index=True)
    mess_id = Column(String(50), default="default_mess", nullable=False, index=True)
    is_synthetic = Column(Integer, default=0, nullable=False, index=True)
    created_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )

    dish = relationship("Dish")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meal_date": self.meal_date,
            "meal_type": self.meal_type,
            "dish_id": self.dish_id,
            "dish_name": self.dish.name if self.dish else None,
            "rating": self.rating,
            "comment": self.comment,
            "device_hash": self.device_hash,
            "mess_id": self.mess_id,
            "is_synthetic": self.is_synthetic,
            "created_at": self.created_at,
        }


class ModelRegistry(Base):
    """Model registry table: versions, metrics, time splits, and champion status (A11)."""

    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), unique=True, nullable=False, index=True)
    model_type = Column(String(50), nullable=False)
    training_start_date = Column(String(10), nullable=False)
    training_end_date = Column(String(10), nullable=False)
    feature_set = Column(Text, nullable=False)  # JSON serialized list of features
    wape = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    bias = Column(Float, nullable=False)
    status = Column(String(20), default="challenger", nullable=False)  # champion, challenger, archived, rejected
    is_active = Column(Integer, default=0, nullable=False)
    artifacts_path = Column(String(255), nullable=True)
    trained_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
    promoted_at = Column(String(30), nullable=True)
    promotion_notes = Column(Text, nullable=True)
    mess_id = Column(String(50), default="default_mess", nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "version": self.version,
            "model_type": self.model_type,
            "training_start_date": self.training_start_date,
            "training_end_date": self.training_end_date,
            "feature_set": self.feature_set,
            "wape": self.wape,
            "mae": self.mae,
            "bias": self.bias,
            "status": self.status,
            "is_active": self.is_active,
            "artifacts_path": self.artifacts_path,
            "trained_at": self.trained_at,
            "promoted_at": self.promoted_at,
            "promotion_notes": self.promotion_notes,
            "mess_id": self.mess_id,
        }


class Recipe(Base):
    """Recipes table: link dishes to ingredients and yield specifications (B9, B10)."""

    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), unique=True, nullable=False, index=True)
    servings_yield = Column(Float, default=100.0, nullable=False)
    instructions = Column(Text, nullable=True)
    version = Column(String(20), default="v1.0", nullable=False)
    mess_id = Column(String(50), default="default_mess", nullable=False, index=True)
    created_at = Column(
        String(30),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )

    dish = relationship("Dish")
    ingredients = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dish_id": self.dish_id,
            "dish_name": self.dish.name if self.dish else None,
            "servings_yield": self.servings_yield,
            "instructions": self.instructions,
            "version": self.version,
            "mess_id": self.mess_id,
            "created_at": self.created_at,
            "ingredients": [i.to_dict() for i in self.ingredients],
        }


class RecipeIngredient(Base):
    """Recipe ingredients breakdown and manager-configured costs (B9, B10)."""

    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, index=True)
    ingredient_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)  # amount for recipe.servings_yield
    unit = Column(String(20), default="kg", nullable=False)
    cost_per_unit = Column(Float, nullable=True)  # INR per unit
    cost_source = Column(String(50), default="configured", nullable=False)
    mess_id = Column(String(50), default="default_mess", nullable=False, index=True)

    recipe = relationship("Recipe", back_populates="ingredients")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "ingredient_name": self.ingredient_name,
            "amount": self.amount,
            "unit": self.unit,
            "cost_per_unit": self.cost_per_unit,
            "cost_source": self.cost_source,
            "mess_id": self.mess_id,
        }


# Database Engine and Session Factory Management
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "messwise.db"


def get_default_db_url() -> str:
    """Resolve database URL from environment or fallback to local SQLite."""
    custom_path = os.getenv("MESSWISE_DB_PATH")
    if custom_path:
        return f"sqlite:///{custom_path}"
    _DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{_DEFAULT_DB_PATH}"


def get_engine(db_url: Optional[str] = None) -> Engine:
    """Create or return a SQLAlchemy engine."""
    url = db_url or get_default_db_url()
    return create_engine(
        url,
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
        echo=False,
    )


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker[Session]:
    """Return a sessionmaker bound to the given or default engine."""
    eng = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)


def migrate_db(engine: Engine) -> None:
    """Idempotently add new columns to SQLite tables if they do not already exist, and create new tables."""
    try:
        with engine.connect() as conn:
            # 1. Meals table
            cursor_m = conn.execute(text("PRAGMA table_info(meals)"))
            meal_cols = {row[1] for row in cursor_m.fetchall()}
            if meal_cols:
                if "verification_status" not in meal_cols:
                    conn.execute(text("ALTER TABLE meals ADD COLUMN verification_status VARCHAR(30) DEFAULT 'unverified_test'"))
                if "mess_id" not in meal_cols:
                    conn.execute(text("ALTER TABLE meals ADD COLUMN mess_id VARCHAR(50) DEFAULT 'default_mess'"))
                conn.execute(text("UPDATE meals SET verification_status = 'synthetic' WHERE is_synthetic = 1 AND (verification_status IS NULL OR verification_status = 'unverified_test')"))
                conn.execute(text("UPDATE meals SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            # 2. Dish_log table
            cursor_dl = conn.execute(text("PRAGMA table_info(dish_log)"))
            dl_cols = {row[1] for row in cursor_dl.fetchall()}
            if dl_cols:
                if "verification_status" not in dl_cols:
                    conn.execute(text("ALTER TABLE dish_log ADD COLUMN verification_status VARCHAR(30) DEFAULT 'unverified_test'"))
                if "mess_id" not in dl_cols:
                    conn.execute(text("ALTER TABLE dish_log ADD COLUMN mess_id VARCHAR(50) DEFAULT 'default_mess'"))
                conn.execute(text("UPDATE dish_log SET verification_status = 'synthetic' WHERE is_synthetic = 1 AND (verification_status IS NULL OR verification_status = 'unverified_test')"))
                conn.execute(text("UPDATE dish_log SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            # 3. Dishes table
            cursor_dishes = conn.execute(text("PRAGMA table_info(dishes)"))
            dish_cols = {row[1] for row in cursor_dishes.fetchall()}
            if dish_cols:
                for col_name, col_type in [
                    ("batch_size", "REAL"),
                    ("shortage_cost_cu", "REAL"),
                    ("waste_cost_co", "REAL"),
                    ("cost_ratio_k", "REAL"),
                    ("mess_id", "VARCHAR(50) DEFAULT 'default_mess'"),
                ]:
                    if col_name not in dish_cols:
                        conn.execute(text(f"ALTER TABLE dishes ADD COLUMN {col_name} {col_type}"))
                conn.execute(text("UPDATE dishes SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            # 4. Predictions table
            cursor_p = conn.execute(text("PRAGMA table_info(predictions)"))
            pred_cols = {row[1] for row in cursor_p.fetchall()}
            if pred_cols:
                for col_name, col_type in [
                    ("baseline_last_week", "REAL"),
                    ("baseline_trailing_avg", "REAL"),
                    ("forecast_error", "REAL"),
                    ("abs_error", "REAL"),
                    ("status", "VARCHAR(20) DEFAULT 'pending'"),
                    ("explanation", "TEXT"),
                    ("context_json", "TEXT"),
                    ("mess_id", "VARCHAR(50) DEFAULT 'default_mess'"),
                ]:
                    if col_name not in pred_cols:
                        conn.execute(text(f"ALTER TABLE predictions ADD COLUMN {col_name} {col_type}"))
                conn.execute(text("UPDATE predictions SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            # 5. Overrides table
            cursor_ov = conn.execute(text("PRAGMA table_info(overrides)"))
            ov_cols = {row[1] for row in cursor_ov.fetchall()}
            if ov_cols:
                if "mess_id" not in ov_cols:
                    conn.execute(text("ALTER TABLE overrides ADD COLUMN mess_id VARCHAR(50) DEFAULT 'default_mess'"))
                conn.execute(text("UPDATE overrides SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            # 6. Audit log table
            cursor_al = conn.execute(text("PRAGMA table_info(audit_log)"))
            al_cols = {row[1] for row in cursor_al.fetchall()}
            if al_cols:
                if "mess_id" not in al_cols:
                    conn.execute(text("ALTER TABLE audit_log ADD COLUMN mess_id VARCHAR(50) DEFAULT 'default_mess'"))
                conn.execute(text("UPDATE audit_log SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            # 7. Surplus events table
            cursor_surplus = conn.execute(text("PRAGMA table_info(surplus_events)"))
            surplus_cols = {row[1] for row in cursor_surplus.fetchall()}
            if surplus_cols:
                for col_name, col_type in [
                    ("uncertainty_range", "VARCHAR(100)"),
                    ("cooking_completed_at", "VARCHAR(35)"),
                    ("hold_type", "VARCHAR(20) DEFAULT 'hot'"),
                    ("safe_window_hours", "REAL DEFAULT 4.0"),
                    ("safe_cutoff_at", "VARCHAR(35)"),
                    ("current_temp_c", "REAL"),
                    ("temp_recorded_at", "VARCHAR(35)"),
                    ("temp_log_json", "TEXT"),
                    ("suspected_contamination", "INTEGER DEFAULT 0"),
                    ("eligibility_status", "VARCHAR(50) DEFAULT 'pending_inspection'"),
                    ("blocking_reason", "TEXT"),
                    ("policy_version", "VARCHAR(50) DEFAULT 'FSSAI-2019-Reg4-Sched2'"),
                    ("manager_status", "VARCHAR(20) DEFAULT 'pending'"),
                    ("manager_who", "VARCHAR(100)"),
                    ("manager_reason", "TEXT"),
                    ("manager_action_at", "VARCHAR(35)"),
                    ("partner_name", "VARCHAR(100)"),
                    ("partner_phone", "VARCHAR(50)"),
                    ("communication_draft", "TEXT"),
                    ("is_synthetic", "INTEGER DEFAULT 0"),
                    ("mess_id", "VARCHAR(50) DEFAULT 'default_mess'"),
                ]:
                    if col_name not in surplus_cols:
                        conn.execute(text(f"ALTER TABLE surplus_events ADD COLUMN {col_name} {col_type}"))
                conn.execute(text("UPDATE surplus_events SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            # 8. Entrance tallies table
            cursor_et = conn.execute(text("PRAGMA table_info(entrance_tallies)"))
            et_cols = {row[1] for row in cursor_et.fetchall()}
            if et_cols:
                if "mess_id" not in et_cols:
                    conn.execute(text("ALTER TABLE entrance_tallies ADD COLUMN mess_id VARCHAR(50) DEFAULT 'default_mess'"))
                conn.execute(text("UPDATE entrance_tallies SET mess_id = 'default_mess' WHERE mess_id IS NULL"))

            conn.commit()
    except Exception:
        pass

    # Ensure all new ORM models have their tables created idempotently
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass


def init_db(engine: Optional[Engine] = None) -> None:
    """Initialize database schema, creating all tables if not present, and applying migrations."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    migrate_db(eng)


def get_db(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Dependency helper yielding an active SQLAlchemy session."""
    session_factory = get_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# High-level Data Operations
def log_audit(
    session: Session,
    who: str,
    action: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
) -> AuditLog:
    """Add an entry to the audit log."""
    entry = AuditLog(
        who=who,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )
    session.add(entry)
    return entry


def get_or_create_dish(
    session: Session,
    name: str,
    unit: str = "kg",
    category: str = "main",
    criticality_tier: str = "main",
    prep_loss_pct: float = 0.0,
    batch_size: Optional[float] = None,
    standard_portion: Optional[float] = None,
    is_synthetic: int = 0,
) -> Dish:
    """Fetch an existing dish by name or register a new one."""
    clean_name = name.strip()
    norm_unit = normalize_unit(unit)
    eff_crit = criticality_tier
    if eff_crit == "main" and category.strip().lower() in ("staple", "side"):
        eff_crit = category.strip().lower()

    dish = session.execute(select(Dish).where(Dish.name == clean_name)).scalar_one_or_none()
    if dish:
        if batch_size is not None and dish.batch_size is None:
            dish.batch_size = batch_size
        if standard_portion is not None and dish.standard_portion is None:
            dish.standard_portion = standard_portion
        session.flush()
        return dish

    dish = Dish(
        name=clean_name,
        category=category,
        unit=norm_unit,
        criticality_tier=eff_crit,
        prep_loss_pct=prep_loss_pct,
        batch_size=batch_size,
        standard_portion=standard_portion,
        is_synthetic=is_synthetic,
    )
    session.add(dish)
    session.flush()
    log_audit(
        session,
        who="system",
        action="create_dish",
        new_value=f"id={dish.id}, name={dish.name}, unit={dish.unit}, batch_size={dish.batch_size}",
    )
    return dish


def save_meal_plan(
    session: Session,
    meal_date: str,
    meal_type: str,
    plan_dict: dict,
    service_level: float = 0.95,
    is_synthetic: int = 0,
    who: str = "manager",
) -> Optional[Prediction]:
    """Store or update plan_json in Prediction record and record an audit log entry."""
    import json
    stmt = select(Prediction).where(
        Prediction.meal_date == meal_date,
        Prediction.meal_type == meal_type,
        Prediction.is_synthetic == is_synthetic,
    ).order_by(Prediction.id.desc())
    pred = session.execute(stmt).scalars().first()
    plan_str = json.dumps(plan_dict)
    
    if pred:
        old_val = pred.plan_json
        pred.plan_json = plan_str
        pred.service_level = service_level
    else:
        # Create a prediction record if one did not exist
        h_hat = plan_dict.get("forecast_h_hat", plan_dict.get("planning_headcount", 0))
        pred = Prediction(
            meal_date=meal_date,
            meal_type=meal_type,
            model_version="v0.1.0-planner",
            h_hat=float(h_hat),
            h_lo=float(plan_dict.get("h_lo", h_hat * 0.9)),
            h_hi=float(plan_dict.get("h_hi", h_hat * 1.1)),
            service_level=service_level,
            plan_json=plan_str,
            status="pending",
            explanation=plan_dict.get("summary_explanation", "Saved cooking plan"),
            is_synthetic=is_synthetic,
        )
        session.add(pred)
        old_val = None

    session.flush()
    log_audit(
        session,
        who=who,
        action="save_meal_plan",
        old_value=old_val[:100] if old_val else None,
        new_value=f"meal={meal_date} {meal_type}, service_level={service_level}, dishes={len(plan_dict.get('dishes', []))}",
    )
    session.commit()
    return pred


def link_actual_to_predictions(session: Session, meal: Meal) -> int:
    """Associate a newly logged meal with any unlinked prior predictions for that slot."""
    stmt = select(Prediction).where(
        Prediction.meal_date == meal.date,
        Prediction.meal_type == meal.meal_type,
        Prediction.is_synthetic == meal.is_synthetic,
        Prediction.status == "pending",
    )
    predictions = session.execute(stmt).scalars().all()
    updated_count = 0
    for pred in predictions:
        pred.actual_headcount = meal.headcount
        pred.forecast_error = float(meal.headcount - pred.h_hat)
        pred.abs_error = float(abs(meal.headcount - pred.h_hat))
        pred.status = "evaluated"
        updated_count += 1
    if updated_count > 0:
        session.flush()
    return updated_count


def create_meal_record(session: Session, meal_data: MealCreate) -> Meal:
    """Create and persist a validated meal record, linking to prior predictions."""
    v_status = getattr(meal_data, "verification_status", "unverified_test")
    if meal_data.is_synthetic == 1:
        v_status = "synthetic"
    m_id = getattr(meal_data, "mess_id", "default_mess")

    meal = Meal(
        date=meal_data.date,
        meal_type=normalize_meal_type(meal_data.meal_type),
        headcount=meal_data.headcount,
        hostel_strength=meal_data.hostel_strength,
        event_flag=meal_data.event_flag,
        exam_flag=meal_data.exam_flag,
        holiday_flag=meal_data.holiday_flag,
        temp_c=meal_data.temp_c,
        rain_mm=meal_data.rain_mm,
        source=meal_data.source,
        is_synthetic=meal_data.is_synthetic,
        verification_status=v_status,
        mess_id=m_id,
    )
    session.add(meal)
    session.flush()

    # Link with earlier prediction log records if any exist (E1 Prediction Log requirement)
    linked = link_actual_to_predictions(session=session, meal=meal)

    log_audit(
        session,
        who="user",
        action="create_meal",
        new_value=f"meal_id={meal.id}, date={meal.date}, type={meal.meal_type}, headcount={meal.headcount}, status={meal.verification_status}, mess={meal.mess_id}, linked_predictions={linked}",
    )
    return meal


def create_dish_log_record(session: Session, dish_log_data: DishLogCreate) -> DishLog:
    """Create and persist a validated dish log record."""
    # Verify parent meal exists
    meal = session.get(Meal, dish_log_data.meal_id)
    if not meal:
        raise ValueError(f"Parent meal with id {dish_log_data.meal_id} does not exist.")

    # Verify dish exists
    dish = session.get(Dish, dish_log_data.dish_id)
    if not dish:
        raise ValueError(f"Dish with id {dish_log_data.dish_id} does not exist.")

    v_status = getattr(dish_log_data, "verification_status", meal.verification_status)
    if dish_log_data.is_synthetic == 1:
        v_status = "synthetic"
    m_id = getattr(dish_log_data, "mess_id", meal.mess_id)

    dish_log = DishLog(
        meal_id=dish_log_data.meal_id,
        dish_id=dish_log_data.dish_id,
        cooked_qty=dish_log_data.cooked_qty,
        leftover_qty=dish_log_data.leftover_qty,
        unit=normalize_unit(dish_log_data.unit),
        ran_out=dish_log_data.ran_out,
        waste_stage=dish_log_data.waste_stage,
        reason_tag=dish_log_data.reason_tag,
        entry_method=dish_log_data.entry_method,
        photo_ref=dish_log_data.photo_ref,
        is_synthetic=dish_log_data.is_synthetic,
        verification_status=v_status,
        mess_id=m_id,
    )
    session.add(dish_log)
    session.flush()
    log_audit(
        session,
        who="kitchen",
        action="create_dish_log",
        new_value=f"dish_log_id={dish_log.id}, meal_id={dish_log.meal_id}, cooked={dish_log.cooked_qty}, leftover={dish_log.leftover_qty}, status={dish_log.verification_status}, mess={dish_log.mess_id}",
    )
    return dish_log


def list_meals_query(
    session: Session,
    is_synthetic: Optional[int] = None,
    mess_id: Optional[str] = None,
    verification_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Meal]:
    """Retrieve meals ordered by date descending."""
    stmt = select(Meal)
    if is_synthetic is not None:
        stmt = stmt.where(Meal.is_synthetic == is_synthetic)
    if mess_id is not None:
        stmt = stmt.where(Meal.mess_id == mess_id)
    if verification_status is not None:
        stmt = stmt.where(Meal.verification_status == verification_status)
    stmt = stmt.order_by(Meal.date.desc(), Meal.id.desc()).limit(limit).offset(offset)
    return list(session.execute(stmt).scalars().all())


def get_meal_with_dishes(
    session: Session, meal_id: int
) -> Optional[Tuple[Meal, List[DishLog]]]:
    """Retrieve a meal and its associated dish logs."""
    meal = session.get(Meal, meal_id)
    if not meal:
        return None
    return meal, meal.dish_logs


def get_data_environment_summary(
    session: Optional[Session] = None,
    mess_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspect database to return accurate counts of real pilot vs synthetic demo records.

    Clearly distinguishes verified pilot measurements from unverified test entries.
    If no session is provided, automatically creates and manages a session.
    """
    if session is None:
        session_factory = get_session_factory()
        with session_factory() as s:
            return get_data_environment_summary(session=s, mess_id=mess_id)

    # Meal counts
    meal_filter = []
    dish_log_filter = []
    dish_filter = []
    if mess_id is not None:
        meal_filter.append(Meal.mess_id == mess_id)
        dish_log_filter.append(DishLog.mess_id == mess_id)
        dish_filter.append(Dish.mess_id == mess_id)

    real_meals = session.execute(
        select(func.count(Meal.id)).where(Meal.is_synthetic == 0, *meal_filter)
    ).scalar() or 0
    verified_meals = session.execute(
        select(func.count(Meal.id)).where(Meal.is_synthetic == 0, Meal.verification_status == "verified_pilot", *meal_filter)
    ).scalar() or 0
    unverified_meals = session.execute(
        select(func.count(Meal.id)).where(Meal.is_synthetic == 0, Meal.verification_status != "verified_pilot", *meal_filter)
    ).scalar() or 0
    synth_meals = session.execute(
        select(func.count(Meal.id)).where(Meal.is_synthetic == 1, *meal_filter)
    ).scalar() or 0

    real_dish_logs = session.execute(
        select(func.count(DishLog.id)).where(DishLog.is_synthetic == 0, *dish_log_filter)
    ).scalar() or 0
    verified_dish_logs = session.execute(
        select(func.count(DishLog.id)).where(DishLog.is_synthetic == 0, DishLog.verification_status == "verified_pilot", *dish_log_filter)
    ).scalar() or 0
    unverified_dish_logs = session.execute(
        select(func.count(DishLog.id)).where(DishLog.is_synthetic == 0, DishLog.verification_status != "verified_pilot", *dish_log_filter)
    ).scalar() or 0
    synth_dish_logs = session.execute(
        select(func.count(DishLog.id)).where(DishLog.is_synthetic == 1, *dish_log_filter)
    ).scalar() or 0

    real_dishes = session.execute(
        select(func.count(Dish.id)).where(Dish.is_synthetic == 0, *dish_filter)
    ).scalar() or 0
    synth_dishes = session.execute(
        select(func.count(Dish.id)).where(Dish.is_synthetic == 1, *dish_filter)
    ).scalar() or 0
    total_dishes = session.execute(
        select(func.count(Dish.id)).where(*dish_filter)
    ).scalar() or 0

    return {
        "real_meals_count": int(real_meals),
        "verified_pilot_meals_count": int(verified_meals),
        "unverified_test_meals_count": int(unverified_meals),
        "synthetic_meals_count": int(synth_meals),
        "total_meals_count": int(real_meals + synth_meals),
        "real_dish_logs_count": int(real_dish_logs),
        "verified_pilot_dish_logs_count": int(verified_dish_logs),
        "unverified_test_dish_logs_count": int(unverified_dish_logs),
        "synthetic_dish_logs_count": int(synth_dish_logs),
        "total_dish_logs_count": int(real_dish_logs + synth_dish_logs),
        "real_dishes_count": int(real_dishes),
        "synthetic_dishes_count": int(synth_dishes),
        "registered_dishes_count": int(total_dishes),
        "dishes_count": int(total_dishes),
        "has_real_data": bool(real_meals > 0),
        "has_verified_pilot_data": bool(verified_meals > 0),
        "is_verified_pilot": bool(verified_meals > 0),
        "real_env_label": (
            f"🟢 Verified Pilot Data ({verified_meals} verified operational meals)"
            if verified_meals > 0
            else f"🟡 Unverified Test Entries ({unverified_meals} manual test entries — Non-Pilot)"
        ),
        "real_env_badge": (
            f"● Active Environment: Verified Pilot Data ({verified_meals} records)"
            if verified_meals > 0
            else f"▲ Active Environment: Unverified Test Data ({unverified_meals} records — Non-Pilot)"
        ),
        "real_env_badge_class": "badge-real" if verified_meals > 0 else "badge-unverified",
        "has_synthetic_data": bool(synth_meals > 0),
        "active_mess_id": mess_id or "default_mess",
    }


def record_entrance_tally(
    session: Session,
    meal_id: int,
    time_bucket: str,
    headcount_count: int,
    recorded_by: str = "staff",
    is_synthetic: int = 0,
) -> EntranceTally:
    """Record an aggregate, privacy-preserving entrance check-in count for a 15-minute bucket (C7)."""
    if headcount_count < 0:
        raise ValueError(f"Headcount count must be non-negative (got {headcount_count}).")

    tally = EntranceTally(
        meal_id=meal_id,
        time_bucket=time_bucket.strip(),
        headcount_count=headcount_count,
        recorded_by=recorded_by.strip() or "staff",
        is_synthetic=is_synthetic,
    )
    session.add(tally)
    session.commit()
    session.refresh(tally)
    return tally


def get_meal_tallies(session: Session, meal_id: int) -> List[EntranceTally]:
    """Retrieve all timestamped entrance tally buckets for a meal in time order."""
    stmt = (
        select(EntranceTally)
        .where(EntranceTally.meal_id == meal_id)
        .order_by(EntranceTally.time_bucket.asc(), EntranceTally.id.asc())
    )
    return list(session.execute(stmt).scalars().all())


# A7 Campus Calendar Operations
def add_campus_event(
    session: Session,
    event_name: str,
    event_type: str,
    start_date: str,
    end_date: str,
    expected_attendance_factor: float = 1.0,
    notes: Optional[str] = None,
    mess_id: str = "default_mess",
) -> CampusEvent:
    """Register an academic or campus event affecting headcount expectations (A7)."""
    event = CampusEvent(
        event_name=event_name.strip(),
        event_type=event_type.strip().lower(),
        start_date=start_date.strip(),
        end_date=end_date.strip(),
        expected_attendance_factor=float(expected_attendance_factor),
        notes=notes.strip() if notes else None,
        mess_id=mess_id.strip() or "default_mess",
    )
    session.add(event)
    session.flush()
    log_audit(
        session,
        who="system",
        action="add_campus_event",
        new_value=f"event_id={event.id}, name={event.event_name}, type={event.event_type}, dates={event.start_date}..{event.end_date}, factor={event.expected_attendance_factor}",
    )
    session.commit()
    return event


def list_campus_events(
    session: Session,
    target_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mess_id: str = "default_mess",
) -> List[CampusEvent]:
    """Retrieve campus events applicable on a specific date or date window."""
    stmt = select(CampusEvent).where(CampusEvent.mess_id == mess_id)
    if target_date:
        stmt = stmt.where(
            CampusEvent.start_date <= target_date,
            CampusEvent.end_date >= target_date,
        )
    elif start_date and end_date:
        stmt = stmt.where(
            CampusEvent.start_date <= end_date,
            CampusEvent.end_date >= start_date,
        )
    stmt = stmt.order_by(CampusEvent.start_date.asc())
    return list(session.execute(stmt).scalars().all())


# A9 & F1 Student Anonymous Meal Check-in Operations
def record_meal_checkin(
    session: Session,
    meal_date: str,
    meal_type: str,
    response: str,
    device_hash: Optional[str] = None,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
) -> MealCheckIn:
    """Record an anonymous, aggregate-only student meal check-in response (A9, F1)."""
    resp_clean = response.strip().lower()
    if resp_clean not in ("yes", "no", "maybe"):
        raise ValueError(f"Invalid check-in response '{response}'. Must be 'yes', 'no', or 'maybe'.")

    # Duplicate suppression if device_hash provided: update existing response for this meal
    if device_hash:
        existing = session.execute(
            select(MealCheckIn).where(
                MealCheckIn.meal_date == meal_date,
                MealCheckIn.meal_type == meal_type,
                MealCheckIn.device_hash == device_hash,
                MealCheckIn.mess_id == mess_id,
            )
        ).scalar_one_or_none()
        if existing:
            existing.response = resp_clean
            session.commit()
            return existing

    checkin = MealCheckIn(
        meal_date=meal_date,
        meal_type=normalize_meal_type(meal_type),
        response=resp_clean,
        device_hash=device_hash,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
    )
    session.add(checkin)
    session.commit()
    return checkin


def get_meal_checkins_summary(
    session: Session,
    meal_date: str,
    meal_type: str,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
) -> Dict[str, Any]:
    """Retrieve aggregate anonymous student check-in turnout signal for a meal."""
    m_type = normalize_meal_type(meal_type)
    stmt = select(MealCheckIn).where(
        MealCheckIn.meal_date == meal_date,
        MealCheckIn.meal_type == m_type,
        MealCheckIn.mess_id == mess_id,
        MealCheckIn.is_synthetic == is_synthetic,
    )
    records = session.execute(stmt).scalars().all()
    yes_count = sum(1 for r in records if r.response == "yes")
    no_count = sum(1 for r in records if r.response == "no")
    maybe_count = sum(1 for r in records if r.response == "maybe")
    total = len(records)

    return {
        "meal_date": meal_date,
        "meal_type": m_type,
        "mess_id": mess_id,
        "yes_count": yes_count,
        "no_count": no_count,
        "maybe_count": maybe_count,
        "total_responses": total,
        "projected_attendance_signal": float(yes_count + 0.5 * maybe_count) if total > 0 else None,
        "has_signal": bool(total >= 5),  # threshold for statistical relevance
    }


# A8 & F2 Anonymous Dish Rating Operations
def record_meal_rating(
    session: Session,
    meal_date: str,
    meal_type: str,
    dish_id: int,
    rating: int,
    comment: Optional[str] = None,
    device_hash: Optional[str] = None,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
) -> MealRating:
    """Record an anonymous dish rating between 1 and 5 (A8, F2)."""
    if rating < 1 or rating > 5:
        raise ValueError(f"Rating must be between 1 and 5 (got {rating}).")
    
    # Check duplicate rating by device_hash for this dish on this date/meal
    if device_hash:
        existing = session.execute(
            select(MealRating).where(
                MealRating.meal_date == meal_date,
                MealRating.meal_type == meal_type,
                MealRating.dish_id == dish_id,
                MealRating.device_hash == device_hash,
                MealRating.mess_id == mess_id,
            )
        ).scalar_one_or_none()
        if existing:
            existing.rating = rating
            existing.comment = comment[:255] if comment else None
            session.commit()
            return existing

    meal_rating = MealRating(
        meal_date=meal_date,
        meal_type=normalize_meal_type(meal_type),
        dish_id=dish_id,
        rating=rating,
        comment=comment[:255] if comment else None,
        device_hash=device_hash,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
    )
    session.add(meal_rating)
    session.commit()
    return meal_rating


def get_dish_ratings_summary(
    session: Session,
    dish_id: int,
    cutoff_date: Optional[str] = None,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
) -> Dict[str, Any]:
    """Calculate historical rating summary for a dish strictly before cutoff_date (A8 leak prevention)."""
    stmt = select(MealRating).where(
        MealRating.dish_id == dish_id,
        MealRating.mess_id == mess_id,
        MealRating.is_synthetic == is_synthetic,
    )
    if cutoff_date:
        stmt = stmt.where(MealRating.meal_date < cutoff_date)

    ratings = session.execute(stmt).scalars().all()
    count = len(ratings)
    if count == 0:
        return {
            "dish_id": dish_id,
            "ratings_count": 0,
            "average_rating": None,
            "popularity_tier": "insufficient_data",
            "popularity_multiplier": 1.0,
            "has_popularity_data": False,
        }

    avg_score = sum(r.rating for r in ratings) / count
    # Multiplier: 3.0 is neutral (1.0). 5.0 is +10% lift (1.10). 1.0 is -10% drop (0.90).
    multiplier = round(1.0 + (avg_score - 3.0) * 0.05, 3)

    return {
        "dish_id": dish_id,
        "ratings_count": count,
        "average_rating": round(avg_score, 2),
        "popularity_tier": "high" if avg_score >= 4.0 else ("low" if avg_score < 2.5 else "neutral"),
        "popularity_multiplier": multiplier,
        "has_popularity_data": bool(count >= 3),
    }


# B9 & B10 Recipe & Procurement Operations
def save_recipe(
    session: Session,
    dish_id: int,
    servings_yield: float = 100.0,
    ingredients_list: Optional[List[Dict[str, Any]]] = None,
    instructions: Optional[str] = None,
    version: str = "v1.0",
    mess_id: str = "default_mess",
) -> Recipe:
    """Register or update a manager-configured recipe for ingredient-level procurement (B9, B10)."""
    dish = session.get(Dish, dish_id)
    if not dish:
        raise ValueError(f"Dish with id {dish_id} does not exist.")

    recipe = session.execute(
        select(Recipe).where(Recipe.dish_id == dish_id, Recipe.mess_id == mess_id)
    ).scalar_one_or_none()

    if recipe:
        recipe.servings_yield = servings_yield
        recipe.instructions = instructions
        recipe.version = version
        # Remove old ingredients and re-add
        for ing in list(recipe.ingredients):
            session.delete(ing)
        session.flush()
    else:
        recipe = Recipe(
            dish_id=dish_id,
            servings_yield=servings_yield,
            instructions=instructions,
            version=version,
            mess_id=mess_id,
        )
        session.add(recipe)
        session.flush()

    if ingredients_list:
        for item in ingredients_list:
            ing = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_name=item["ingredient_name"].strip(),
                amount=float(item["amount"]),
                unit=normalize_unit(item.get("unit", "kg")),
                cost_per_unit=float(item["cost_per_unit"]) if item.get("cost_per_unit") is not None else None,
                cost_source=item.get("cost_source", "configured"),
                mess_id=mess_id,
            )
            session.add(ing)

    session.flush()
    log_audit(
        session,
        who="manager",
        action="save_recipe",
        new_value=f"dish_id={dish_id}, yield={servings_yield}, ingredients={len(ingredients_list or [])}",
    )
    session.commit()
    return recipe


def get_recipe_for_dish(
    session: Session,
    dish_id: int,
    mess_id: str = "default_mess",
) -> Optional[Recipe]:
    """Retrieve configured recipe for a dish."""
    stmt = select(Recipe).where(Recipe.dish_id == dish_id, Recipe.mess_id == mess_id)
    return session.execute(stmt).scalar_one_or_none()


# A11 Model Registry & Controlled Retraining Operations
def log_model_version(
    session: Session,
    version: str,
    model_type: str,
    training_start_date: str,
    training_end_date: str,
    feature_set: List[str],
    wape: float,
    mae: float,
    bias: float,
    status: str = "challenger",
    artifacts_path: Optional[str] = None,
    mess_id: str = "default_mess",
) -> ModelRegistry:
    """Record a newly evaluated model version in the registry (A11)."""
    import json
    model_entry = ModelRegistry(
        version=version.strip(),
        model_type=model_type.strip(),
        training_start_date=training_start_date,
        training_end_date=training_end_date,
        feature_set=json.dumps(feature_set),
        wape=float(wape),
        mae=float(mae),
        bias=float(bias),
        status=status,
        is_active=1 if status == "champion" else 0,
        artifacts_path=artifacts_path,
        mess_id=mess_id,
    )
    session.add(model_entry)
    session.flush()
    log_audit(
        session,
        who="ml_pipeline",
        action="log_model_version",
        new_value=f"version={version}, type={model_type}, wape={wape:.4f}, mae={mae:.2f}, status={status}",
    )
    session.commit()
    return model_entry


def get_active_model(
    session: Session,
    mess_id: str = "default_mess",
) -> Optional[ModelRegistry]:
    """Retrieve current champion model for active serving."""
    stmt = select(ModelRegistry).where(
        ModelRegistry.mess_id == mess_id,
        ModelRegistry.is_active == 1,
    ).order_by(ModelRegistry.id.desc())
    return session.execute(stmt).scalars().first()


def promote_model_version(
    session: Session,
    version: str,
    promotion_notes: str,
    mess_id: str = "default_mess",
) -> bool:
    """Promote challenger model to champion if validation gates pass (A11)."""
    target = session.execute(
        select(ModelRegistry).where(
            ModelRegistry.version == version,
            ModelRegistry.mess_id == mess_id,
        )
    ).scalar_one_or_none()
    if not target:
        return False

    # Demote existing champion
    current_champ = session.execute(
        select(ModelRegistry).where(
            ModelRegistry.mess_id == mess_id,
            ModelRegistry.is_active == 1,
        )
    ).scalars().all()
    for c in current_champ:
        c.is_active = 0
        c.status = "archived"

    target.is_active = 1
    target.status = "champion"
    target.promoted_at = datetime.now(timezone.utc).isoformat()
    target.promotion_notes = promotion_notes.strip()

    log_audit(
        session,
        who="model_governance",
        action="promote_model",
        new_value=f"promoted_version={version}, notes={promotion_notes}",
    )
    session.commit()
    return True


def list_model_versions(
    session: Session,
    mess_id: str = "default_mess",
) -> List[ModelRegistry]:
    """Retrieve model registry audit history."""
    stmt = select(ModelRegistry).where(ModelRegistry.mess_id == mess_id).order_by(ModelRegistry.id.desc())
    return list(session.execute(stmt).scalars().all())


