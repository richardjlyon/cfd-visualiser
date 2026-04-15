"""Daily LCCC CSV fetch with gzip archive (PIPE-01, PIPE-04).

Security:
- HTML-body guard: rejects responses containing <html in first 1024 bytes
- Min-size guard: rejects responses smaller than MIN_BYTES (catches truncated downloads)
- httpx raise_for_status: rejects non-2xx responses
- TLS via httpx default; retries=3 with HTTPTransport

See T-01-02-01 and T-01-02-02 in plan threat model.
"""
from __future__ import annotations

import datetime as dt
import gzip
from pathlib import Path

import httpx

LCCC_URL: str = (
    "https://dp.lowcarboncontracts.uk/dataset/"
    "8e8ca0d5-c774-4dc8-a079-347f1c180c0f/resource/"
    "5279a55d-4996-4b1e-ba07-f411d8fd31f0/download/"
    "actual_cfd_generation_and_avoided_ghg_emissions.csv"
)

MIN_BYTES = 1024  # < 1 KB is definitely a truncated/empty response


def fetch(
    dest_csv: Path,
    raw_dir: Path,
    *,
    client: httpx.Client | None = None,
    url: str = LCCC_URL,
    today: dt.date | None = None,
) -> Path:
    """Download LCCC CSV to dest_csv and write a gzipped archive to raw_dir.

    Args:
        dest_csv: Destination path for the uncompressed CSV (e.g. data/latest.csv).
        raw_dir: Directory for gzipped date-stamped snapshots (e.g. data/raw/).
        client: Optional httpx.Client for testing. If None, a client with retries=3
                and timeout=60s is created and closed after the request.
        url: CSV download URL. Defaults to LCCC_URL.
        today: Date used for archive filename stamp. Defaults to dt.date.today().

    Returns:
        Path to the written dest_csv file.

    Raises:
        httpx.HTTPStatusError: On non-2xx HTTP response after retries.
        ValueError: If response body is smaller than MIN_BYTES or looks like HTML.
    """
    owns_client = client is None
    if client is None:
        transport = httpx.HTTPTransport(retries=3)
        client = httpx.Client(
            transport=transport, timeout=60.0, follow_redirects=True
        )
    try:
        r = client.get(url)
        r.raise_for_status()
        body = r.content
    finally:
        if owns_client:
            client.close()

    if len(body) < MIN_BYTES:
        raise ValueError(
            f"LCCC response too small ({len(body)} bytes); "
            f"expected >= {MIN_BYTES}"
        )
    head = body[:1024].lower()
    if b"<html" in head or b"<!doctype html" in head:
        raise ValueError(
            "LCCC response looks like HTML (not CSV) — upstream error page?"
        )

    dest_csv.parent.mkdir(parents=True, exist_ok=True)
    dest_csv.write_bytes(body)

    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = (today or dt.date.today()).isoformat()
    archive = raw_dir / f"{stamp}.csv.gz"
    with gzip.open(archive, "wb") as dst:
        dst.write(body)
    return dest_csv
