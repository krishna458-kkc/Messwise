"""MessWise Student & Community Engagement Module (Module F: F1, F2, F3).

Implements P1 specifications from PLAN.md Section 8.6:
- F1: Anonymous, aggregate-only meal check-ins (Yes / No / Maybe) with duplicate control.
- F2: One-tap anonymous dish ratings (1 to 5 stars) for menu popularity and kitchen feedback.
- F3: Public Student Impact Wall displaying verified waste reduction, CO2e, and meals equivalent.
- Privacy-first: Zero names, roll numbers, facial scans, biometrics, or personal identifiers.
- Synthetic separation: Real measurements explicitly distinguished from demonstration data.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from messwise.db import (
    Dish,
    Meal,
    get_dish_ratings_summary,
    get_meal_checkins_summary,
    record_meal_checkin,
    record_meal_rating,
)
from messwise.impact import generate_impact_summary

logger = logging.getLogger(__name__)


def generate_privacy_hash(client_identifier: Optional[str] = None) -> Optional[str]:
    """Generate a one-way, privacy-preserving SHA256 hash for anonymous duplicate suppression.
    
    Does NOT store raw IP addresses, user agents, or personal identifiers.
    """
    if not client_identifier:
        return None
    salt = "messwise-privacy-salt-2026"
    return hashlib.sha256(f"{client_identifier}:{salt}".encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# F1: Anonymous Meal Check-in Intake
# ---------------------------------------------------------------------------
def submit_student_checkin(
    session: Session,
    meal_date: str,
    meal_type: str,
    response: str,
    client_token: Optional[str] = None,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
) -> Dict[str, Any]:
    """Record an anonymous student meal attendance intention (F1)."""
    device_hash = generate_privacy_hash(client_token)

    record = record_meal_checkin(
        session=session,
        meal_date=meal_date,
        meal_type=meal_type,
        response=response,
        device_hash=device_hash,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
    )

    summary = get_meal_checkins_summary(
        session=session,
        meal_date=meal_date,
        meal_type=meal_type,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
    )

    return {
        "success": True,
        "message": f"Check-in recorded anonymously for {meal_date} {meal_type.title()}.",
        "your_response": record.response,
        "current_meal_tally": {
            "yes_count": summary["yes_count"],
            "no_count": summary["no_count"],
            "maybe_count": summary["maybe_count"],
            "total_responses": summary["total_responses"],
        },
        "privacy_notice": "Anonymous: No personal IDs, student roll numbers, or biometrics are stored.",
    }


# ---------------------------------------------------------------------------
# F2: One-Tap Dish Rating
# ---------------------------------------------------------------------------
def submit_student_dish_rating(
    session: Session,
    meal_date: str,
    meal_type: str,
    dish_id: int,
    rating: int,
    comment: Optional[str] = None,
    client_token: Optional[str] = None,
    mess_id: str = "default_mess",
    is_synthetic: int = 0,
) -> Dict[str, Any]:
    """Record an anonymous dish rating (1 to 5 stars) from a dining student (F2)."""
    dish = session.get(Dish, dish_id)
    if not dish:
        raise ValueError(f"Dish with id {dish_id} does not exist.")

    device_hash = generate_privacy_hash(client_token)

    record = record_meal_rating(
        session=session,
        meal_date=meal_date,
        meal_type=meal_type,
        dish_id=dish_id,
        rating=rating,
        comment=comment,
        device_hash=device_hash,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
    )

    summary = get_dish_ratings_summary(
        session=session,
        dish_id=dish_id,
        mess_id=mess_id,
        is_synthetic=is_synthetic,
    )

    return {
        "success": True,
        "message": f"Thank you! Your feedback for {dish.name} has been recorded.",
        "dish_name": dish.name,
        "your_rating": record.rating,
        "average_dish_rating": summary["average_rating"],
        "total_reviews": summary["ratings_count"],
        "popularity_tier": summary["popularity_tier"],
    }


# ---------------------------------------------------------------------------
# F3: Student Impact Wall (Public Read-Only)
# ---------------------------------------------------------------------------
def get_student_impact_wall(
    session: Session,
    is_synthetic: int = 0,
    reporting_period: str = "October 2026",
    mess_id: str = "default_mess",
) -> Dict[str, Any]:
    """Retrieve public aggregate environmental and food-saving impact for the Student Impact Wall (F3).
    
    Strict Privacy and Candor:
    - Never exposes individual student records, internal IDs, or manager financial audit notes.
    - If real data is unverified or empty, displays transparent 'Pending Verified Measurements' badge.
    - Demonstrates true metrics without fabricating CO2e or food savings.
    """
    impact_summary = generate_impact_summary(
        session=session,
        is_synthetic=is_synthetic,
        reporting_period=reporting_period,
    )

    # Candor disclosures
    if is_synthetic == 1:
        status_banner = "DEMONSTRATION & DEVELOPMENT DATA ONLY"
        is_verified = False
        subtitle = "Simulated campus impact generated for algorithm validation and demonstration."
    else:
        if impact_summary.meals_count == 0 or not impact_summary.co2e_impact.is_available:
            status_banner = "REAL PILOT DATA PENDING"
            is_verified = False
            subtitle = "Active operational measurement in progress. Results will appear once operator-verified pilot records are logged."
        else:
            status_banner = "VERIFIED REAL-WORLD PILOT RESULTS"
            is_verified = True
            subtitle = "Measured food waste reduction and verified green-campus impact from your hostel dining hall."

    return {
        "wall_title": "MessWise Student Impact Wall",
        "subtitle": subtitle,
        "reporting_period": reporting_period,
        "status_banner": status_banner,
        "is_verified_pilot": is_verified,
        "is_synthetic_demo": bool(is_synthetic == 1),
        "data_basis_label": impact_summary.data_basis_label,
        "metrics": {
            "food_waste_avoided_kg": impact_summary.eligible_avoided_kg,
            "central_co2e_saved_kg": impact_summary.co2e_impact.central_co2e_kg if impact_summary.co2e_impact.is_available else 0.0,
            "meals_equivalent_saved": impact_summary.meals_equivalent.meals_equivalent if impact_summary.meals_equivalent.is_available else 0.0,
            "service_level_preserved_pct": impact_summary.service_level_preserved_pct,
            "total_meals_served": impact_summary.meals_count,
            "waste_percentage": impact_summary.waste_percentage,
        },
        "sdg_alignment": {
            "target": "UN SDG Target 12.3: Halving Food Waste",
            "status": impact_summary.sdg123.status_label if impact_summary.sdg123 else "Baseline in progress",
            "reduction_pct": impact_summary.sdg123.reduction_pct if impact_summary.sdg123 else None,
        },
        "privacy_guarantee": "Zero student names, roll numbers, personal IDs, or biometric data are stored by MessWise.",
    }
