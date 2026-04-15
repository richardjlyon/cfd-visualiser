"""Tests for pipeline/units.py — PIPE-07 unit constant correctness."""
from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from pipeline.units import (
    GBP,
    GBP_BN,
    GBP_M,
    GBP_PER_MWH,
    GWH,
    MWH,
    MWH_PER_GWH,
    TCO2E,
    gbp_to_billions,
    gbp_to_millions,
    millions_to_gbp,
    mwh_to_gwh,
)

# Reference constant: sum of CFD_Generation_MWh for year 2026 in cfd_sample.csv.
# Computed once from the committed fixture; used to assert stable round-trip.
# (Fixture is biased toward 2026 data — only 1 row exists for 2023.)
EXPECTED_2026_MWH: float = 2665955.9839999997
TOLERANCE: float = 0.0001  # ±0.01%


def test_gbp_to_millions() -> None:
    """£1,000,000 = 1.0 £m exactly."""
    assert gbp_to_millions(1_000_000) == 1.0
    assert gbp_to_millions(0) == 0.0
    assert gbp_to_millions(2_500_000) == 2.5


def test_gbp_to_billions() -> None:
    """£1,500,000,000 = 1.5 £bn exactly."""
    assert gbp_to_billions(1_500_000_000) == 1.5
    assert gbp_to_billions(0) == 0.0
    assert gbp_to_billions(1_000_000_000) == 1.0


def test_mwh_to_gwh() -> None:
    """2500 MWh = 2.5 GWh exactly."""
    assert mwh_to_gwh(2500) == 2.5
    assert mwh_to_gwh(0) == 0.0
    assert mwh_to_gwh(1_000) == 1.0


def test_round_trip_gbp_millions() -> None:
    """gbp_to_millions → millions_to_gbp round-trip for various values."""
    for x in [0.0, 1.0, 123.456, 1e9]:
        result = millions_to_gbp(gbp_to_millions(x))
        assert abs(result - x) < 1e-6, f"Round-trip failed for {x}: got {result}"


def test_scale_factor_constants() -> None:
    """Scale factor constants have expected numeric values."""
    assert GBP_M == 1_000_000.0
    assert GBP_BN == 1_000_000_000.0
    assert MWH_PER_GWH == 1_000.0


def test_string_label_constants() -> None:
    """String label constants are non-empty strings."""
    for label in [GBP, GBP_PER_MWH, MWH, GWH, TCO2E]:
        assert isinstance(label, str)
        assert len(label) > 0


def test_2026_total_generation_gwh_matches_reference(sample_csv_path: Path) -> None:
    """Sum of 2026 CFD_Generation_MWh in fixture matches committed reference constant.

    Uses 2026 as the reference year because the stratified sample is biased toward
    recent dates (100 rows per technology/round combination, sorted descending by date),
    giving ~978 rows in 2026 vs only 1 row in 2023.
    """
    df = pl.read_csv(sample_csv_path).with_columns(
        pl.col("Settlement_Date")
        .str.slice(0, 10)
        .str.to_date("%Y-%m-%d")
        .alias("Settlement_Date")
    )
    total_mwh = df.filter(pl.col("Settlement_Date").dt.year() == 2026)[
        "CFD_Generation_MWh"
    ].sum()
    assert total_mwh > 0, "No 2026 data found in fixture"

    # Verify the MWh total matches reference within ±0.01%
    rel_error = abs(total_mwh - EXPECTED_2026_MWH) / EXPECTED_2026_MWH
    assert rel_error <= TOLERANCE, (
        f"2026 MWh total {total_mwh} differs from reference {EXPECTED_2026_MWH} "
        f"by {rel_error:.4%} (tolerance {TOLERANCE:.4%})"
    )

    # Verify GWh conversion is consistent
    total_gwh = mwh_to_gwh(total_mwh)
    assert abs(total_gwh - EXPECTED_2026_MWH / MWH_PER_GWH) < 1e-6
