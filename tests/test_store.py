"""Tests for pipeline/store.py — idempotent DuckDB upsert (PIPE-03)."""
from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl
import pytest

from pipeline.store import upsert


def _load(sample_csv_path: Path) -> pl.DataFrame:
    """Load fixture as raw DataFrame (string Settlement_Date)."""
    return pl.read_csv(sample_csv_path)


def test_creates_table_first_call(fresh_duckdb: Path, sample_csv_path: Path) -> None:
    """upsert() creates raw_generation table with 13 columns on first call."""
    df = _load(sample_csv_path)
    upsert(df, fresh_duckdb)

    con = duckdb.connect(str(fresh_duckdb))
    try:
        tables = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'raw_generation';"
        ).fetchall()
        assert len(tables) == 1, "raw_generation table not found"

        col_info = con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'raw_generation' ORDER BY ordinal_position;"
        ).fetchall()
        assert len(col_info) == 13, f"Expected 13 columns, got {len(col_info)}"
    finally:
        con.close()


def test_idempotent(fresh_duckdb: Path, sample_csv_path: Path) -> None:
    """Running upsert twice produces an identical table (same aggregates)."""
    df = _load(sample_csv_path)

    upsert(df, fresh_duckdb)
    con = duckdb.connect(str(fresh_duckdb))
    try:
        row1 = con.execute(
            "SELECT COUNT(*), SUM(CFD_Generation_MWh), SUM(CFD_Payments_GBP) "
            "FROM raw_generation;"
        ).fetchone()
    finally:
        con.close()

    upsert(df, fresh_duckdb)
    con = duckdb.connect(str(fresh_duckdb))
    try:
        row2 = con.execute(
            "SELECT COUNT(*), SUM(CFD_Generation_MWh), SUM(CFD_Payments_GBP) "
            "FROM raw_generation;"
        ).fetchone()
    finally:
        con.close()

    assert row1 == row2, f"Upsert not idempotent: {row1} != {row2}"
    assert row1[0] > 0, "Table is empty after upsert"


def test_update_on_conflict(fresh_duckdb: Path, sample_csv_path: Path) -> None:
    """ON CONFLICT: second upsert with modified value updates the stored row."""
    df = _load(sample_csv_path).with_columns(
        pl.col("Settlement_Date").str.slice(0, 10).str.to_date("%Y-%m-%d")
    )
    upsert(df, fresh_duckdb)

    # Pick the first row's PK
    first_row = df.row(0, named=True)
    target_date = first_row["Settlement_Date"]
    target_id = first_row["CfD_ID"]
    original_mwh = first_row["CFD_Generation_MWh"]

    # Modify that row's CFD_Generation_MWh
    new_mwh = original_mwh + 999.0
    modified = df.with_columns(
        pl.when(
            (pl.col("Settlement_Date") == target_date)
            & (pl.col("CfD_ID") == target_id)
        )
        .then(pl.lit(new_mwh))
        .otherwise(pl.col("CFD_Generation_MWh"))
        .alias("CFD_Generation_MWh")
    )

    upsert(modified, fresh_duckdb)

    con = duckdb.connect(str(fresh_duckdb))
    try:
        stored = con.execute(
            "SELECT CFD_Generation_MWh FROM raw_generation "
            "WHERE Settlement_Date = ? AND CfD_ID = ?;",
            [target_date, target_id],
        ).fetchone()
    finally:
        con.close()

    assert stored is not None, "Row not found after update"
    assert abs(stored[0] - new_mwh) < 1e-6, (
        f"Expected {new_mwh}, got {stored[0]}"
    )


def test_settlement_date_is_date_type(fresh_duckdb: Path, sample_csv_path: Path) -> None:
    """Settlement_Date column in DuckDB has SQL type DATE (not TIMESTAMP)."""
    df = _load(sample_csv_path)
    upsert(df, fresh_duckdb)

    con = duckdb.connect(str(fresh_duckdb))
    try:
        col_type = con.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'raw_generation' "
            "AND column_name = 'Settlement_Date';"
        ).fetchone()
    finally:
        con.close()

    assert col_type is not None
    assert col_type[0].upper() == "DATE", (
        f"Expected DATE, got {col_type[0]}"
    )


def test_returns_row_count(fresh_duckdb: Path, sample_csv_path: Path) -> None:
    """upsert() return value equals SELECT COUNT(*) FROM raw_generation."""
    df = _load(sample_csv_path)
    returned_count = upsert(df, fresh_duckdb)

    con = duckdb.connect(str(fresh_duckdb))
    try:
        actual_count = con.execute(
            "SELECT COUNT(*) FROM raw_generation;"
        ).fetchone()[0]
    finally:
        con.close()

    assert returned_count == actual_count
    assert returned_count > 0
