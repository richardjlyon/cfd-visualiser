"""End-to-end tests for pipeline/__main__.py (PIPE-05).

Covers:
- Happy path: fetch -> validate -> upsert -> returns 0, DuckDB file created
- Fetch failure (500): returns exit code 1, DuckDB NOT created
- Schema drift (extra column): returns exit code 2, DuckDB NOT created
- Healthcheck ping issued when hc_url provided
- Healthcheck skipped when PIPELINE_HC_URL is unset
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import httpx
import pytest


def _make_mock_client_for(
    lccc_body: bytes,
    *,
    hc_url: str | None = None,
    hc_calls: list[str] | None = None,
) -> httpx.Client:
    """Build a mock httpx.Client.

    If hc_url and hc_calls are provided, the HC URL returns 200 and the call
    is recorded in hc_calls for assertion.
    """
    lccc_url_fragment = "lowcarboncontracts.uk"

    def handler(request: httpx.Request) -> httpx.Response:
        if lccc_url_fragment in str(request.url):
            return httpx.Response(200, content=lccc_body, headers={"content-type": "text/csv"})
        if hc_url and str(request.url) == hc_url:
            if hc_calls is not None:
                hc_calls.append(str(request.url))
            return httpx.Response(200)
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _make_mock_client_500() -> httpx.Client:
    """Mock client that always returns 500."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b"Internal Server Error")

    return httpx.Client(transport=httpx.MockTransport(handler))


def _csv_with_extra_column(original_bytes: bytes) -> bytes:
    """Add a spurious 'Foo' column to a CSV bytes payload."""
    text = original_bytes.decode("utf-8")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    # Add 'Foo' header and values
    rows[0].append("Foo")
    for row in rows[1:]:
        row.append("99")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def test_end_to_end_happy_path(tmp_path: Path, mock_lccc_response: bytes) -> None:
    from pipeline.__main__ import run

    client = _make_mock_client_for(mock_lccc_response)
    ret = run(
        latest_csv=tmp_path / "latest.csv",
        raw_dir=tmp_path / "raw",
        db_path=tmp_path / "cfd.duckdb",
        client=client,
    )
    assert ret == 0
    db_path = tmp_path / "cfd.duckdb"
    assert db_path.exists(), "DuckDB file should exist after successful run"

    import duckdb

    con = duckdb.connect(str(db_path))
    count = con.execute("SELECT COUNT(*) FROM raw_generation;").fetchone()[0]
    con.close()
    assert count >= 800, f"Expected >= 800 rows, got {count}"


def test_fetch_failure_exits_1(tmp_path: Path) -> None:
    from pipeline.__main__ import run

    client = _make_mock_client_500()
    ret = run(
        latest_csv=tmp_path / "latest.csv",
        raw_dir=tmp_path / "raw",
        db_path=tmp_path / "cfd.duckdb",
        client=client,
    )
    assert ret == 1
    assert not (tmp_path / "cfd.duckdb").exists(), "DuckDB must NOT be created on fetch failure"


def test_schema_drift_exits_2(tmp_path: Path, mock_lccc_response: bytes) -> None:
    from pipeline.__main__ import run

    bad_body = _csv_with_extra_column(mock_lccc_response)
    client = _make_mock_client_for(bad_body)
    ret = run(
        latest_csv=tmp_path / "latest.csv",
        raw_dir=tmp_path / "raw",
        db_path=tmp_path / "cfd.duckdb",
        client=client,
    )
    assert ret == 2
    assert not (tmp_path / "cfd.duckdb").exists(), "DuckDB must NOT be created on schema drift"


def test_healthcheck_ping_issued(tmp_path: Path, mock_lccc_response: bytes) -> None:
    from pipeline.__main__ import run

    hc_calls: list[str] = []
    hc_url = "http://hc.test/abc"
    client = _make_mock_client_for(mock_lccc_response, hc_url=hc_url, hc_calls=hc_calls)
    ret = run(
        latest_csv=tmp_path / "latest.csv",
        raw_dir=tmp_path / "raw",
        db_path=tmp_path / "cfd.duckdb",
        client=client,
        hc_url=hc_url,
    )
    assert ret == 0
    assert len(hc_calls) == 1, f"Expected exactly 1 HC ping, got {len(hc_calls)}"
    assert hc_calls[0] == hc_url


def test_healthcheck_skipped_when_unset(
    tmp_path: Path, mock_lccc_response: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pipeline.__main__ import run

    monkeypatch.delenv("PIPELINE_HC_URL", raising=False)
    hc_calls: list[str] = []
    # Client does NOT have an HC handler — any HC call would return 404 and cause failure
    client = _make_mock_client_for(mock_lccc_response, hc_url=None, hc_calls=hc_calls)
    ret = run(
        latest_csv=tmp_path / "latest.csv",
        raw_dir=tmp_path / "raw",
        db_path=tmp_path / "cfd.duckdb",
        client=client,
    )
    assert ret == 0
    assert len(hc_calls) == 0, "Healthcheck should not be called when PIPELINE_HC_URL is unset"
