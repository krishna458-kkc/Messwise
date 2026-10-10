"""MessWise Food-Safe Surplus Routing & Safety Clock Engine (Module G: G1 & G2).

Implements specifications from PLAN.md Section 5 (Module G), Appendix B, and Appendix F:
- G1: Predicted-Surplus Alert: Computes potential surplus from quantity plan predictions
      and kitchen measurements. Deduplicated, unit-aware alert states.
      Strict distinction between Predicted Surplus (pre-service estimate) and
      Measured Surplus (post-service kitchen weigh-in).
- G2: Food-Safety Clock: Time and temperature observation tracking and compliance engine.
      Enforces holding-time thresholds and safety gates aligned with authoritative
      Food Safety and Standards (Recovery and Distribution of Surplus Food) Regulations, 2019 (FSSAI).

Core Food-Safety Rules:
- NEVER recommend re-serving cooked leftovers in the mess.
- NEVER declare food safe merely because a timer has not expired.
- Block donation proposals when the safe window has expired, temperature is invalid or in danger zone,
  food history is uncertain, or eligibility is unconfirmed.
- Strict server-side gate enforcement in Python logic and FastAPI endpoints.
- In-app alerts as required MVP channel; pre-filled WhatsApp click-to-chat draft only after
  manager approval and verified safety. No automatic message sending or physical food transfer.
- Strict synthetic vs. real data isolation (is_synthetic=1 vs 0), displaying prominent labels:
  "Synthetic Demonstration — Not a Real Food Donation".
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import quote
from zoneinfo import ZoneInfo

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from messwise.db import (
    AuditLog,
    Dish,
    DishLog,
    Meal,
    SurplusEvent,
    get_or_create_dish,
    log_audit,
)
from messwise.planner import generate_meal_plan
from messwise.validation import normalize_meal_type, normalize_unit

# Authoritative FSSAI Regulatory Reference & Operational Standards
# Source: Food Safety and Standards (Recovery and Distribution of Surplus Food) Regulations, 2019
# Published under the Food Safety and Standards Act, 2006 (FSSAI)
FSSAI_POLICY_NAME: str = (
    "Food Safety and Standards (Recovery and Distribution of Surplus Food) Regulations, 2019"
)
FSSAI_POLICY_VERSION: str = "FSSAI-2019-Reg4-Sched2"

# Safe Temperature & Holding Limits (FSSAI 2019 / Schedule II)
FSSAI_HOT_HOLD_MIN_TEMP_C: float = 65.0   # Hot holding must be kept at or above 65°C
FSSAI_COLD_HOLD_MAX_TEMP_C: float = 5.0   # Cold holding must be kept at or below 5°C
FSSAI_HOT_HOLD_MAX_HOURS: float = 4.0     # Maximum safe window from cooking completion for hot-held food
FSSAI_AMBIENT_MAX_HOURS: float = 2.0      # Maximum safe window for ambient / unheated holding
FSSAI_COLD_HOLD_MAX_HOURS: float = 24.0   # Maximum safe window under continuous refrigeration (<= 5°C)

# Temperature Danger Zone
DANGER_ZONE_MIN_C: float = 5.0
DANGER_ZONE_MAX_C: float = 65.0

# Application Timezone (IST: Asia/Kolkata, UTC+05:30)
APP_TIMEZONE: ZoneInfo = ZoneInfo("Asia/Kolkata")


def parse_iso_dt(dt_str: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """Parse an ISO string or datetime into a timezone-aware datetime in APP_TIMEZONE."""
    if dt_str is None:
        return None
    if isinstance(dt_str, datetime):
        if dt_str.tzinfo is None:
            return dt_str.replace(tzinfo=APP_TIMEZONE)
        return dt_str.astimezone(APP_TIMEZONE)
    
    clean_str = dt_str.strip()
    if not clean_str:
        return None
    # Normalize trailing Z to UTC offset
    if clean_str.endswith("Z"):
        clean_str = clean_str[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=APP_TIMEZONE)
        return dt.astimezone(APP_TIMEZONE)
    except Exception:
        return None


def now_iso(as_of: Optional[Union[str, datetime]] = None) -> str:
    """Return an ISO 8601 string in APP_TIMEZONE for the given or current timestamp."""
    if as_of is not None:
        parsed = parse_iso_dt(as_of)
        if parsed:
            return parsed.isoformat()
    return datetime.now(APP_TIMEZONE).isoformat()


@dataclass
class SafetyClockResult:
    """Deterministic evaluation result of the G2 Food-Safety Clock."""

    as_of_time: str
    cooking_completed_at: Optional[str]
    safe_cutoff_at: Optional[str]
    hold_type: str
    safe_window_hours: float
    elapsed_seconds: Optional[float]
    elapsed_hours: Optional[float]
    remaining_seconds: Optional[float]
    remaining_hours: Optional[float]
    is_expired: bool
    is_temperature_safe: bool
    eligibility_status: str  # eligible | pending_inspection | blocked_expired | blocked_temperature | blocked_missing_data | blocked_contamination | dismissed
    blocking_reason: Optional[str]
    policy_citation: str
    observations_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_food_safety_clock(
    cooking_completed_at: Optional[str],
    hold_type: str = "hot",
    observations: Optional[List[Dict[str, Any]]] = None,
    suspected_contamination: bool = False,
    as_of_time: Optional[Union[str, datetime]] = None,
    policy_version: str = FSSAI_POLICY_VERSION,
) -> SafetyClockResult:
    """Evaluate elapsed time, remaining safe window, and temperature compliance.

    Deterministic logic used by Streamlit, FastAPI, and test suites.
    """
    curr_dt = parse_iso_dt(as_of_time) or datetime.now(APP_TIMEZONE)
    curr_iso = curr_dt.isoformat()
    obs_list = observations or []
    norm_hold = hold_type.lower().strip() if hold_type else "hot"
    if norm_hold not in ("hot", "ambient", "cold"):
        norm_hold = "hot"

    # Citation
    citation = f"{FSSAI_POLICY_NAME} ({policy_version})"

    # 1. Contamination check
    if suspected_contamination:
        return SafetyClockResult(
            as_of_time=curr_iso,
            cooking_completed_at=cooking_completed_at,
            safe_cutoff_at=None,
            hold_type=norm_hold,
            safe_window_hours=0.0,
            elapsed_seconds=None,
            elapsed_hours=None,
            remaining_seconds=0.0,
            remaining_hours=0.0,
            is_expired=True,
            is_temperature_safe=False,
            eligibility_status="blocked_contamination",
            blocking_reason=(
                "Suspected contamination or spoilage flagged. FSSAI 2019 regulations "
                "strictly prohibit recovery and donation of questionable food."
            ),
            policy_citation=citation,
            observations_count=len(obs_list),
        )

    # 2. Cooking / holding start timestamp validation
    if not cooking_completed_at:
        return SafetyClockResult(
            as_of_time=curr_iso,
            cooking_completed_at=None,
            safe_cutoff_at=None,
            hold_type=norm_hold,
            safe_window_hours=FSSAI_HOT_HOLD_MAX_HOURS if norm_hold == "hot" else FSSAI_AMBIENT_MAX_HOURS,
            elapsed_seconds=None,
            elapsed_hours=None,
            remaining_seconds=None,
            remaining_hours=None,
            is_expired=False,
            is_temperature_safe=False,
            eligibility_status="blocked_missing_data",
            blocking_reason=(
                "Missing cooking completion / holding start timestamp. "
                "Safe holding window cannot be determined without a verified start time."
            ),
            policy_citation=citation,
            observations_count=len(obs_list),
        )

    start_dt = parse_iso_dt(cooking_completed_at)
    if start_dt is None:
        return SafetyClockResult(
            as_of_time=curr_iso,
            cooking_completed_at=cooking_completed_at,
            safe_cutoff_at=None,
            hold_type=norm_hold,
            safe_window_hours=FSSAI_HOT_HOLD_MAX_HOURS if norm_hold == "hot" else FSSAI_AMBIENT_MAX_HOURS,
            elapsed_seconds=None,
            elapsed_hours=None,
            remaining_seconds=None,
            remaining_hours=None,
            is_expired=False,
            is_temperature_safe=False,
            eligibility_status="blocked_missing_data",
            blocking_reason="Invalid cooking completion timestamp format.",
            policy_citation=citation,
            observations_count=len(obs_list),
        )

    # Determine safe window hours
    if norm_hold == "hot":
        safe_window_hours = FSSAI_HOT_HOLD_MAX_HOURS
    elif norm_hold == "cold":
        safe_window_hours = FSSAI_COLD_HOLD_MAX_HOURS
    else:  # ambient
        safe_window_hours = FSSAI_AMBIENT_MAX_HOURS

    cutoff_dt = start_dt + timedelta(hours=safe_window_hours)
    cutoff_iso = cutoff_dt.isoformat()

    elapsed_sec = (curr_dt - start_dt).total_seconds()
    remaining_sec = (cutoff_dt - curr_dt).total_seconds()
    elapsed_hr = round(elapsed_sec / 3600.0, 2)
    remaining_hr = round(remaining_sec / 3600.0, 2)

    # Check future start time
    if elapsed_sec < -60.0:  # Allow 1 min clock skew
        return SafetyClockResult(
            as_of_time=curr_iso,
            cooking_completed_at=cooking_completed_at,
            safe_cutoff_at=cutoff_iso,
            hold_type=norm_hold,
            safe_window_hours=safe_window_hours,
            elapsed_seconds=elapsed_sec,
            elapsed_hours=elapsed_hr,
            remaining_seconds=remaining_sec,
            remaining_hours=remaining_hr,
            is_expired=False,
            is_temperature_safe=False,
            eligibility_status="pending_inspection",
            blocking_reason=(
                f"Cooking completion time is in the future ({cooking_completed_at}). "
                "Service has not completed yet."
            ),
            policy_citation=citation,
            observations_count=len(obs_list),
        )

    # 3. Check safe holding window expiry
    if remaining_sec <= 0:
        return SafetyClockResult(
            as_of_time=curr_iso,
            cooking_completed_at=cooking_completed_at,
            safe_cutoff_at=cutoff_iso,
            hold_type=norm_hold,
            safe_window_hours=safe_window_hours,
            elapsed_seconds=elapsed_sec,
            elapsed_hours=elapsed_hr,
            remaining_seconds=0.0,
            remaining_hours=0.0,
            is_expired=True,
            is_temperature_safe=False,
            eligibility_status="blocked_expired",
            blocking_reason=(
                f"Safe holding window of {safe_window_hours:.1f}h expired at "
                f"{cutoff_dt.strftime('%H:%M %p')} ({elapsed_hr:.1f}h elapsed). "
                f"Donation strictly prohibited under FSSAI 2019 regulations."
            ),
            policy_citation=citation,
            observations_count=len(obs_list),
        )

    # 4. Temperature observation validation
    if not obs_list:
        return SafetyClockResult(
            as_of_time=curr_iso,
            cooking_completed_at=cooking_completed_at,
            safe_cutoff_at=cutoff_iso,
            hold_type=norm_hold,
            safe_window_hours=safe_window_hours,
            elapsed_seconds=elapsed_sec,
            elapsed_hours=elapsed_hr,
            remaining_seconds=remaining_sec,
            remaining_hours=remaining_hr,
            is_expired=False,
            is_temperature_safe=False,
            eligibility_status="pending_inspection",
            blocking_reason=(
                "Pending temperature observation. Under FSSAI 2019 Schedule II, "
                "holding temperature must be measured and verified before surplus is eligible."
            ),
            policy_citation=citation,
            observations_count=0,
        )

    # Validate observation history
    for idx, obs in enumerate(obs_list):
        t_val = obs.get("temp_c")
        if t_val is None or not isinstance(t_val, (int, float)):
            return SafetyClockResult(
                as_of_time=curr_iso,
                cooking_completed_at=cooking_completed_at,
                safe_cutoff_at=cutoff_iso,
                hold_type=norm_hold,
                safe_window_hours=safe_window_hours,
                elapsed_seconds=elapsed_sec,
                elapsed_hours=elapsed_hr,
                remaining_seconds=remaining_sec,
                remaining_hours=remaining_hr,
                is_expired=False,
                is_temperature_safe=False,
                eligibility_status="blocked_missing_data",
                blocking_reason=f"Observation #{idx+1} contains invalid or missing temperature value.",
                policy_citation=citation,
                observations_count=len(obs_list),
            )
        # Physical bounds check
        if t_val < -20.0 or t_val > 120.0:
            return SafetyClockResult(
                as_of_time=curr_iso,
                cooking_completed_at=cooking_completed_at,
                safe_cutoff_at=cutoff_iso,
                hold_type=norm_hold,
                safe_window_hours=safe_window_hours,
                elapsed_seconds=elapsed_sec,
                elapsed_hours=elapsed_hr,
                remaining_seconds=remaining_sec,
                remaining_hours=remaining_hr,
                is_expired=False,
                is_temperature_safe=False,
                eligibility_status="blocked_missing_data",
                blocking_reason=f"Observation #{idx+1} temperature {t_val}°C is outside realistic physical limits (-20°C to 120°C).",
                policy_citation=citation,
                observations_count=len(obs_list),
            )

    latest_obs = obs_list[-1]
    latest_temp = float(latest_obs["temp_c"])

    # Temperature threshold enforcement
    if norm_hold == "hot":
        if latest_temp < FSSAI_HOT_HOLD_MIN_TEMP_C:
            return SafetyClockResult(
                as_of_time=curr_iso,
                cooking_completed_at=cooking_completed_at,
                safe_cutoff_at=cutoff_iso,
                hold_type=norm_hold,
                safe_window_hours=safe_window_hours,
                elapsed_seconds=elapsed_sec,
                elapsed_hours=elapsed_hr,
                remaining_seconds=remaining_sec,
                remaining_hours=remaining_hr,
                is_expired=False,
                is_temperature_safe=False,
                eligibility_status="blocked_temperature",
                blocking_reason=(
                    f"Temperature violation: recorded {latest_temp:.1f}°C is below FSSAI hot-holding minimum "
                    f"of {FSSAI_HOT_HOLD_MIN_TEMP_C}°C. Food has entered the Danger Zone (5°C–65°C)."
                ),
                policy_citation=citation,
                observations_count=len(obs_list),
            )
    elif norm_hold == "cold":
        if latest_temp > FSSAI_COLD_HOLD_MAX_TEMP_C:
            return SafetyClockResult(
                as_of_time=curr_iso,
                cooking_completed_at=cooking_completed_at,
                safe_cutoff_at=cutoff_iso,
                hold_type=norm_hold,
                safe_window_hours=safe_window_hours,
                elapsed_seconds=elapsed_sec,
                elapsed_hours=elapsed_hr,
                remaining_seconds=remaining_sec,
                remaining_hours=remaining_hr,
                is_expired=False,
                is_temperature_safe=False,
                eligibility_status="blocked_temperature",
                blocking_reason=(
                    f"Temperature violation: recorded {latest_temp:.1f}°C exceeds FSSAI cold-holding maximum "
                    f"of {FSSAI_COLD_HOLD_MAX_TEMP_C}°C."
                ),
                policy_citation=citation,
                observations_count=len(obs_list),
            )

    # All checks passed: eligible!
    return SafetyClockResult(
        as_of_time=curr_iso,
        cooking_completed_at=cooking_completed_at,
        safe_cutoff_at=cutoff_iso,
        hold_type=norm_hold,
        safe_window_hours=safe_window_hours,
        elapsed_seconds=elapsed_sec,
        elapsed_hours=elapsed_hr,
        remaining_seconds=remaining_sec,
        remaining_hours=remaining_hr,
        is_expired=False,
        is_temperature_safe=True,
        eligibility_status="eligible",
        blocking_reason=None,
        policy_citation=citation,
        observations_count=len(obs_list),
    )


def generate_predicted_surplus_alerts(
    session: Session,
    target_date: str,
    meal_type: str,
    is_synthetic: int = 0,
    threshold_kg: float = 2.0,
    service_level: float = 0.95,
) -> List[SurplusEvent]:
    """Generate or update G1 Predicted-Surplus Alerts from an upcoming meal plan (B1-B5).

    Predicted surplus is derived before service from quantity planning.
    It is clearly labelled as an estimate and NOT physically verified food.
    """
    clean_date = target_date.strip()
    norm_meal = normalize_meal_type(meal_type)

    # Reuse working cooking quantity planner
    meal_plan = generate_meal_plan(
        session=session,
        target_date=clean_date,
        meal_type=norm_meal,
        service_level=service_level,
        is_synthetic=is_synthetic,
    )

    alerts: List[SurplusEvent] = []

    for item in meal_plan.dishes:
        # Check threshold in compatible units
        unit = normalize_unit(item.unit)
        is_above_threshold = False
        if unit in ("kg", "L"):
            is_above_threshold = (item.expected_surplus_qty >= threshold_kg)
        elif unit == "count":
            # For count units (rotis/bananas), threshold is scaled (e.g. 10 count)
            is_above_threshold = (item.expected_surplus_qty >= max(threshold_kg * 5.0, 5.0))

        if not is_above_threshold:
            continue

        # Uncertainty range derived from forecast interval
        h_hat = meal_plan.forecast_h_hat
        low_consumed = h_hat * 0.90 * item.per_head_rate
        high_consumed = h_hat * 1.10 * item.per_head_rate
        hi_surplus = max(item.expected_surplus_qty, item.planned_quantity - low_consumed)
        lo_surplus = max(0.0, item.planned_quantity - high_consumed)
        uncertainty_str = f"{lo_surplus:.1f} – {hi_surplus:.1f} {unit}"

        # Deduplication check: meal_date, meal_type, dish_id, surplus_type="predicted"
        stmt = select(SurplusEvent).where(
            SurplusEvent.meal_date == clean_date,
            SurplusEvent.meal_type == norm_meal,
            SurplusEvent.dish_id == item.dish_id,
            SurplusEvent.surplus_type == "predicted",
        )
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            existing.estimated_qty = round(item.expected_surplus_qty, 2)
            existing.unit = unit
            existing.uncertainty_range = uncertainty_str
            existing.is_synthetic = is_synthetic
            alerts.append(existing)
        else:
            alert = SurplusEvent(
                meal_date=clean_date,
                meal_type=norm_meal,
                dish_id=item.dish_id,
                surplus_type="predicted",
                estimated_qty=round(item.expected_surplus_qty, 2),
                unit=unit,
                uncertainty_range=uncertainty_str,
                cooking_completed_at=None,
                hold_type="hot",
                safe_window_hours=FSSAI_HOT_HOLD_MAX_HOURS,
                safe_cutoff_at=None,
                current_temp_c=None,
                temp_recorded_at=None,
                temp_log_json=json.dumps([]),
                suspected_contamination=0,
                eligibility_status="pending_inspection",
                blocking_reason=(
                    "Predicted surplus estimate based on pre-service planning. "
                    "Awaiting kitchen completion and post-cooking physical weigh-in."
                ),
                policy_version=FSSAI_POLICY_VERSION,
                manager_status="pending",
                is_synthetic=is_synthetic,
            )
            session.add(alert)
            session.flush()
            log_audit(
                session,
                who="system",
                action="surplus_predicted_alert",
                new_value=f"dish_id={alert.dish_id}, qty={alert.estimated_qty} {alert.unit}, synth={is_synthetic}",
            )
            alerts.append(alert)

    session.commit()
    return alerts


def generate_measured_surplus_alerts(
    session: Session,
    meal_id: int,
    threshold_kg: float = 1.0,
    cooking_completed_at: Optional[str] = None,
) -> List[SurplusEvent]:
    """Generate or update G1 Measured-Surplus Alerts from post-service kitchen weigh-in records.

    Strict rule: Only serving_surplus (unserved counter/batch food) can be recovered.
    plate_waste is completely disqualified.
    """
    meal = session.get(Meal, meal_id)
    if not meal:
        return []

    alerts: List[SurplusEvent] = []

    for log in meal.dish_logs:
        # Strictly ignore plate waste and non-serving surplus
        if log.waste_stage != "serving_surplus":
            continue

        unit = normalize_unit(log.unit)
        is_above_threshold = False
        if unit in ("kg", "L"):
            is_above_threshold = (log.leftover_qty >= threshold_kg)
        elif unit == "count":
            is_above_threshold = (log.leftover_qty >= max(threshold_kg * 5.0, 5.0))

        if not is_above_threshold:
            continue

        # Deduplication check
        stmt = select(SurplusEvent).where(
            SurplusEvent.meal_id == meal.id,
            SurplusEvent.dish_id == log.dish_id,
            SurplusEvent.surplus_type == "measured",
        )
        existing = session.execute(stmt).scalar_one_or_none()

        start_time = cooking_completed_at or (existing.cooking_completed_at if existing else None)

        if existing:
            existing.estimated_qty = round(log.leftover_qty, 2)
            existing.unit = unit
            if start_time:
                existing.cooking_completed_at = start_time
            alerts.append(existing)
        else:
            alert = SurplusEvent(
                meal_id=meal.id,
                meal_date=meal.date,
                meal_type=meal.meal_type,
                dish_id=log.dish_id,
                surplus_type="measured",
                estimated_qty=round(log.leftover_qty, 2),
                unit=unit,
                uncertainty_range="Measured Leftover (Scale Weigh-in)",
                cooking_completed_at=start_time,
                hold_type="hot",
                safe_window_hours=FSSAI_HOT_HOLD_MAX_HOURS,
                safe_cutoff_at=None,
                current_temp_c=None,
                temp_recorded_at=None,
                temp_log_json=json.dumps([]),
                suspected_contamination=0,
                eligibility_status="pending_inspection",
                blocking_reason="Measured leftover recorded. Safe-holding start time and temperature observation required.",
                policy_version=FSSAI_POLICY_VERSION,
                manager_status="pending",
                is_synthetic=meal.is_synthetic,
            )
            session.add(alert)
            session.flush()
            log_audit(
                session,
                who="kitchen",
                action="surplus_measured_alert",
                new_value=f"meal_id={meal.id}, dish_id={alert.dish_id}, leftover={alert.estimated_qty} {alert.unit}",
            )
            alerts.append(alert)

    session.commit()
    return alerts


def record_safety_observation(
    session: Session,
    alert_id: int,
    temp_c: float,
    temp_unit: str = "C",
    hold_type: str = "hot",
    observed_at: Optional[str] = None,
    observed_by: str = "cook",
    cooking_completed_at: Optional[str] = None,
    suspected_contamination: bool = False,
    notes: str = "",
    as_of_time: Optional[Union[str, datetime]] = None,
) -> Tuple[SurplusEvent, SafetyClockResult]:
    """Record a time/temperature observation for a surplus alert and update the Food-Safety Clock."""
    alert = session.get(SurplusEvent, alert_id)
    if not alert:
        raise ValueError(f"Surplus event #{alert_id} not found.")

    # Unit conversion and validation
    norm_unit = temp_unit.strip().upper()
    temp_in_c: float
    if norm_unit == "F":
        temp_in_c = (temp_c - 32.0) * 5.0 / 9.0
    elif norm_unit == "C":
        temp_in_c = float(temp_c)
    else:
        raise ValueError(f"Invalid temperature unit '{temp_unit}'. Allowed units: 'C', 'F'.")

    obs_iso = parse_iso_dt(observed_at or as_of_time or now_iso()).isoformat()

    # Load existing observations
    observations = []
    if alert.temp_log_json:
        try:
            observations = json.loads(alert.temp_log_json)
        except Exception:
            observations = []

    new_obs = {
        "timestamp": obs_iso,
        "temp_c": round(temp_in_c, 1),
        "hold_type": hold_type.lower(),
        "observed_by": observed_by,
        "notes": notes,
    }
    observations.append(new_obs)

    # Update start time if supplied
    if cooking_completed_at:
        parsed_start = parse_iso_dt(cooking_completed_at)
        if parsed_start:
            alert.cooking_completed_at = parsed_start.isoformat()

    alert.hold_type = hold_type.lower()
    alert.suspected_contamination = 1 if suspected_contamination else 0
    alert.temp_log_json = json.dumps(observations)
    alert.current_temp_c = round(temp_in_c, 1)
    alert.temp_recorded_at = obs_iso

    # Re-evaluate Food-Safety Clock
    clock_result = evaluate_food_safety_clock(
        cooking_completed_at=alert.cooking_completed_at,
        hold_type=alert.hold_type,
        observations=observations,
        suspected_contamination=bool(alert.suspected_contamination),
        as_of_time=as_of_time,
        policy_version=alert.policy_version,
    )

    alert.safe_cutoff_at = clock_result.safe_cutoff_at
    alert.safe_window_hours = clock_result.safe_window_hours
    alert.eligibility_status = clock_result.eligibility_status
    alert.blocking_reason = clock_result.blocking_reason

    # If previously approved but now blocked (e.g. clock expired or temperature dropped), revoke approval
    if alert.manager_status == "approved" and clock_result.eligibility_status != "eligible":
        alert.manager_status = "pending"
        alert.communication_draft = None

    log_audit(
        session,
        who=observed_by,
        action="safety_observation_recorded",
        new_value=f"alert_id={alert.id}, temp={alert.current_temp_c}C, status={alert.eligibility_status}",
    )
    session.commit()
    return alert, clock_result


def build_communication_draft(
    alert: SurplusEvent,
    partner_name: Optional[str] = None,
    partner_phone: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Build shareable communication draft text and optional WhatsApp click-to-chat URL.

    WhatsApp click-to-chat URL is generated ONLY if a valid partner phone is configured.
    """
    dish_name = alert.dish.name if alert.dish else f"Dish #{alert.dish_id}"
    hold_str = f"{alert.current_temp_c:.1f}°C ({alert.hold_type.upper()} HOLDING)" if alert.current_temp_c is not None else "Temperature pending"

    lines: List[str] = []

    if alert.is_synthetic == 1:
        lines.append("⚠️ SYNTHETIC DEMONSTRATION — NOT A REAL FOOD DONATION ⚠️")
        lines.append("This alert is generated from synthetic test data. No real food is available for donation.\n")

    lines.append("🍲 *MessWise Surplus Food Recovery Alert*")
    lines.append(f"• *Date & Meal*: {alert.meal_date} ({alert.meal_type.title()})")
    lines.append(f"• *Dish*: {dish_name}")
    lines.append(f"• *Available Quantity*: {alert.estimated_qty} {alert.unit} ({alert.surplus_type.title()} Surplus)")
    if alert.cooking_completed_at:
        start_dt = parse_iso_dt(alert.cooking_completed_at)
        if start_dt:
            lines.append(f"• *Cooking Finished*: {start_dt.strftime('%I:%M %p')}")
    if alert.safe_cutoff_at:
        cutoff_dt = parse_iso_dt(alert.safe_cutoff_at)
        if cutoff_dt:
            lines.append(f"• *Safe Window Cutoff*: {cutoff_dt.strftime('%I:%M %p')} (FSSAI 2019 compliant)")
    lines.append(f"• *Holding Status*: {hold_str}")
    lines.append(f"• *Manager Verified*: {alert.manager_who or 'Mess Supervisor'}")
    lines.append("\n*Action*: Please confirm pickup capability within the safe window.")

    draft_text = "\n".join(lines)

    wa_link = None
    if partner_phone:
        clean_phone = "".join(ch for ch in partner_phone if ch.isdigit())
        if clean_phone:
            wa_link = f"https://wa.me/{clean_phone}?text={quote(draft_text)}"

    return draft_text, wa_link


def approve_surplus_alert(
    session: Session,
    alert_id: int,
    manager_who: str = "manager",
    manager_reason: Optional[str] = None,
    partner_name: Optional[str] = None,
    partner_phone: Optional[str] = None,
    as_of_time: Optional[Union[str, datetime]] = None,
) -> SurplusEvent:
    """Manager approval of a surplus alert.

    MANDATORY FOOD-SAFETY GATE:
    Approval is strictly refused if the Food-Safety Clock has expired,
    temperature is out of range, data is missing, or contamination is suspected.
    """
    alert = session.get(SurplusEvent, alert_id)
    if not alert:
        raise ValueError(f"Surplus event #{alert_id} not found.")

    observations = []
    if alert.temp_log_json:
        try:
            observations = json.loads(alert.temp_log_json)
        except Exception:
            observations = []

    # Re-evaluate live safety clock
    clock = evaluate_food_safety_clock(
        cooking_completed_at=alert.cooking_completed_at,
        hold_type=alert.hold_type,
        observations=observations,
        suspected_contamination=bool(alert.suspected_contamination),
        as_of_time=as_of_time,
        policy_version=alert.policy_version,
    )

    alert.eligibility_status = clock.eligibility_status
    alert.blocking_reason = clock.blocking_reason
    alert.safe_cutoff_at = clock.safe_cutoff_at

    # STRICT GATE: Refuse approval if ineligible
    if clock.eligibility_status != "eligible":
        raise ValueError(
            f"Cannot approve surplus donation for {alert.dish.name if alert.dish else alert.dish_id}: "
            f"Food safety gate blocked ({clock.eligibility_status}): {clock.blocking_reason}"
        )

    # Approve
    alert.manager_status = "approved"
    alert.manager_who = manager_who.strip() or "manager"
    alert.manager_reason = manager_reason
    alert.manager_action_at = now_iso(as_of_time)
    alert.partner_name = partner_name
    alert.partner_phone = partner_phone

    draft_text, _ = build_communication_draft(alert, partner_name, partner_phone)
    alert.communication_draft = draft_text

    log_audit(
        session,
        who=alert.manager_who,
        action="surplus_approved",
        new_value=f"alert_id={alert.id}, dish_id={alert.dish_id}, qty={alert.estimated_qty} {alert.unit}",
    )
    session.commit()
    return alert


def dismiss_surplus_alert(
    session: Session,
    alert_id: int,
    manager_who: str = "manager",
    manager_reason: str = "Dismissed by kitchen manager",
) -> SurplusEvent:
    """Manager dismissal of a surplus alert with mandatory reason."""
    alert = session.get(SurplusEvent, alert_id)
    if not alert:
        raise ValueError(f"Surplus event #{alert_id} not found.")

    clean_reason = manager_reason.strip() if manager_reason else "Dismissed by manager"

    alert.manager_status = "dismissed"
    alert.manager_who = manager_who.strip() or "manager"
    alert.manager_reason = clean_reason
    alert.manager_action_at = now_iso()
    alert.eligibility_status = "dismissed"
    alert.blocking_reason = f"Dismissed: {clean_reason}"
    alert.communication_draft = None

    log_audit(
        session,
        who=alert.manager_who,
        action="surplus_dismissed",
        new_value=f"alert_id={alert.id}, reason={clean_reason}",
    )
    session.commit()
    return alert


def list_surplus_alerts_query(
    session: Session,
    is_synthetic: Optional[int] = None,
    surplus_type: Optional[str] = None,
    manager_status: Optional[str] = None,
    eligibility_status: Optional[str] = None,
    limit: int = 50,
) -> List[SurplusEvent]:
    """Retrieve surplus alerts ordered by ID descending."""
    stmt = select(SurplusEvent)
    if is_synthetic is not None:
        stmt = stmt.where(SurplusEvent.is_synthetic == is_synthetic)
    if surplus_type is not None:
        stmt = stmt.where(SurplusEvent.surplus_type == surplus_type)
    if manager_status is not None:
        stmt = stmt.where(SurplusEvent.manager_status == manager_status)
    if eligibility_status is not None:
        stmt = stmt.where(SurplusEvent.eligibility_status == eligibility_status)
    stmt = stmt.order_by(desc(SurplusEvent.id)).limit(limit)
    return list(session.execute(stmt).scalars().all())
