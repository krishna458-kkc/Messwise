"""Tests for MessWise Historical Register CSV Import (Module C: C4)."""

import io
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from messwise.csv_import import (
    import_register_csv,
    parse_date_string,
    preview_register_csv,
)
from messwise.db import AuditLog, Base, Meal, init_db


@pytest.fixture
def mem_session():
    """Provides an isolated in-memory SQLite session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_parse_date_string():
    """Verify robust date parsing across international formats."""
    assert parse_date_string("2026-10-15") == "2026-10-15"
    assert parse_date_string("15/10/2026") == "2026-10-15"
    assert parse_date_string("15-10-2026") == "2026-10-15"
    assert parse_date_string("invalid-date") is None
    assert parse_date_string("") is None


def test_preview_register_csv_auto_mapping():
    """Verify preview auto-maps typical column header aliases."""
    csv_data = """meal_date,service_slot,attendance,hostel_capacity,is_event
2026-10-11,lunch,410,500,0
2026-10-11,dinner,395,500,1
"""
    res = preview_register_csv(csv_data)
    assert res.is_valid is True
    assert res.total_rows == 2
    assert res.suggested_mapping["date"] == "meal_date"
    assert res.suggested_mapping["meal_type"] == "service_slot"
    assert res.suggested_mapping["headcount"] == "attendance"
    assert res.suggested_mapping["hostel_strength"] == "hostel_capacity"
    assert res.suggested_mapping["event_flag"] == "is_event"


def test_import_register_csv_valid(mem_session):
    """Verify clean import of valid CSV records into target environment."""
    csv_data = """date,meal_type,headcount,hostel_strength
2026-10-01,breakfast,320,500
2026-10-01,lunch,440,500
2026-10-01,dinner,410,500
"""
    col_map = {
        "date": "date",
        "meal_type": "meal_type",
        "headcount": "headcount",
        "hostel_strength": "hostel_strength",
    }
    result = import_register_csv(
        session=mem_session,
        csv_content=csv_data,
        column_mapping=col_map,
        is_synthetic=1,
        who="test_warden",
    )
    assert result.total_rows == 3
    assert result.accepted_rows == 3
    assert result.rejected_rows == 0
    assert len(result.imported_meal_ids) == 3
    assert result.rejected_csv_bytes is None

    # Verify meals stored in database with source="register_csv"
    meals = mem_session.execute(select(Meal).where(Meal.is_synthetic == 1)).scalars().all()
    assert len(meals) == 3
    assert all(m.source == "register_csv" for m in meals)

    # Verify AuditLog created
    audit = mem_session.execute(select(AuditLog).where(AuditLog.action == "csv_register_import")).scalars().first()
    assert audit is not None
    assert audit.who == "test_warden"
    assert "3 meals imported" in audit.new_value


def test_import_register_csv_rejects_negative_headcount_and_duplicates(mem_session):
    """Verify validation rejects negative attendance and duplicate entries."""
    csv_data = """date,meal_type,headcount,hostel_strength
2026-10-02,lunch,400,500
2026-10-02,lunch,410,500
2026-10-03,dinner,-50,500
2026-10-04,invalid_meal,300,500
2026-10-05,lunch,1500,500
"""
    col_map = {
        "date": "date",
        "meal_type": "meal_type",
        "headcount": "headcount",
        "hostel_strength": "hostel_strength",
    }
    result = import_register_csv(
        session=mem_session,
        csv_content=csv_data,
        column_mapping=col_map,
        is_synthetic=1,
    )
    assert result.total_rows == 5
    assert result.accepted_rows == 1  # only first row accepted
    assert result.rejected_rows == 4
    assert result.rejected_csv_bytes is not None

    reasons = [e.error_reason for e in result.errors]
    assert any("Duplicate entry inside CSV batch" in r for r in reasons)
    assert any("non-negative integer" in r for r in reasons)
    assert any("Invalid meal type" in r for r in reasons)
    assert any("excessively exceeds hostel capacity" in r for r in reasons)


def test_import_register_csv_environment_isolation(mem_session):
    """Verify is_synthetic flag strictly isolates real vs synthetic records."""
    csv_data = """date,meal_type,headcount\n2026-10-06,lunch,380\n"""
    col_map = {"date": "date", "meal_type": "meal_type", "headcount": "headcount"}

    # Import into Real Pilot (is_synthetic=0)
    res_real = import_register_csv(
        mem_session, csv_data, col_map, is_synthetic=0, who="real_admin"
    )
    assert res_real.accepted_rows == 1

    # Verify record in DB has is_synthetic=0
    m_real = mem_session.execute(select(Meal).where(Meal.date == "2026-10-06")).scalars().first()
    assert m_real.is_synthetic == 0

    # Same date & meal in Synthetic Demo (is_synthetic=1) is allowed and distinct
    res_synth = import_register_csv(
        mem_session, csv_data, col_map, is_synthetic=1, who="demo_user"
    )
    assert res_synth.accepted_rows == 1
    m_synth = mem_session.execute(select(Meal).where(Meal.date == "2026-10-06", Meal.is_synthetic == 1)).scalars().first()
    assert m_synth.is_synthetic == 1
    assert m_synth.id != m_real.id
