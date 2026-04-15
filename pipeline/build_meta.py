"""Meta artefact builder: last_updated, versions, captions (EDIT-02).

Writes a JSON object that accompanies each chart page with dataset provenance,
pipeline version, and editorial captions.

Phase 01.1 additions (shock counter, D-09..D-12):
- ytd_subsidy_gbp: cumulative consumer subsidy £ for current calendar year up
  to max_settlement_date (clamped >= 0)
- ytd_as_of: data date the YTD is computed against (= max_settlement_date,
  NOT last_updated build time — mitigates T-01.1-02 stale-data deception)
- gbp_per_sec_rate: rolling-30-data-day mean daily subsidy / 86400s,
  clamped non-negative via SQL GREATEST (mitigates T-01.1-04 clawback DoS),
  rounded to 2 dp
- ytd_label_year: calendar year derived from max_settlement_date (int)

Security: DuckDB connection is read-only; all SQL is either hard-coded or uses
positional `?` parameter binding — no f-string interpolation into SQL
(convention from pipeline/build_chart_3c.py, T-01-04-01 / T-01.1-09).
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import duckdb

SCHEMA_VERSION = "1.1"

# YTD subsidy (D-09): cumulative consumer subsidy for the current calendar year
# up to and including max_settlement_date. Clamped non-negative via COALESCE.
# Parameters: [f"{year}-01-01", max_settlement_date]
_SQL_YTD_SUBSIDY = """
SELECT COALESCE(SUM(CFD_Payments_GBP), 0.0)
FROM raw_generation
WHERE Settlement_Date >= ?
  AND Settlement_Date <= ?
"""

# Rolling 30-day mean daily subsidy -> £/sec rate (D-11). GREATEST clamp
# mitigates clawback-window negatives (RESEARCH §Pitfall 2 — Phase 01.1).
_SQL_RATE = """
WITH daily AS (
  SELECT Settlement_Date AS d, SUM(CFD_Payments_GBP) AS daily_gbp
  FROM raw_generation
  WHERE Settlement_Date > (SELECT MAX(Settlement_Date) FROM raw_generation) - INTERVAL 30 DAY
    AND Settlement_Date <= (SELECT MAX(Settlement_Date) FROM raw_generation)
  GROUP BY 1
)
SELECT GREATEST(COALESCE(AVG(daily_gbp), 0.0) / 86400.0, 0.0) FROM daily
"""


def _git_sha() -> str:
    """Return the current git HEAD short SHA, or 'dev' if unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return out.decode().strip() or "dev"
    except Exception:
        return "dev"


def build(
    db_path: str | Path,
    captions_path: str | Path,
    out_path: str | Path,
    *,
    pipeline_version: str | None = None,
    now_iso: str | None = None,
) -> dict:
    """Build the meta artefact and write it to out_path.

    Args:
        db_path: Path to the DuckDB file (read-only).
        captions_path: Path to the captions JSON file.
        out_path: Destination path for the meta JSON artefact.
        pipeline_version: Explicit version string; defaults to git HEAD SHA or 'dev'.
        now_iso: Explicit ISO-8601 UTC timestamp string; defaults to current UTC time.

    Returns:
        The meta dict written to out_path.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        row_count = con.execute(
            "SELECT COUNT(*) FROM raw_generation"
        ).fetchone()[0]
        max_date = con.execute(
            "SELECT CAST(MAX(Settlement_Date) AS VARCHAR) FROM raw_generation"
        ).fetchone()[0]
        # Derive year from the data date (max_settlement_date), NOT datetime.now().
        # This decouples ytd_label_year from wall-clock time — important for
        # deterministic tests and backdated fixtures; also mitigates T-01.1-02
        # (stale-data deception: if the pipeline builds against an old snapshot,
        # the YTD year must still reflect the data, not the build time).
        year = int(max_date[:4])
        ytd_subsidy = con.execute(
            _SQL_YTD_SUBSIDY,
            [f"{year}-01-01", max_date],
        ).fetchone()[0] or 0.0
        rate_per_sec = con.execute(_SQL_RATE).fetchone()[0] or 0.0
    finally:
        con.close()

    captions = json.loads(Path(captions_path).read_text())

    meta = {
        "captions": captions,
        "last_updated": now_iso or dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "max_settlement_date": max_date,
        "pipeline_version": pipeline_version or _git_sha(),
        "row_count": int(row_count),
        "schema_version": SCHEMA_VERSION,
        # Phase 01.1 — shock counter (D-09..D-12)
        "ytd_subsidy_gbp": float(ytd_subsidy),
        "ytd_as_of": max_date,
        "gbp_per_sec_rate": round(float(rate_per_sec), 2),
        "ytd_label_year": year,
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(
        json.dumps(meta, separators=(",", ":"), sort_keys=True)
    )
    return meta
