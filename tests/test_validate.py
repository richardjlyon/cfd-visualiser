"""Tests for pipeline/validate.py (PIPE-02, PIPE-08).

Covers:
- Valid CSV returns polars.DataFrame with 13 columns
- Settlement_Date is polars.Date dtype (not Datetime, not Utf8) — PIPE-08
- Extra column in CSV raises pandera.errors.SchemaError (strict=True)
- Unknown Technology value raises pandera.errors.SchemaError
- Missing CfD_ID column raises schema error
- Input file is not mutated by read_and_validate
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandera.errors
import polars as pl
import pytest


def test_valid_csv_returns_dataframe(sample_csv_path: Path) -> None:
    from pipeline.validate import read_and_validate

    df = read_and_validate(sample_csv_path)
    assert isinstance(df, pl.DataFrame)
    assert df.width == 13


def test_settlement_date_is_polars_date(sample_csv_path: Path) -> None:
    from pipeline.validate import read_and_validate

    df = read_and_validate(sample_csv_path)
    assert df["Settlement_Date"].dtype == pl.Date, (
        f"Expected pl.Date, got {df['Settlement_Date'].dtype}"
    )


def test_extra_column_fails(tmp_path: Path, sample_csv_path: Path) -> None:
    """CSV with an extra column should raise SchemaError (strict=True)."""
    from pipeline.validate import read_and_validate

    # Read the fixture CSV and add an extra column
    df = pl.read_csv(sample_csv_path)
    df_extra = df.with_columns(pl.lit(99).alias("Foo"))
    extra_csv = tmp_path / "extra_col.csv"
    df_extra.write_csv(extra_csv)

    with pytest.raises(pandera.errors.SchemaError):
        read_and_validate(extra_csv)


def test_unknown_technology_fails(tmp_path: Path, sample_csv_path: Path) -> None:
    """CSV with an unrecognised Technology value should raise SchemaError."""
    from pipeline.validate import read_and_validate

    df = pl.read_csv(sample_csv_path)
    # Mutate the first row's Technology to an unknown value
    bad_tech = df.with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(pl.lit("UnknownTech"))
        .otherwise(pl.col("Technology"))
        .alias("Technology")
    )
    bad_csv = tmp_path / "bad_tech.csv"
    bad_tech.write_csv(bad_csv)

    with pytest.raises(pandera.errors.SchemaError):
        read_and_validate(bad_csv)


def test_missing_column_fails(tmp_path: Path, sample_csv_path: Path) -> None:
    """CSV without CfD_ID column should raise a schema error."""
    from pipeline.validate import read_and_validate

    df = pl.read_csv(sample_csv_path)
    df_no_id = df.drop("CfD_ID")
    no_id_csv = tmp_path / "no_id.csv"
    df_no_id.write_csv(no_id_csv)

    with pytest.raises((pandera.errors.SchemaError, Exception)):
        read_and_validate(no_id_csv)


def test_file_not_mutated(sample_csv_path: Path) -> None:
    """read_and_validate must not modify the input CSV file."""
    from pipeline.validate import read_and_validate

    original_hash = hashlib.sha256(sample_csv_path.read_bytes()).hexdigest()
    read_and_validate(sample_csv_path)
    after_hash = hashlib.sha256(sample_csv_path.read_bytes()).hexdigest()
    assert original_hash == after_hash, "read_and_validate mutated the input file"
