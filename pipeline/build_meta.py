"""Meta artefact builder: last_updated, versions, captions (EDIT-02).

Writes a JSON object that accompanies each chart page with dataset provenance,
pipeline version, and editorial captions.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import duckdb

SCHEMA_VERSION = "1.0"


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
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(
        json.dumps(meta, separators=(",", ":"), sort_keys=True)
    )
    return meta
