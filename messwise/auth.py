"""MessWise Governance, Role-Based Access Control, and Multi-Mess Isolation (Modules I5 & I7).

Implements specifications from PLAN.md Section 8.9 and Sprint Instructions:
- Real backend authorization guards (NOT just client-side button hiding).
- Defined roles: manager, cook, warden, auditor, student, ngo.
- Strict action permission verification with 403 / PermissionError enforcement.
- Multi-mess site isolation: users cannot query or mutate operational records belonging to another mess.
- Safe defaults: fails safely if unauthorized.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Valid platform personas / roles
VALID_ROLES: Set[str] = {
    "manager",
    "cook",
    "warden",
    "auditor",
    "student",
    "ngo",
}

DEFAULT_ROLE = "manager"
DEFAULT_MESS_ID = "default_mess"

# Action-level permissions matrix
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "manager": {
        "create_meal",
        "create_dish_log",
        "save_meal_plan",
        "override_plan",
        "manage_recipes",
        "configure_costs",
        "retrain_model",
        "rollback_model",
        "review_surplus",
        "record_safety_temp",
        "record_tally",
        "add_calendar_event",
        "view_audit_log",
        "view_reports",
        "view_impact",
        "export_data",
        "student_checkin",
        "student_rate",
        "view_impact_wall",
        "view_ngo_surplus",
    },
    "cook": {
        "create_meal",
        "create_dish_log",
        "override_plan",
        "record_safety_temp",
        "record_tally",
        "view_impact_wall",
    },
    "warden": {
        "view_audit_log",
        "view_reports",
        "view_impact",
        "view_impact_wall",
        "export_data",
    },
    "auditor": {
        "view_audit_log",
        "view_reports",
        "view_impact",
        "view_impact_wall",
        "export_data",
    },
    "student": {
        "student_checkin",
        "student_rate",
        "view_impact_wall",
    },
    "ngo": {
        "view_ngo_surplus",
        "view_impact_wall",
    },
}


class AuthorizationError(PermissionError):
    """Raised when an operation is disallowed by role-based access policy."""
    pass


class CrossMessAccessViolation(PermissionError):
    """Raised when an operation attempts to access or mutate data across a mess boundary."""
    pass


def check_role_permission(role: str, action: str) -> bool:
    """Check if the specified role has permission to execute an action."""
    r_norm = str(role).strip().lower()
    allowed_actions = ROLE_PERMISSIONS.get(r_norm, set())
    return action in allowed_actions


def enforce_role_permission(role: str, action: str) -> None:
    """Raise AuthorizationError if the role lacks permission for the action."""
    if not check_role_permission(role, action):
        raise AuthorizationError(
            f"Unauthorized operation: Role '{role}' does not have permission to execute action '{action}'."
        )


def validate_mess_scope(
    requested_mess_id: Optional[str],
    user_authorized_mess_id: str = DEFAULT_MESS_ID,
) -> str:
    """Ensure data operations cannot cross or violate the mess isolation boundary (I7)."""
    target = (requested_mess_id or user_authorized_mess_id).strip()
    user_mess = user_authorized_mess_id.strip()

    if target != user_mess and user_mess != "global_admin":
        raise CrossMessAccessViolation(
            f"Cross-mess access denied: User authorized for mess '{user_mess}' "
            f"cannot read or modify records belonging to mess '{target}'."
        )
    return target


def get_role_description(role: str) -> Dict[str, Any]:
    """Retrieve capabilities description for display or documentation."""
    r_norm = str(role).strip().lower()
    return {
        "role": r_norm,
        "is_valid": r_norm in VALID_ROLES,
        "allowed_actions_count": len(ROLE_PERMISSIONS.get(r_norm, set())),
        "allowed_actions": sorted(list(ROLE_PERMISSIONS.get(r_norm, set()))),
    }
