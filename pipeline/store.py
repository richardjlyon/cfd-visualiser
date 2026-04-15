"""Polars -> DuckDB idempotent upsert (PIPE-03).

Security: uses DuckDB Arrow registration + column-name allowlist (_VALUE_COLS).
No user data is interpolated into SQL strings — T-01-01-02.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl

from pipeline.schema import validate

_VALUE_COLS = [
    "Name_of_CfD_Unit",
    "Technology",
    "Allocation_round",
    "Reference_Type",
    "CFD_Generation_MWh",
    "Avoided_GHG_tonnes_CO2e",
    "CFD_Payments_GBP",
    "Avoided_GHG_Cost_GBP",
    "Strike_Price_GBP_Per_MWh",
    "Market_Reference_Price_GBP_Per_MWh",
    "Weighted_IMRP_GBP_Per_MWh",
]

_DDL = """
CREATE TABLE IF NOT EXISTS raw_generation (
    Settlement_Date DATE NOT NULL,
    CfD_ID VARCHAR NOT NULL,
    Name_of_CfD_Unit VARCHAR,
    Technology VARCHAR,
    Allocation_round VARCHAR,
    Reference_Type VARCHAR,
    CFD_Generation_MWh DOUBLE,
    Avoided_GHG_tonnes_CO2e DOUBLE,
    CFD_Payments_GBP DOUBLE,
    Avoided_GHG_Cost_GBP DOUBLE,
    Strike_Price_GBP_Per_MWh DOUBLE,
    Market_Reference_Price_GBP_Per_MWh DOUBLE,
    Weighted_IMRP_GBP_Per_MWh DOUBLE,
    PRIMARY KEY (Settlement_Date, CfD_ID)
);
"""


def upsert(df: pl.DataFrame, db_path: str | Path) -> int:
    """Validate df and upsert all rows into the raw_generation table.

    Creates the table if it does not exist. On PK conflict
    (Settlement_Date, CfD_ID), updates all value columns to the incoming value.

    Args:
        df: Raw or pre-processed polars DataFrame (may have Settlement_Date as
            string or Date — validate() handles the conversion).
        db_path: Path to the DuckDB file. Will be created if absent.

    Returns:
        Row count of the raw_generation table after the upsert.
    """
    df = validate(df)
    con = duckdb.connect(str(db_path))
    try:
        con.execute(_DDL)
        con.register("incoming", df.to_arrow())
        set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in _VALUE_COLS)
        con.execute(
            f"""
            INSERT INTO raw_generation
            SELECT
                Settlement_Date, CfD_ID,
                Name_of_CfD_Unit, Technology,
                Allocation_round, Reference_Type,
                CFD_Generation_MWh, Avoided_GHG_tonnes_CO2e,
                CFD_Payments_GBP, Avoided_GHG_Cost_GBP,
                Strike_Price_GBP_Per_MWh,
                Market_Reference_Price_GBP_Per_MWh,
                Weighted_IMRP_GBP_Per_MWh
            FROM incoming
            ON CONFLICT (Settlement_Date, CfD_ID) DO UPDATE SET
                {set_clause};
            """
        )
        count = con.execute("SELECT COUNT(*) FROM raw_generation;").fetchone()[0]
        return int(count)
    finally:
        con.close()
