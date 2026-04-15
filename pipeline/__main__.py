"""CLI entry: fetch -> validate -> store -> healthcheck (PIPE-01..05).

Exit codes:
- 0  OK
- 1  fetch failed (network, HTML response, truncated body)
- 2  schema drift (Pandera SchemaError — does NOT write to DuckDB)
- 3  store failed (DuckDB write error)
- 4  healthcheck ping failed (store completed successfully)

Environment variables:
- PIPELINE_HC_URL (optional): Healthchecks.io ping URL; silent skip if unset.
- PIPELINE_LATEST_CSV (optional): Override path for the downloaded CSV (default: data/latest.csv).
- PIPELINE_RAW_DIR (optional): Override path for the raw gzip archive dir (default: data/raw).
- PIPELINE_DB_PATH (optional): Override path for the DuckDB file (default: data/cfd.duckdb).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pandera.errors

from pipeline.fetch import fetch
from pipeline.validate import read_and_validate
from pipeline.store import upsert

EXIT_OK = 0
EXIT_FETCH_FAILED = 1
EXIT_SCHEMA_DRIFT = 2
EXIT_STORE_FAILED = 3
EXIT_HEALTHCHECK_FAILED = 4


def run(
    *,
    latest_csv: Path = Path("data/latest.csv"),
    raw_dir: Path = Path("data/raw"),
    db_path: Path = Path("data/cfd.duckdb"),
    client: httpx.Client | None = None,
    hc_url: str | None = None,
) -> int:
    """Run the full pipeline: fetch -> validate -> store -> healthcheck.

    Args:
        latest_csv: Destination for the downloaded CSV.
        raw_dir: Directory for gzipped date-stamped snapshots.
        db_path: Path to the DuckDB file.
        client: Optional httpx.Client for testing injection.
        hc_url: Healthchecks ping URL. Falls back to PIPELINE_HC_URL env var.
                If neither is set, healthcheck step is skipped.

    Returns:
        Exit code (0 = success, 1-4 = failure — see module docstring).
    """
    hc_url = hc_url if hc_url is not None else os.environ.get("PIPELINE_HC_URL")

    # Step 1: Fetch
    try:
        fetch(latest_csv, raw_dir, client=client)
    except Exception as e:
        print(f"ERROR: fetch failed: {e}", file=sys.stderr)
        return EXIT_FETCH_FAILED

    # Step 2: Validate (schema drift halts before any DuckDB write)
    try:
        df = read_and_validate(latest_csv)
    except pandera.errors.SchemaError as e:
        print(f"ERROR: schema drift detected: {e}", file=sys.stderr)
        return EXIT_SCHEMA_DRIFT

    # Step 3: Store
    try:
        rows = upsert(df, db_path)
        print(f"ok: {rows} rows in raw_generation")
    except Exception as e:
        print(f"ERROR: store failed: {e}", file=sys.stderr)
        return EXIT_STORE_FAILED

    # Step 4: Healthcheck ping (optional)
    if hc_url:
        try:
            # Re-use injected client for tests; fall back to a simple one-shot GET
            if client is not None:
                client.get(hc_url, timeout=10.0).raise_for_status()
            else:
                httpx.get(hc_url, timeout=10.0).raise_for_status()
            print(f"ok: healthcheck pinged {hc_url}")
        except Exception as e:
            print(f"WARN: healthcheck ping failed: {e}", file=sys.stderr)
            return EXIT_HEALTHCHECK_FAILED

    return EXIT_OK


if __name__ == "__main__":
    # Support env-var overrides for the data paths
    latest_csv = Path(os.environ.get("PIPELINE_LATEST_CSV", "data/latest.csv"))
    raw_dir = Path(os.environ.get("PIPELINE_RAW_DIR", "data/raw"))
    db_path = Path(os.environ.get("PIPELINE_DB_PATH", "data/cfd.duckdb"))
    sys.exit(run(latest_csv=latest_csv, raw_dir=raw_dir, db_path=db_path))
