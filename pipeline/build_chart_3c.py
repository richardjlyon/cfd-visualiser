"""CHART-01 scissors view-model builder (CHART-01).

Security: uses a read-only DuckDB connection; SQL is hard-coded with no
user/environment data interpolation (T-01-04-01).
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

_SQL = """
SELECT
    strftime('%Y-%m', Settlement_Date) AS month,
    Allocation_round AS round,
    SUM(CFD_Generation_MWh) AS generation_mwh,
    SUM(Strike_Price_GBP_Per_MWh * CFD_Generation_MWh)
      / NULLIF(SUM(CFD_Generation_MWh), 0) AS strike,
    SUM(Market_Reference_Price_GBP_Per_MWh * CFD_Generation_MWh)
      / NULLIF(SUM(CFD_Generation_MWh), 0) AS market,
    SUM(CFD_Payments_GBP) AS payments_gbp
FROM raw_generation
WHERE Reference_Type = 'IMRP'
GROUP BY 1, 2
HAVING SUM(CFD_Generation_MWh) > 0
ORDER BY 1, 2;
"""


def build(db_path: str | Path, out_path: str | Path) -> list[dict]:
    """Read raw_generation, filter to Reference_Type='IMRP',
    compute generation-weighted monthly aggregates per allocation round,
    write view-model JSON to out_path, return the list written.

    Args:
        db_path: Path to the DuckDB file (read-only).
        out_path: Destination path for the JSON artefact.

    Returns:
        The list of view-model records written to out_path.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(_SQL).fetchall()
    finally:
        con.close()

    cols = ["month", "round", "generation_mwh", "strike", "market", "payments_gbp"]
    view_model = [
        {c: (float(v) if isinstance(v, (int, float)) else v) for c, v in zip(cols, r)}
        for r in rows
    ]

    # Round numeric fields to 6 dp to stabilise golden fixture
    for rec in view_model:
        for k in ("generation_mwh", "strike", "market", "payments_gbp"):
            rec[k] = round(rec[k], 6)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(
        json.dumps(view_model, separators=(",", ":"), sort_keys=True)
    )
    return view_model
