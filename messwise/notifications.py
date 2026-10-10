"""MessWise In-App Operational Notifications Engine (Module I: I9).

Evaluates active operational events across forecasts, kitchen logs,
waste intelligence, and surplus safety clocks.
Provides deduplicated, honest alerts for kitchen managers.
Never generates fake or speculative notifications.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from messwise.db import Meal, Prediction, SurplusEvent
from messwise.intelligence import detect_dish_waste_anomalies


@dataclass
class OperationalNotification:
    """Structured in-app notification item (I9)."""

    notification_id: str
    category: str  # "forecast_risk", "safety_clock", "waste_anomaly", "missing_logs"
    severity: str  # "high", "medium", "info"
    title: str
    message: str
    action_hint: str
    timestamp: str
    is_synthetic: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_active_notifications(
    session: Session,
    is_synthetic: int = 1,
) -> List[OperationalNotification]:
    """Evaluate and retrieve deduplicated in-app operational notifications (I9)."""
    notifications: List[OperationalNotification] = []
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Forecast Uncertainty & High Risk Alerts
    recent_preds = session.execute(
        select(Prediction)
        .where(Prediction.is_synthetic == is_synthetic)
        .order_by(Prediction.created_at.desc())
        .limit(3)
    ).scalars().all()

    for pred in recent_preds:
        spread = pred.h_hi - pred.h_lo
        if spread >= 50:
            notif_id = f"fc_spread_{pred.id}"
            notifications.append(
                OperationalNotification(
                    notification_id=notif_id,
                    category="forecast_risk",
                    severity="medium",
                    title="High Forecast Uncertainty",
                    message=(
                        f"Upcoming forecast for {pred.meal_date} {pred.meal_type.title()} "
                        f"has a wide conformal uncertainty band ({int(pred.h_lo)} to {int(pred.h_hi)} students, ±{int(spread/2)})."
                    ),
                    action_hint="Check hostel event calendar and review planning service level before cooking.",
                    timestamp=pred.created_at,
                    is_synthetic=is_synthetic,
                )
            )

    # 2. Safety-Clock Expiration or Blocked Eligibility Alerts
    surplus_records = session.execute(
        select(SurplusEvent)
        .where(SurplusEvent.is_synthetic == is_synthetic)
        .order_by(SurplusEvent.created_at.desc())
        .limit(5)
    ).scalars().all()

    for se in surplus_records:
        if se.eligibility_status in ("blocked_expired", "blocked_temperature"):
            notif_id = f"surplus_blocked_{se.id}"
            notifications.append(
                OperationalNotification(
                    notification_id=notif_id,
                    category="safety_clock",
                    severity="high",
                    title="Surplus Safety Clock Expired",
                    message=(
                        f"Surplus event #{se.id} ({se.meal_date} {se.meal_type}) is blocked from donation "
                        f"under food safety policy ({se.blocking_reason or 'expired safety window'})."
                    ),
                    action_hint="Direct surplus to verified on-campus composting or biowaste bin.",
                    timestamp=se.created_at,
                    is_synthetic=is_synthetic,
                )
            )

    # 3. Statistical Waste Anomalies
    anomalies = detect_dish_waste_anomalies(session=session, is_synthetic=is_synthetic)
    flagged_anomalies = [a for a in anomalies if a.is_anomaly]
    for anom in flagged_anomalies[:3]:
        notif_id = f"waste_anom_{anom.log_id}"
        notifications.append(
            OperationalNotification(
                notification_id=notif_id,
                category="waste_anomaly",
                severity="medium",
                title=f"Waste Anomaly: {anom.dish_name}",
                message=(
                    f"{anom.dish_name} had {anom.observed_waste_pct:.1f}% waste on {anom.meal_date} "
                    f"(historical median: {anom.historical_median_pct:.1f}%, robust z = {anom.z_score:+.2f})."
                ),
                action_hint="Review portion spoons, batch size, or root-cause hypotheses on Waste Intelligence.",
                timestamp=now_iso,
                is_synthetic=is_synthetic,
            )
        )

    # Deduplicate by notification_id
    seen_ids = set()
    deduped = []
    for n in notifications:
        if n.notification_id not in seen_ids:
            seen_ids.add(n.notification_id)
            deduped.append(n)

    return deduped
