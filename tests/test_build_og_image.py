"""Tests for pipeline/build_og_image.py — RED phase (Task 2, Plan 01-05).

Verifies: 1200x630 PNG dimensions, file-size bounds, valid PNG magic bytes.
Uses struct.unpack on the PNG IHDR chunk to read dimensions without adding
an extra dependency (no pillow required).
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "cfd_sample_expected_3c.json"


def _read_png_dimensions(path: Path) -> tuple[int, int]:
    """Read width and height from a PNG IHDR chunk.

    PNG structure:
        bytes 0-7   : PNG signature
        bytes 8-11  : IHDR chunk data length (big-endian uint32) — always 13
        bytes 12-15 : IHDR type b"IHDR"
        bytes 16-19 : width (big-endian uint32)
        bytes 20-23 : height (big-endian uint32)
    """
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a valid PNG file"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def test_og_png_dimensions(tmp_path: Path) -> None:
    """PNG must be exactly 1200x630 pixels (Open Graph standard)."""
    from pipeline.build_og_image import build

    out = tmp_path / "og-card.png"
    build(FIXTURE, out)
    assert out.exists(), "build() did not create the output file"
    width, height = _read_png_dimensions(out)
    assert width == 1200, f"expected width 1200, got {width}"
    assert height == 630, f"expected height 630, got {height}"


def test_og_png_size_bounds(tmp_path: Path) -> None:
    """PNG file size must be between 10 KB and 500 KB."""
    from pipeline.build_og_image import build

    out = tmp_path / "og-card.png"
    build(FIXTURE, out)
    size = out.stat().st_size
    assert 10_000 <= size <= 500_000, (
        f"PNG size {size} bytes is outside the expected range [10 KB, 500 KB]"
    )


def test_og_png_is_valid_png(tmp_path: Path) -> None:
    """First 8 bytes must be the PNG magic signature."""
    from pipeline.build_og_image import build

    out = tmp_path / "og-card.png"
    build(FIXTURE, out)
    magic = out.read_bytes()[:8]
    assert magic == b"\x89PNG\r\n\x1a\n", f"unexpected file header: {magic!r}"
