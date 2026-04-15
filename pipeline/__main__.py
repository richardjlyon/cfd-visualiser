"""CLI entry: fetch -> validate -> store -> build_chart_3c -> build_meta -> og_image -> chart_pngs -> healthcheck.

Exit codes:
- 0  OK
- 1  fetch failed (network, HTML response, truncated body)
- 2  schema drift (Pandera SchemaError — does NOT write to DuckDB)
- 3  store failed (DuckDB write error)
- 4  healthcheck ping failed (store completed successfully)
- 5  chart/meta build failed
- 7  og-image build failed (best-effort; store + chart already succeeded)
- 8  per-chart PNG export failed (D-13..D-16; previous PNGs retained on disk
     byte-for-byte because Step 2 schema-drift returns BEFORE this step)

Environment variables:
- PIPELINE_HC_URL (optional): Healthchecks.io ping URL; silent skip if unset.
- PIPELINE_LATEST_CSV (optional): Override path for the downloaded CSV (default: data/latest.csv).
- PIPELINE_RAW_DIR (optional): Override path for the raw gzip archive dir (default: data/raw).
- PIPELINE_DB_PATH (optional): Override path for the DuckDB file (default: data/cfd.duckdb).
- PIPELINE_CHART_ASSETS_DIR (optional): Override output dir for per-chart
  download PNGs (default: src/assets/charts).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
import pandera.errors

from pipeline.fetch import fetch
from pipeline.validate import read_and_validate
from pipeline.store import upsert
from pipeline.build_chart_3c import build as build_chart_3c
from pipeline.build_meta import build as build_meta
from pipeline.build_og_image import build as build_og
from pipeline.export_chart_images import build_all as build_chart_images

EXIT_OK = 0
EXIT_FETCH_FAILED = 1
EXIT_SCHEMA_DRIFT = 2
EXIT_STORE_FAILED = 3
EXIT_HEALTHCHECK_FAILED = 4
EXIT_CHART_BUILD_FAILED = 5
EXIT_OG_FAILED = 7
EXIT_IMAGE_EXPORT_FAILED = 8


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

    # Step 4: Build chart view-model and meta artefacts
    try:
        build_chart_3c(db_path, Path("src/data/chart-3c.json"))
        build_meta(
            db_path,
            Path("src/content/captions.json"),
            Path("src/data/meta.json"),
        )
        print("ok: chart-3c.json and meta.json built")
    except Exception as e:
        print(f"ERROR: chart/meta build failed: {e}", file=sys.stderr)
        return EXIT_CHART_BUILD_FAILED

    # Step 5: Build OG card (best-effort — does not block healthcheck)
    try:
        build_og(Path("src/data/chart-3c.json"), Path("src/assets/og-card.png"))
        print("ok: og-card.png built")
    except Exception as e:
        print(f"WARN: og-card build failed: {e}", file=sys.stderr)
        return EXIT_OG_FAILED

    # Step 5b: Per-chart download PNGs (Phase 01.1 D-13..D-16)
    #
    # Schema-drift retention (T-01.1-04): Step 2 returns EXIT_SCHEMA_DRIFT
    # before reaching here, so on a drift run this block never executes and
    # any previously-deployed PNGs on disk remain byte-identical. No
    # explicit guard needed — the guarantee is structural.
    #
    # max_date is read back from the meta.json artefact written by Step 4
    # above (single local-file read; avoids changing build_meta's API).
    try:
        chart_assets_dir = Path(
            os.environ.get("PIPELINE_CHART_ASSETS_DIR", "src/assets/charts")
        )
        captions_path = Path("src/content/captions.json")
        captions = json.loads(captions_path.read_text())
        meta = json.loads(Path("src/data/meta.json").read_text())
        max_date = meta.get("max_settlement_date", "")
        build_chart_images(
            chart_assets_dir,
            chart_json=Path("src/data/chart-3c.json"),
            build_date=max_date,
            captions=captions,
        )
        print("ok: per-chart PNGs built")
    except Exception as e:
        print(f"ERROR: per-chart PNG build failed: {e}", file=sys.stderr)
        return EXIT_IMAGE_EXPORT_FAILED

    # Step 6: Healthcheck ping (optional)
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
