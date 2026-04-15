"""Read LCCC CSV and apply Pandera schema (PIPE-02, PIPE-08).

Timezone convention: Settlement_Date is treated as UTC-naive date-only.
The raw CSV uses `YYYY-MM-DD 00:00:00.0000000` timestamp literals; we
slice to the first 10 characters and parse as polars.Date. No time
component survives this function.
"""
from __future__ import annotations

from pathlib import Path

import polars as pl

from pipeline.schema import validate as _schema_validate


def read_and_validate(csv_path: Path) -> pl.DataFrame:
    """Read a LCCC CSV file and validate it against the Pandera schema.

    Settlement_Date is coerced to polars.Date (UTC-naive, date-only) before
    schema validation. The input file is never modified.

    Args:
        csv_path: Path to the LCCC CSV file.

    Returns:
        A validated polars.DataFrame with 13 columns and Settlement_Date as
        polars.Date dtype.

    Raises:
        pandera.errors.SchemaError: If the CSV does not conform to the schema
            (unknown columns, missing columns, invalid enum values, etc.).
    """
    df = pl.read_csv(csv_path, infer_schema_length=10_000)
    if df.schema.get("Settlement_Date") != pl.Date:
        df = df.with_columns(
            pl.col("Settlement_Date")
            .str.slice(0, 10)
            .str.to_date("%Y-%m-%d")
        )
    return _schema_validate(df)
