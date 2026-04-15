"""Tests for pipeline/build_meta.py (meta artefact builder).

TDD RED phase: tests must fail before build_meta.py exists.
"""
from __future__ import annotations

import datetime as dt
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
    """All 10 required keys are present in the meta output (Phase 01.1 adds 4)."""
    required = {
        "last_updated", "row_count", "max_settlement_date",
        "pipeline_version", "schema_version", "captions",
        # Phase 01.1 — shock counter
        "ytd_subsidy_gbp", "ytd_as_of", "gbp_per_sec_rate", "ytd_label_year",
    }
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
    """schema_version is exactly the string '1.1' after Phase 01.1 bump."""
    assert meta_output["schema_version"] == "1.1"


# ── Phase 01.1 shock-counter field tests ──────────────────────────────────────

def test_emits_ytd_subsidy(meta_output: dict) -> None:
    """ytd_subsidy_gbp is a float >= 0 (D-09)."""
    v = meta_output["ytd_subsidy_gbp"]
    assert isinstance(v, float), f"ytd_subsidy_gbp must be float, got {type(v)}"
    assert v >= 0.0, f"ytd_subsidy_gbp must be >= 0, got {v}"


def test_rate_clamped_non_negative(seeded_db: Path, tmp_path: Path) -> None:
    """gbp_per_sec_rate is clamped >= 0 even when a clawback row dominates the
    trailing 30-day window (Pitfall 2 / T-01.1-04).

    Fixture construction: inject a synthetic row into raw_generation with a
    large negative CFD_Payments_GBP (typical of 2022 clawback events) dated
    one day before max_settlement_date. If the SQL were not GREATEST-clamped,
    AVG(daily_gbp) / 86400 would go negative.
    """
    import duckdb  # noqa: PLC0415
    from pipeline.build_meta import build  # noqa: PLC0415

    # Inject a clawback row. Use a fresh writable connection.
    con = duckdb.connect(str(seeded_db))
    try:
        max_date = con.execute(
            "SELECT CAST(MAX(Settlement_Date) AS VARCHAR) FROM raw_generation"
        ).fetchone()[0]
        # Insert a single clawback row dated = max_date with a large negative
        # payment. This guarantees AVG(daily_gbp) over the 30-day window is
        # dominated by the clawback if the existing rows net positive.
        con.execute(
            """
            INSERT INTO raw_generation (
                Settlement_Date, CfD_ID, Name_of_CfD_Unit, Technology,
                Allocation_round, Reference_Type, CFD_Generation_MWh,
                Avoided_GHG_tonnes_CO2e, CFD_Payments_GBP, Avoided_GHG_Cost_GBP,
                Strike_Price_GBP_Per_MWh, Market_Reference_Price_GBP_Per_MWh,
                Weighted_IMRP_GBP_Per_MWh
            ) VALUES (
                ?, 'CLW-XYZ-999', 'Clawback Synthetic', 'Offshore Wind',
                'Allocation Round 1', 'IMRP', 1.0, 0.0, ?, 0.0, 100.0, 50.0, 50.0
            )
            """,
            [max_date, -1_000_000_000.0],
        )
    finally:
        con.close()

    out = tmp_path / "meta_clawback.json"
    meta = build(
        seeded_db, CAPTIONS_PATH, out,
        pipeline_version="test", now_iso="2026-04-15T06:30:00Z",
    )
    assert meta["gbp_per_sec_rate"] >= 0.0, (
        f"gbp_per_sec_rate must be clamped non-negative even under clawback, "
        f"got {meta['gbp_per_sec_rate']}"
    )


def test_ytd_as_of_is_data_date(meta_output: dict) -> None:
    """ytd_as_of equals max_settlement_date (NOT last_updated build time).

    Mitigates T-01.1-02 stale-data deception: if build_meta silently uses
    `last_updated` here, a stale snapshot would claim a fresher YTD.
    """
    assert meta_output["ytd_as_of"] == meta_output["max_settlement_date"], (
        f"ytd_as_of ({meta_output['ytd_as_of']!r}) must equal "
        f"max_settlement_date ({meta_output['max_settlement_date']!r})"
    )
    # Explicitly distinct from last_updated (which is an ISO timestamp).
    assert meta_output["ytd_as_of"] != meta_output["last_updated"]


def test_ytd_as_of_not_in_future(meta_output: dict) -> None:
    """ytd_as_of must not be in the future relative to wall-clock UTC date.

    ISO YYYY-MM-DD strings compare correctly lexicographically.
    """
    today_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    assert meta_output["ytd_as_of"] <= today_iso, (
        f"ytd_as_of {meta_output['ytd_as_of']!r} is in the future "
        f"(today UTC = {today_iso!r})"
    )


def test_ytd_year_from_data(meta_output: dict) -> None:
    """ytd_label_year is the int year derived from max_settlement_date,
    NOT from datetime.now().year."""
    expected_year = int(meta_output["max_settlement_date"][:4])
    assert meta_output["ytd_label_year"] == expected_year
    assert isinstance(meta_output["ytd_label_year"], int)


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
