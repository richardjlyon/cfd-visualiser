"""Pandera schema for the LCCC CfD generation CSV (PIPE-02 + PIPE-08).

Enforces:
- strict=True: unknown columns fail validation
- Settlement_Date is polars.Date (not Datetime) — PIPE-08
- Technology, Allocation_round, Reference_Type are enum-constrained
- CfD_ID matches the observed ID format
- CFD_Generation_MWh is non-negative (clawbacks appear in CFD_Payments_GBP, not generation)
- CFD_Payments_GBP is signed (negative during 2022 clawback events)
"""
from __future__ import annotations

import pandera.polars as pa
import polars as pl

# Enum sets: exact values from LCCC dataset (verified by direct inspection of
# data/actual_cfd_generation_and_avoided_ghg_emissions.csv — see 01-RESEARCH.md)
TECHNOLOGIES: frozenset[str] = frozenset(
    {
        "Offshore Wind",
        "Onshore Wind",
        "Solar PV",
        "Biomass Conversion",
        "Energy from Waste",
        "Dedicated Biomass",
        "Advanced Conversion Technology",
    }
)

ROUNDS: frozenset[str] = frozenset(
    {
        "Allocation Round 1",
        "Allocation Round 2",
        "Allocation Round 4",
        "Allocation Round 5",
        "Investment Contract",
    }
)

# Note: AR3 was postponed/cancelled — intentionally absent from this set.

REFERENCE_TYPES: frozenset[str] = frozenset({"IMRP", "BMRP"})

# CfD_ID format: observed prefixes include AAA-, CAA-, AR2-, AR4-, AR5-, INV-
# Regex covers all observed IDs (e.g. CAA-EAS-166, AR2-HRN-306, AAA-K3C-180, INV-HOR-001)
_CFD_ID_RE = r"^[A-Z0-9]{2,4}-[A-Z0-9]{3}-\d+$"

schema: pa.DataFrameSchema = pa.DataFrameSchema(
    {
        "Settlement_Date": pa.Column(
            pl.Date,
            nullable=False,
        ),
        "CfD_ID": pa.Column(
            pl.Utf8,
            nullable=False,
            checks=pa.Check.str_matches(_CFD_ID_RE),
        ),
        "Name_of_CfD_Unit": pa.Column(pl.Utf8, nullable=False),
        "Technology": pa.Column(
            pl.Utf8,
            nullable=False,
            checks=pa.Check.isin(list(TECHNOLOGIES)),
        ),
        "Allocation_round": pa.Column(
            pl.Utf8,
            nullable=False,
            checks=pa.Check.isin(list(ROUNDS)),
        ),
        "Reference_Type": pa.Column(
            pl.Utf8,
            nullable=False,
            checks=pa.Check.isin(list(REFERENCE_TYPES)),
        ),
        "CFD_Generation_MWh": pa.Column(
            pl.Float64,
            nullable=False,
            checks=pa.Check.ge(0),
        ),
        "Avoided_GHG_tonnes_CO2e": pa.Column(pl.Float64, nullable=False),
        "CFD_Payments_GBP": pa.Column(pl.Float64, nullable=False),  # signed — allow negative
        "Avoided_GHG_Cost_GBP": pa.Column(pl.Float64, nullable=False),
        "Strike_Price_GBP_Per_MWh": pa.Column(
            pl.Float64,
            nullable=False,
            checks=pa.Check.gt(0),
        ),
        "Market_Reference_Price_GBP_Per_MWh": pa.Column(pl.Float64, nullable=False),
        "Weighted_IMRP_GBP_Per_MWh": pa.Column(pl.Float64, nullable=True),
    },
    strict=True,
)


def validate(df: pl.DataFrame) -> pl.DataFrame:
    """Validate and return a cleaned DataFrame.

    Converts Settlement_Date from the LCCC timestamp string format
    ('YYYY-MM-DD 00:00:00.0000000') to polars.Date if needed, then runs
    the Pandera schema. Raises pandera.errors.SchemaError on violation.

    Args:
        df: Raw polars DataFrame loaded from the LCCC CSV.

    Returns:
        The same DataFrame with Settlement_Date as pl.Date dtype.
    """
    if df.schema.get("Settlement_Date") != pl.Date:
        df = df.with_columns(
            pl.col("Settlement_Date")
            .str.slice(0, 10)
            .str.to_date("%Y-%m-%d")
            .alias("Settlement_Date")
        )
    return schema.validate(df, lazy=False)
