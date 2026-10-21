"""MessWise Database Migration Utility.

Safely copies all existing records (including synthetic demo data and genuine operational/pilot data)
from a source SQLite database to a target PostgreSQL database (or other SQLAlchemy-compatible DB).

Key Safety Guarantees:
1. Source database is READ-ONLY and NEVER altered, overwritten, or reset.
2. Preserves all primary keys, foreign keys, timestamps, and data types.
3. Preserves synthetic separation: is_synthetic flags and verification_status are retained exactly.
4. Idempotent: checks for existing records before inserting to avoid duplicates.
5. Prints a detailed reconciliation report comparing source row counts with destination row counts.

Usage:
  python scripts/migrate_to_postgres.py --dest "postgresql://user:pass@host:5432/dbname"
  # Or via environment variable:
  export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
  python scripts/migrate_to_postgres.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Type

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

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
    get_default_db_url,
)

# Ordered models respecting foreign key dependencies
MODELS_IN_ORDER: List[Type[Base]] = [
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
]


def sync_postgres_sequences(engine: Engine, models: List[Type[Base]]) -> List[Dict[str, Any]]:
    """Synchronize PostgreSQL identity sequences for all tables with autoincrement primary keys.

    When records with explicit IDs are inserted, PostgreSQL sequence counters do not advance
    automatically. This function inspects each model's primary key columns from metadata,
    queries pg_get_serial_sequence, and uses setval() to set the sequence counter to MAX(id).
    """
    if engine.dialect.name != "postgresql":
        return []

    sync_results = []
    with engine.connect() as conn:
        for model in models:
            table = model.__table__
            table_name = table.name

            # Identify eligible primary key columns from SQLAlchemy table metadata
            eligible_pks = [
                col for col in table.primary_key.columns
                if col.autoincrement in (True, "auto") or str(col.type).upper().startswith(("INT", "BIGINT", "SMALLINT"))
            ]

            for col in eligible_pks:
                col_name = col.name
                # Query PostgreSQL pg_get_serial_sequence safely
                seq_res = conn.execute(
                    text("SELECT pg_get_serial_sequence(:tbl, :col)"),
                    {"tbl": table_name, "col": col_name},
                ).scalar()

                if not seq_res:
                    sync_results.append({
                        "table": table_name,
                        "column": col_name,
                        "sequence": None,
                        "max_id": None,
                        "status": "unresolved_sequence",
                    })
                    continue

                # Query maximum existing ID safely with quoted identifiers
                max_id = conn.execute(
                    text(f'SELECT MAX("{col_name}") FROM "{table_name}"')
                ).scalar()

                if max_id is not None and max_id > 0:
                    # Populated table: advance sequence to max_id, is_called = true
                    # Next nextval() will return max_id + 1 without collision
                    conn.execute(
                        text("SELECT setval(:seq, :val, true)"),
                        {"seq": seq_res, "val": max_id},
                    )
                    sync_results.append({
                        "table": table_name,
                        "column": col_name,
                        "sequence": seq_res,
                        "max_id": max_id,
                        "status": "synchronized",
                    })
                else:
                    # Empty table: reset sequence to 1, is_called = false
                    # Next nextval() will return 1
                    conn.execute(
                        text("SELECT setval(:seq, 1, false)"),
                        {"seq": seq_res},
                    )
                    sync_results.append({
                        "table": table_name,
                        "column": col_name,
                        "sequence": seq_res,
                        "max_id": None,
                        "status": "synchronized_empty",
                    })

        conn.commit()

    return sync_results


def migrate_data(source_url: str, dest_url: str) -> None:
    print(f"[MessWise Migration] Source: {source_url}")
    print(f"[MessWise Migration] Target: {dest_url}")

    # Normalize destination postgres:// if needed
    if dest_url.startswith("postgres://"):
        dest_url = dest_url.replace("postgres://", "postgresql://", 1)

    source_engine = create_engine(source_url, connect_args={"check_same_thread": False} if "sqlite" in source_url else {})
    dest_engine = create_engine(dest_url, pool_pre_ping=True)

    print("[MessWise Migration] Initializing destination database schema...")
    Base.metadata.create_all(bind=dest_engine)

    SourceSession = sessionmaker(bind=source_engine, autocommit=False, autoflush=False)
    DestSession = sessionmaker(bind=dest_engine, autocommit=False, autoflush=False)

    print("\n" + "=" * 65)
    print(f"{'Table':<25} | {'Source Count':<15} | {'Target Count':<15}")
    print("=" * 65)

    with SourceSession() as src, DestSession() as dst:
        for model in MODELS_IN_ORDER:
            table_name = model.__tablename__
            src_count = src.query(model).count()
            
            if src_count == 0:
                dst_count = dst.query(model).count()
                print(f"{table_name:<25} | {src_count:<15} | {dst_count:<15} (no records to copy)")
                continue

            # Fetch all rows from source
            records = src.query(model).all()
            copied_count = 0

            for rec in records:
                # Check if record already exists in destination
                existing = dst.query(model).filter(model.id == rec.id).first()
                if not existing:
                    # Create clean clone using column attributes
                    col_dict = {c.name: getattr(rec, c.name) for c in model.__table__.columns}
                    new_rec = model(**col_dict)
                    dst.add(new_rec)
                    copied_count += 1

            dst.commit()
            dst_final_count = dst.query(model).count()
            print(f"{table_name:<25} | {src_count:<15} | {dst_final_count:<15} (+{copied_count} migrated)")

    print("=" * 65)

    # If destination is PostgreSQL, synchronize sequence counters to prevent unique constraint collisions
    if dest_engine.dialect.name == "postgresql":
        print("\n[MessWise Migration] Synchronizing PostgreSQL identity sequences...")
        sync_results = sync_postgres_sequences(dest_engine, MODELS_IN_ORDER)
        print("-" * 75)
        print(f"{'Table':<24} | {'Column':<8} | {'Status':<22} | {'Max ID'}")
        print("-" * 75)
        for r in sync_results:
            max_id_str = str(r['max_id']) if r['max_id'] is not None else "(empty)"
            print(f"{r['table']:<24} | {r['column']:<8} | {r['status']:<22} | {max_id_str}")
        print("-" * 75)

    print("[MessWise Migration] Migration completed successfully. Source data intact.\n")


def main():
    parser = argparse.ArgumentParser(description="MessWise Safe SQLite to PostgreSQL Migration")
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Source SQLite database URL (defaults to local data/messwise.db)",
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=None,
        help="Target database URL (or set DATABASE_URL environment variable)",
    )
    args = parser.parse_args()

    default_sqlite_path = Path(__file__).resolve().parent.parent / "data" / "messwise.db"
    source = args.source or f"sqlite:///{default_sqlite_path}"
    dest = args.dest or os.getenv("DATABASE_URL")

    if not dest:
        print("[ERROR] No destination database URL provided.")
        print("Please specify --dest <url> or set the DATABASE_URL environment variable.")
        print("Example: python scripts/migrate_to_postgres.py --dest postgresql://user:pass@host:5432/dbname")
        sys.exit(1)

    if source == dest:
        print("[ERROR] Source and destination URLs are identical. Aborting to avoid data corruption.")
        sys.exit(1)

    migrate_data(source_url=source, dest_url=dest)


if __name__ == "__main__":
    main()
