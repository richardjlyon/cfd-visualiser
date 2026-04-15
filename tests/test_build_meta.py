"""Tests for pipeline/build_meta.py (meta artefact builder).

TDD RED phase: tests must fail before build_meta.py exists.
"""
from __future__ import annotations

import json
import re
import sys
import unittest.mock as mock
from pathlib import Path

import pytest

from pipeline.validate import read_and_validate
from pipeline.store import upsert


FIXTURES = Path(__file__).parent / "fixtures"
CAPTIONS_PATH = Path("src/content/captions.json")


def _seed_db(tmp_path: Path, sample_csv_path: Path) -> Path:
    db_path = tmp_path / "test.duckdb"
    df = read_and_validate(sample_csv_path)
    upsert(df, db_path)
    return db_path


@pytest.fixture
def seeded_db(tmp_path: Path, sample_csv_path: Path) -> Path:
    return _seed_db(tmp_path, sample_csv_path)


@pytest.fixture
def meta_output(seeded_db: Path, tmp_path: Path) -> dict:
    """Build meta and return the dict."""
    from pipeline.build_meta import build  # noqa: PLC0415
    out = tmp_path / "meta.json"
    result = build(
        seeded_db,
        CAPTIONS_PATH,
        out,
        pipeline_version="test-abc1234",
        now_iso="2026-04-15T06:30:00Z",
    )
    return result


# ── tests ─────────────────────────────────────────────────────────────────────

def test_meta_keys_present(meta_output: dict) -> None:
    """All 6 required keys are present in the meta output."""
    required = {"last_updated", "row_count", "max_settlement_date",
                "pipeline_version", "schema_version", "captions"}
    assert required == set(meta_output.keys()), (
        f"Key mismatch. Got: {set(meta_output.keys())}"
    )


def test_last_updated_iso_z(meta_output: dict) -> None:
    """last_updated matches ISO-8601 UTC format ending in Z."""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    assert pattern.match(meta_output["last_updated"]), (
        f"Bad last_updated format: {meta_output['last_updated']!r}"
    )


def test_row_count_matches_db(seeded_db: Path, tmp_path: Path) -> None:
    """row_count equals SELECT COUNT(*) FROM raw_generation."""
    import duckdb  # noqa: PLC0415
    from pipeline.build_meta import build  # noqa: PLC0415

    out = tmp_path / "meta.json"
    meta = build(seeded_db, CAPTIONS_PATH, out,
                 pipeline_version="test", now_iso="2026-04-15T06:30:00Z")

    con = duckdb.connect(str(seeded_db), read_only=True)
    try:
        expected = con.execute("SELECT COUNT(*) FROM raw_generation").fetchone()[0]
    finally:
        con.close()

    assert meta["row_count"] == expected, (
        f"row_count {meta['row_count']} != db count {expected}"
    )


def test_max_settlement_date_format(meta_output: dict) -> None:
    """max_settlement_date matches YYYY-MM-DD format."""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    assert pattern.match(meta_output["max_settlement_date"]), (
        f"Bad max_settlement_date format: {meta_output['max_settlement_date']!r}"
    )


def test_schema_version_literal(meta_output: dict) -> None:
    """schema_version is exactly the string '1.0'."""
    assert meta_output["schema_version"] == "1.0"


def test_captions_deep_copy(meta_output: dict) -> None:
    """captions payload equals the content of src/content/captions.json."""
    expected = json.loads(CAPTIONS_PATH.read_text())
    assert meta_output["captions"] == expected


def test_pipeline_version_override(seeded_db: Path, tmp_path: Path) -> None:
    """Passing pipeline_version='abc1234' uses that value verbatim."""
    from pipeline.build_meta import build  # noqa: PLC0415
    out = tmp_path / "meta.json"
    meta = build(seeded_db, CAPTIONS_PATH, out,
                 pipeline_version="abc1234", now_iso="2026-04-15T06:30:00Z")
    assert meta["pipeline_version"] == "abc1234"


def test_main_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """pipeline.__main__.run() creates chart-3c.json and meta.json artefacts."""
    import httpx  # noqa: PLC0415

    # Paths redirected to tmp so we don't touch real data/src
    db_path = tmp_path / "cfd.duckdb"
    latest_csv = tmp_path / "latest.csv"
    raw_dir = tmp_path / "raw"
    chart_out = tmp_path / "chart-3c.json"
    meta_out = tmp_path / "meta.json"
    captions_src = Path("src/content/captions.json")

    # Seed the database directly (bypass fetch)
    df = read_and_validate(FIXTURES / "cfd_sample.csv")
    upsert(df, db_path)

    # Import and patch build paths inside __main__
    import pipeline.__main__ as pm  # noqa: PLC0415
    from pipeline.build_chart_3c import build as bc  # noqa: PLC0415
    from pipeline.build_meta import build as bm  # noqa: PLC0415

    # Monkeypatch build functions to write to our tmp paths
    def mock_bc(dp, op):
        return bc(dp, chart_out)

    def mock_bm(dp, cp, op):
        return bm(dp, captions_src, meta_out,
                  pipeline_version="test", now_iso="2026-04-15T06:30:00Z")

    monkeypatch.setattr("pipeline.__main__.build_chart_3c", mock_bc)
    monkeypatch.setattr("pipeline.__main__.build_meta", mock_bm)

    # Mock fetch to copy fixture CSV to latest_csv
    def mock_fetch(dest, raw, *, client=None):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((FIXTURES / "cfd_sample.csv").read_bytes())

    monkeypatch.setattr("pipeline.__main__.fetch", mock_fetch)

    code = pm.run(
        latest_csv=latest_csv,
        raw_dir=raw_dir,
        db_path=db_path,
    )
    assert code == 0, f"pipeline run returned non-zero exit code: {code}"

    assert chart_out.exists(), "chart-3c.json not created by pipeline run"
    assert meta_out.exists(), "meta.json not created by pipeline run"

    # Validate the outputs are valid JSON
    json.loads(chart_out.read_text())
    json.loads(meta_out.read_text())
