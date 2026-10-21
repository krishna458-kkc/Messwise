"""Tests for MessWise Database Migration Safety and Sequence Synchronization.

Verifies:
1. PostgreSQL sequence synchronization helper correctly handles dialects,
   identifies primary key metadata across all registered ORM models,
   and handles empty and populated tables.
2. AUTO_SEED_SYNTHETIC environment variable robust parsing ('false', '0', 'no', 'off').
3. Model metadata autoincrement integer PK discovery.
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from api.main import _is_auto_seed_enabled
from messwise.db import (
    Base,
    Dish,
    Meal,
    DishLog,
    Prediction,
    Override,
    AuditLog,
    SurplusEvent,
    EntranceTally,
    Recipe,
    RecipeIngredient,
    init_db,
)
from scripts.migrate_to_postgres import MODELS_IN_ORDER, sync_postgres_sequences


def test_auto_seed_enabled_defaults_to_true():
    """Verify auto-seeding defaults to True when env var is not set."""
    with patch.dict(os.environ, {}, clear=True):
        assert _is_auto_seed_enabled() is True


@pytest.mark.parametrize("falsy_val", ["false", "FALSE", "0", "no", "No", "off", "OFF", " false "])
def test_auto_seed_disabled_by_falsy_env_vars(falsy_val):
    """Verify auto-seeding disables on false, 0, no, off."""
    with patch.dict(os.environ, {"AUTO_SEED_SYNTHETIC": falsy_val}):
        assert _is_auto_seed_enabled() is False


@pytest.mark.parametrize("truthy_val", ["true", "TRUE", "1", "yes", "on", ""])
def test_auto_seed_enabled_by_truthy_env_vars(truthy_val):
    """Verify auto-seeding remains enabled for standard truthy inputs."""
    with patch.dict(os.environ, {"AUTO_SEED_SYNTHETIC": truthy_val}):
        assert _is_auto_seed_enabled() is True


def test_sync_postgres_sequences_skips_sqlite():
    """Verify sequence synchronization returns empty list when engine is SQLite."""
    sqlite_engine = create_engine("sqlite:///:memory:")
    init_db(sqlite_engine)
    results = sync_postgres_sequences(sqlite_engine, MODELS_IN_ORDER)
    assert results == []


def test_models_metadata_has_integer_autoincrement_pks():
    """Verify every migration model has an identifiable integer primary key."""
    for model in MODELS_IN_ORDER:
        table = model.__table__
        pk_cols = [
            c for c in table.primary_key.columns
            if c.autoincrement in (True, "auto") or str(c.type).upper().startswith(("INT", "BIGINT", "SMALLINT"))
        ]
        assert len(pk_cols) >= 1, f"Model {model.__name__} has no eligible integer PK"
        assert pk_cols[0].name == "id"


def test_postgres_sequence_sync_query_generation():
    """Test PostgreSQL sequence synchronization query logic against a simulated Postgres connection."""
    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    # Mock sequence resolution: returns sequence name for 'meals', None for others
    def mock_execute(sql, params=None):
        sql_str = str(sql)
        mock_result = MagicMock()
        if "pg_get_serial_sequence" in sql_str:
            if params and params.get("tbl") == "meals":
                mock_result.scalar.return_value = "public.meals_id_seq"
            else:
                mock_result.scalar.return_value = None
        elif "SELECT MAX" in sql_str:
            mock_result.scalar.return_value = 33
        return mock_result

    mock_conn.execute.side_effect = mock_execute

    results = sync_postgres_sequences(mock_engine, [Meal, Override])
    assert len(results) == 2

    # Check meals was synchronized with max_id 33
    meals_res = next(r for r in results if r["table"] == "meals")
    assert meals_res["status"] == "synchronized"
    assert meals_res["max_id"] == 33
    assert meals_res["sequence"] == "public.meals_id_seq"

    # Check override without sequence was safely marked as unresolved_sequence
    override_res = next(r for r in results if r["table"] == "overrides")
    assert override_res["status"] == "unresolved_sequence"
    assert override_res["sequence"] is None
