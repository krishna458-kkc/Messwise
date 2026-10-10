"""MessWise - Historical Register & Headcount CSV Import (Module C: C4).

Implements specifications from PLAN.md Section 5 (Module C4) and Section 7.2:
- Imports historical attendance registers and billing counts to seed forecasting and baseline metrics.
- Validates dates, normalized meal types, non-negative headcounts, and capacity constraints.
- Identifies and rejects duplicate meal records against existing database records and within the batch.
- Strictly separates synthetic demonstration imports from real pilot imports with explicit user confirmation.
- Generates downloadable CSV error reports detailing rejected rows and failure reasons.
- Creates governance audit trail in audit_log.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from messwise.db import (
    AuditLog,
    Dish,
    DishLog,
    Meal,
    get_or_create_dish,
)
from messwise.validation import normalize_meal_type, normalize_unit, VALID_MEAL_TYPES


# Standard column header aliases for intelligent auto-mapping
HEADER_ALIASES: Dict[str, List[str]] = {
    "date": ["date", "meal_date", "day", "date_str", "service_date"],
    "meal_type": ["meal_type", "meal", "service", "meal_slot", "session", "service_slot", "slot"],
    "headcount": ["headcount", "attendance", "count", "actual_count", "diners", "students_served"],
    "hostel_strength": ["hostel_strength", "strength", "capacity", "total_students", "hostel_capacity"],
    "event_flag": ["event_flag", "event", "is_event", "special_event", "fest"],
    "exam_flag": ["exam_flag", "exam", "is_exam", "exam_period"],
    "holiday_flag": ["holiday_flag", "holiday", "is_holiday", "weekend"],
    "temp_c": ["temp_c", "temperature", "temp", "temperature_c"],
    "rain_mm": ["rain_mm", "rain", "rainfall", "rainfall_mm"],
}


@dataclass
class CSVPreviewResult:
    """Pre-import CSV inspection summary for user review and column mapping."""

    total_rows: int
    headers: List[str]
    suggested_mapping: Dict[str, Optional[str]]
    sample_rows: List[Dict[str, Any]]
    is_valid: bool
    status_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CSVImportRowError:
    """Detailed error record for a rejected CSV row."""

    row_index: int
    raw_data: Dict[str, Any]
    error_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CSVImportResult:
    """Structured report returned after processing a CSV import batch."""

    total_rows: int
    accepted_rows: int
    rejected_rows: int
    imported_meal_ids: List[int]
    errors: List[CSVImportRowError]
    rejected_csv_bytes: Optional[bytes]
    data_environment: str
    audit_log_id: Optional[int] = None
    status_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "accepted_rows": self.accepted_rows,
            "rejected_rows": self.rejected_rows,
            "imported_meal_ids": self.imported_meal_ids,
            "errors": [e.to_dict() for e in self.errors],
            "data_environment": self.data_environment,
            "audit_log_id": self.audit_log_id,
            "status_summary": self.status_summary,
        }


def parse_date_string(raw_val: str) -> Optional[str]:
    """Parse flexible date strings into canonical YYYY-MM-DD ISO format."""
    val = str(raw_val).strip()
    if not val:
        return None

    # Standard YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            return None

    # Formats: DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(val, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def preview_register_csv(csv_content: str | bytes) -> CSVPreviewResult:
    """Inspect CSV bytes/text and propose intelligent column mappings."""
    if isinstance(csv_content, bytes):
        try:
            text_str = csv_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text_str = csv_content.decode("latin-1")
            except Exception as e:
                return CSVPreviewResult(
                    total_rows=0,
                    headers=[],
                    suggested_mapping={},
                    sample_rows=[],
                    is_valid=False,
                    status_message=f"Failed to decode CSV text: {e}",
                )
    else:
        text_str = csv_content

    text_io = io.StringIO(text_str.strip())
    try:
        reader = csv.DictReader(text_io)
        if not reader.fieldnames:
            return CSVPreviewResult(
                total_rows=0,
                headers=[],
                suggested_mapping={},
                sample_rows=[],
                is_valid=False,
                status_message="CSV has no header row or is empty.",
            )
        headers = [h.strip() for h in reader.fieldnames if h]
    except Exception as e:
        return CSVPreviewResult(
            total_rows=0,
            headers=[],
            suggested_mapping={},
            sample_rows=[],
            is_valid=False,
            status_message=f"Malformed CSV: {e}",
        )

    # Propose suggested mapping
    norm_headers = {h.lower().replace(" ", "_"): h for h in headers}
    mapping: Dict[str, Optional[str]] = {}
    for canon_field, aliases in HEADER_ALIASES.items():
        matched = None
        for alias in aliases:
            if alias in norm_headers:
                matched = norm_headers[alias]
                break
        mapping[canon_field] = matched

    # Read sample rows and total count
    text_io.seek(0)
    reader = csv.DictReader(text_io)
    all_rows = list(reader)
    sample = all_rows[:5]

    has_date = mapping.get("date") is not None
    has_meal = mapping.get("meal_type") is not None
    has_head = mapping.get("headcount") is not None
    is_valid = has_date and has_meal and has_head

    status_msg = (
        "Column mapping successfully identified."
        if is_valid
        else "Missing required core columns: please map Date, Meal Type, and Headcount."
    )

    return CSVPreviewResult(
        total_rows=len(all_rows),
        headers=headers,
        suggested_mapping=mapping,
        sample_rows=sample,
        is_valid=is_valid,
        status_message=status_msg,
    )


def import_register_csv(
    session: Session,
    csv_content: str | bytes,
    column_mapping: Dict[str, str],
    is_synthetic: int = 1,
    who: str = "mess_manager",
    default_hostel_strength: int = 500,
    allow_update_duplicates: bool = False,
) -> CSVImportResult:
    """Validate and import attendance/register meal records into the database.

    Enforces:
    - Date format validation (normalized to YYYY-MM-DD).
    - Meal type normalisation ('breakfast', 'lunch', 'snacks', 'dinner').
    - Non-negative headcounts with capacity checks (headcount <= hostel_strength).
    - Duplicate detection against existing database records and intra-batch duplicates.
    - Full AuditLog generation tracking accepted and rejected rows.
    - Generation of a downloadable CSV error report for all rejected entries.
    """
    if isinstance(csv_content, bytes):
        text_str = csv_content.decode("utf-8", errors="replace")
    else:
        text_str = csv_content

    text_io = io.StringIO(text_str.strip())
    reader = csv.DictReader(text_io)
    raw_rows = list(reader)

    if not raw_rows:
        return CSVImportResult(
            total_rows=0,
            accepted_rows=0,
            rejected_rows=0,
            imported_meal_ids=[],
            errors=[],
            rejected_csv_bytes=None,
            data_environment="Synthetic Demo" if is_synthetic == 1 else "Real Pilot",
            status_summary="CSV file contains zero data rows.",
        )

    # Required column presence check
    date_col = column_mapping.get("date")
    meal_col = column_mapping.get("meal_type")
    head_col = column_mapping.get("headcount")
    strength_col = column_mapping.get("hostel_strength")
    event_col = column_mapping.get("event_flag")
    exam_col = column_mapping.get("exam_flag")
    holiday_col = column_mapping.get("holiday_flag")
    temp_col = column_mapping.get("temp_c")
    rain_col = column_mapping.get("rain_mm")

    if not (date_col and meal_col and head_col):
        err = CSVImportRowError(
            row_index=0,
            raw_data={},
            error_reason="Missing mandatory column mapping for Date, Meal Type, or Headcount.",
        )
        return CSVImportResult(
            total_rows=len(raw_rows),
            accepted_rows=0,
            rejected_rows=len(raw_rows),
            imported_meal_ids=[],
            errors=[err],
            rejected_csv_bytes=None,
            data_environment="Synthetic Demo" if is_synthetic == 1 else "Real Pilot",
            status_summary="Mapping error: Required columns not configured.",
        )

    # Pre-fetch existing (date, meal_type, is_synthetic) tuples to catch duplicates
    existing_records: Set[Tuple[str, str]] = set()
    existing_stmt = select(Meal.date, Meal.meal_type).where(Meal.is_synthetic == is_synthetic)
    for row in session.execute(existing_stmt).all():
        existing_records.add((row[0], row[1].lower()))

    batch_seen_keys: Set[Tuple[str, str]] = set()
    accepted_meal_ids: List[int] = []
    errors: List[CSVImportRowError] = []

    for idx, r in enumerate(raw_rows, start=1):
        # 1. Date Validation
        raw_date = r.get(date_col, "")
        clean_date = parse_date_string(raw_date)
        if not clean_date:
            errors.append(
                CSVImportRowError(
                    row_index=idx,
                    raw_data=r,
                    error_reason=f"Invalid date format '{raw_date}'. Expected YYYY-MM-DD or DD/MM/YYYY.",
                )
            )
            continue

        # 2. Meal Type Validation
        raw_meal = str(r.get(meal_col, "")).strip().lower()
        if raw_meal not in VALID_MEAL_TYPES:
            errors.append(
                CSVImportRowError(
                    row_index=idx,
                    raw_data=r,
                    error_reason=f"Invalid meal type '{raw_meal}'. Allowed: {', '.join(VALID_MEAL_TYPES)}.",
                )
            )
            continue
        norm_meal = raw_meal

        # 3. Headcount Validation
        raw_head = r.get(head_col, "")
        try:
            headcount_val = int(float(str(raw_head).strip()))
            if headcount_val < 0:
                raise ValueError("Negative headcount")
        except (ValueError, TypeError):
            errors.append(
                CSVImportRowError(
                    row_index=idx,
                    raw_data=r,
                    error_reason=f"Invalid headcount '{raw_head}'. Must be a non-negative integer.",
                )
            )
            continue

        # 4. Hostel Strength Validation
        hostel_str_val = default_hostel_strength
        if strength_col and r.get(strength_col):
            try:
                hostel_str_val = int(float(str(r.get(strength_col)).strip()))
                if hostel_str_val <= 0:
                    hostel_str_val = default_hostel_strength
            except (ValueError, TypeError):
                hostel_str_val = default_hostel_strength

        # Plausibility check: headcount cannot exceed hostel physical capacity
        if headcount_val > hostel_str_val * 1.5:  # small tolerance for guests
            errors.append(
                CSVImportRowError(
                    row_index=idx,
                    raw_data=r,
                    error_reason=(
                        f"Headcount ({headcount_val}) excessively exceeds hostel capacity "
                        f"({hostel_str_val}). Please verify record."
                    ),
                )
            )
            continue

        # 5. Duplicate Detection
        record_key = (clean_date, norm_meal)
        if record_key in batch_seen_keys:
            errors.append(
                CSVImportRowError(
                    row_index=idx,
                    raw_data=r,
                    error_reason=f"Duplicate entry inside CSV batch for {clean_date} ({norm_meal}).",
                )
            )
            continue

        if record_key in existing_records and not allow_update_duplicates:
            errors.append(
                CSVImportRowError(
                    row_index=idx,
                    raw_data=r,
                    error_reason=(
                        f"Record already exists in database for {clean_date} ({norm_meal}) "
                        f"under is_synthetic={is_synthetic}."
                    ),
                )
            )
            continue

        # 6. Parse Contextual Flags & Weather
        def parse_flag(col_name: Optional[str]) -> int:
            if not col_name:
                return 0
            v = str(r.get(col_name, "0")).strip().lower()
            return 1 if v in ("1", "true", "yes", "y") else 0

        def parse_float(col_name: Optional[str]) -> Optional[float]:
            if not col_name:
                return None
            v = str(r.get(col_name, "")).strip()
            if not v:
                return None
            try:
                return float(v)
            except ValueError:
                return None

        event_val = parse_flag(event_col)
        exam_val = parse_flag(exam_col)
        holiday_val = parse_flag(holiday_col)
        temp_val = parse_float(temp_col)
        rain_val = parse_float(rain_col)

        # 7. Persist Meal Record
        new_meal = Meal(
            date=clean_date,
            meal_type=norm_meal,
            headcount=headcount_val,
            hostel_strength=hostel_str_val,
            event_flag=event_val,
            exam_flag=exam_val,
            holiday_flag=holiday_val,
            temp_c=temp_val,
            rain_mm=rain_val,
            source="register_csv",
            is_synthetic=is_synthetic,
        )
        session.add(new_meal)
        session.flush()

        accepted_meal_ids.append(new_meal.id)
        batch_seen_keys.add(record_key)
        existing_records.add(record_key)

    # 8. Commit and Log Audit Record
    env_label = "Synthetic Demo" if is_synthetic == 1 else "Real Pilot"
    audit_msg = (
        f"CSV Register Import: {len(accepted_meal_ids)} meals imported, "
        f"{len(errors)} rows rejected into {env_label} environment."
    )
    audit = AuditLog(
        who=who,
        action="csv_register_import",
        old_value=None,
        new_value=audit_msg,
    )
    session.add(audit)
    session.commit()

    # 9. Build Downloadable Rejected Rows CSV if any errors occurred
    rejected_bytes: Optional[bytes] = None
    if errors:
        out_buf = io.StringIO()
        err_writer = csv.writer(out_buf)
        err_headers = list(raw_rows[0].keys()) + ["rejection_reason"]
        err_writer.writerow(err_headers)
        for e in errors:
            row_vals = [e.raw_data.get(k, "") for k in raw_rows[0].keys()] + [e.error_reason]
            err_writer.writerow(row_vals)
        rejected_bytes = out_buf.getvalue().encode("utf-8")

    status_summary = (
        f"Successfully imported {len(accepted_meal_ids)} meals. "
        f"{len(errors)} rows were rejected due to validation or duplicate rules."
    )

    return CSVImportResult(
        total_rows=len(raw_rows),
        accepted_rows=len(accepted_meal_ids),
        rejected_rows=len(errors),
        imported_meal_ids=accepted_meal_ids,
        errors=errors,
        rejected_csv_bytes=rejected_bytes,
        data_environment=env_label,
        audit_log_id=audit.id,
        status_summary=status_summary,
    )
