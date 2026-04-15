"""Tests for pipeline/schema.py — PIPE-02 (Pandera schema) and PIPE-08 (date-only)."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pandera.errors
import pytest

from pipeline.schema import validate, TECHNOLOGIES, ROUNDS, REFERENCE_TYPES


def _load_valid(sample_csv_path: Path) -> pl.DataFrame:
    """Load fixture and convert Settlement_Date so it's ready for validate()."""
    return pl.read_csv(sample_csv_path).with_columns(
        pl.col("Settlement_Date")
        .str.slice(0, 10)
        .str.to_date("%Y-%m-%d")
        .alias("Settlement_Date")
    )


def test_valid_accepts(sample_csv_path: Path) -> None:
    """A clean fixture DataFrame passes validation and is returned unchanged."""
    df = _load_valid(sample_csv_path)
    result = validate(df)
    assert result.shape == df.shape
    assert result["Settlement_Date"].dtype == pl.Date


def test_extra_column_fails(sample_csv_path: Path) -> None:
    """strict=True: adding an extra column raises SchemaError."""
    df = _load_valid(sample_csv_path).with_columns(
        pl.lit("bad").alias("Foo")
    )
    with pytest.raises(pandera.errors.SchemaError):
        validate(df)


def test_column_rename_fails(sample_csv_path: Path) -> None:
    """Renaming Technology to technology (wrong case) raises SchemaError."""
    df = _load_valid(sample_csv_path).rename({"Technology": "technology"})
    with pytest.raises(pandera.errors.SchemaError):
        validate(df)


def test_unknown_technology_fails(sample_csv_path: Path) -> None:
    """A row with Technology='Wind' (not in enum set) raises SchemaError."""
    df = _load_valid(sample_csv_path)
    # Replace first row's Technology with an unknown value
    bad = df.with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(pl.lit("Wind"))
        .otherwise(pl.col("Technology"))
        .alias("Technology")
    )
    with pytest.raises(pandera.errors.SchemaError):
        validate(bad)


def test_unknown_reference_type_fails(sample_csv_path: Path) -> None:
    """A row with Reference_Type='XYZ' raises SchemaError."""
    df = _load_valid(sample_csv_path)
    bad = df.with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(pl.lit("XYZ"))
        .otherwise(pl.col("Reference_Type"))
        .alias("Reference_Type")
    )
    with pytest.raises(pandera.errors.SchemaError):
        validate(bad)


def test_date_only_no_time(sample_csv_path: Path) -> None:
    """After validation, Settlement_Date dtype is pl.Date (not Datetime) — PIPE-08."""
    df = pl.read_csv(sample_csv_path)  # raw, still a string column
    result = validate(df)
    assert result["Settlement_Date"].dtype == pl.Date
    # Confirm no Datetime dtype
    assert result["Settlement_Date"].dtype != pl.Datetime


def test_negative_generation_fails(sample_csv_path: Path) -> None:
    """A row with CFD_Generation_MWh < 0 raises SchemaError."""
    df = _load_valid(sample_csv_path)
    bad = df.with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(pl.lit(-1.0))
        .otherwise(pl.col("CFD_Generation_MWh"))
        .alias("CFD_Generation_MWh")
    )
    with pytest.raises(pandera.errors.SchemaError):
        validate(bad)


def test_negative_payments_accepted(sample_csv_path: Path) -> None:
    """CFD_Payments_GBP accepts negative values (clawback) without raising."""
    df = _load_valid(sample_csv_path)
    # Fixture already has negative payment rows from the 2022 clawback
    has_negative = (df["CFD_Payments_GBP"] < 0).any()
    assert has_negative, "Fixture should contain negative payment rows"
    # Full validation must succeed despite negatives
    result = validate(df)
    assert result.shape == df.shape


def test_cfd_id_name_one_to_one(sample_csv_path: Path) -> None:
    """CfD_ID <-> Name_of_CfD_Unit mapping is 1:1 on the committed fixture.

    Resolves RESEARCH Open Q2: confirms each CfD_ID has exactly one unit name.
    """
    df = pl.read_csv(sample_csv_path)
    # Count distinct Name_of_CfD_Unit per CfD_ID
    names_per_id = (
        df.select(["CfD_ID", "Name_of_CfD_Unit"])
        .unique()
        .group_by("CfD_ID")
        .len()
    )
    multi_name_ids = names_per_id.filter(pl.col("len") > 1)
    assert len(multi_name_ids) == 0, (
        f"CfD_IDs with multiple names: {multi_name_ids.to_dicts()}"
    )

    # Reverse: count distinct CfD_ID per Name_of_CfD_Unit
    ids_per_name = (
        df.select(["CfD_ID", "Name_of_CfD_Unit"])
        .unique()
        .group_by("Name_of_CfD_Unit")
        .len()
    )
    multi_id_names = ids_per_name.filter(pl.col("len") > 1)
    assert len(multi_id_names) == 0, (
        f"Names with multiple CfD_IDs: {multi_id_names.to_dicts()}"
    )
