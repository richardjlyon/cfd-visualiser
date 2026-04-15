"""Tests for pipeline/fetch.py (PIPE-01, PIPE-04).

Covers:
- Successful download writes dest CSV and gzip archive
- Archive decompresses to original bytes
- Raises on 5xx HTTP status
- Raises on HTML response body
- Raises on too-small response body
"""
from __future__ import annotations

import datetime as dt
import gzip
from pathlib import Path

import httpx
import pytest

TODAY = dt.date(2024, 1, 15)


def _make_mock_client(status: int, body: bytes, content_type: str = "text/csv") -> httpx.Client:
    """Build an httpx.Client backed by a MockTransport that always returns the given response."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=body, headers={"content-type": content_type})

    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport)


def test_fetch_writes_csv(tmp_path: Path, mock_lccc_response: bytes) -> None:
    dest = tmp_path / "latest.csv"
    raw_dir = tmp_path / "raw"
    client = _make_mock_client(200, mock_lccc_response)

    from pipeline.fetch import fetch

    with client:
        fetch(dest, raw_dir, client=client, today=TODAY)

    assert dest.read_bytes() == mock_lccc_response


def test_fetch_writes_gzip_archive(tmp_path: Path, mock_lccc_response: bytes) -> None:
    dest = tmp_path / "latest.csv"
    raw_dir = tmp_path / "raw"
    client = _make_mock_client(200, mock_lccc_response)

    from pipeline.fetch import fetch

    with client:
        fetch(dest, raw_dir, client=client, today=TODAY)

    archive = raw_dir / f"{TODAY.isoformat()}.csv.gz"
    assert archive.exists(), f"Expected archive at {archive}"
    with gzip.open(archive, "rb") as fh:
        decompressed = fh.read()
    assert decompressed == mock_lccc_response


def test_fetch_raises_on_500(tmp_path: Path, mock_lccc_response: bytes) -> None:
    dest = tmp_path / "latest.csv"
    raw_dir = tmp_path / "raw"
    client = _make_mock_client(500, b"Internal Server Error")

    from pipeline.fetch import fetch

    with pytest.raises(httpx.HTTPError):
        with client:
            fetch(dest, raw_dir, client=client, today=TODAY)


def test_fetch_raises_on_html_response(tmp_path: Path) -> None:
    dest = tmp_path / "latest.csv"
    raw_dir = tmp_path / "raw"
    # Pad to meet minimum size
    html_body = b"<html><body>Error page</body></html>" * 100
    client = _make_mock_client(200, html_body, content_type="text/html")

    from pipeline.fetch import fetch

    with pytest.raises(ValueError, match="HTML"):
        with client:
            fetch(dest, raw_dir, client=client, today=TODAY)


def test_fetch_raises_on_tiny_body(tmp_path: Path) -> None:
    dest = tmp_path / "latest.csv"
    raw_dir = tmp_path / "raw"
    tiny_body = b"x" * 100  # < MIN_BYTES (1024)
    client = _make_mock_client(200, tiny_body)

    from pipeline.fetch import fetch

    with pytest.raises(ValueError, match="too small"):
        with client:
            fetch(dest, raw_dir, client=client, today=TODAY)
