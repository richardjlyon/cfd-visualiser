"""Tests for pipeline/export_chart_images.py (Phase 01.1 plan 05 target).

Wave 0 RED: pipeline/export_chart_images.py does not yet exist.

- test_module_file_exists runs OUTSIDE the import-skip guard so that the
  suite fails RED at Wave 0 (not vacuously skipped); flips GREEN when plan 05
  lands the module.
- The parametrised PNG assertions use pytest.importorskip to stay silent
  under collection until the module exists; they flip RED the moment the
  module is importable (plan 05) and only turn GREEN when the 4 PNGs are on
  disk at the correct dimensions + dark background.
"""
from __future__ import annotations

import struct
from pathlib import Path

import pytest

CHART_ASSETS = Path("src/assets/charts")

# (filename, expected_width, expected_height)
EXPECTED_PNGS: list[tuple[str, int, int]] = [
    ("chart-3c.png", 1200, 630),
    ("chart-co2-avoided-placeholder.png", 1200, 630),
    ("chart-cumulative-subsidy-placeholder.png", 1200, 630),
    ("chart-heatmap-placeholder.png", 1200, 630),
]

# Optional thumbnails (card-grid sparklines). Not required in plan 05 but
# listed for forward compatibility — tests skip if module omits them.
OPTIONAL_THUMBNAILS: list[tuple[str, int, int]] = [
    ("chart-3c-thumb.png", 280, 140),
    ("chart-co2-avoided-thumb.png", 280, 140),
]

# Dark-theme top-left background pixel (energy-dashboard aesthetic).
DARK_BG_RGB = (0x0d, 0x11, 0x17)


def test_module_file_exists() -> None:
    """pipeline/export_chart_images.py must exist (plan 05 creates it).

    This assertion is *collected and executed* even when the module is not
    yet importable — Wave 0 records a true RED failure rather than a vacuous
    skip. Once plan 05 adds the file the test flips GREEN.
    """
    assert Path("pipeline/export_chart_images.py").exists(), (
        "pipeline/export_chart_images.py missing — plan 05 target"
    )


def _eci():
    """Return the pipeline.export_chart_images module or pytest.skip at call time.

    Used instead of a module-level importorskip so that test_module_file_exists
    above is still collected and executed (importorskip at module scope skips
    the whole file, including the guard test).
    """
    try:
        import pipeline.export_chart_images as mod  # noqa: PLC0415
    except ImportError:
        pytest.skip(
            "pipeline.export_chart_images not yet implemented — Wave 0 scaffold",
            allow_module_level=False,
        )
    return mod


def _read_png_dimensions(path: Path) -> tuple[int, int]:
    """Read width and height from a PNG IHDR chunk (big-endian uint32s)."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"not a valid PNG: {path}"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


@pytest.fixture(scope="module")
def built_assets(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Invoke build_all() to produce the PNGs into a tmp directory.

    The module is expected to expose a build_all(out_dir: Path) entry point
    mirroring pipeline/build_og_image.py's build(in_path, out_path) shape.
    """
    eci = _eci()
    out = tmp_path_factory.mktemp("chart_pngs")
    # Expected signature: build_all(out_dir: Path) -> list[Path]
    eci.build_all(out)
    return out


@pytest.mark.parametrize("filename,expected_w,expected_h", EXPECTED_PNGS)
def test_is_valid_png(built_assets: Path, filename: str, expected_w: int, expected_h: int) -> None:
    """All required PNGs exist and start with the PNG magic signature."""
    path = built_assets / filename
    assert path.exists(), f"required PNG missing: {filename}"
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"invalid PNG header: {filename}"


@pytest.mark.parametrize("filename,expected_w,expected_h", EXPECTED_PNGS)
def test_dimensions(built_assets: Path, filename: str, expected_w: int, expected_h: int) -> None:
    """Each PNG is exactly 1200x630 (energy-dashboard card proportions)."""
    path = built_assets / filename
    w, h = _read_png_dimensions(path)
    assert (w, h) == (expected_w, expected_h), (
        f"{filename}: expected {expected_w}x{expected_h}, got {w}x{h}"
    )


@pytest.mark.parametrize("filename,expected_w,expected_h", EXPECTED_PNGS)
def test_size_bounds(built_assets: Path, filename: str, expected_w: int, expected_h: int) -> None:
    """PNG file size within [5KB, 600KB] — catches blank or enormous renders."""
    path = built_assets / filename
    size = path.stat().st_size
    assert 5_000 <= size <= 600_000, (
        f"{filename}: size {size} bytes outside [5KB, 600KB]"
    )


@pytest.mark.parametrize("filename,expected_w,expected_h", EXPECTED_PNGS)
def test_dark_bg(built_assets: Path, filename: str, expected_w: int, expected_h: int) -> None:
    """Top-left pixel RGB matches the dark-theme background (0d1117)."""
    from PIL import Image  # noqa: PLC0415

    path = built_assets / filename
    with Image.open(path) as img:
        px = img.convert("RGB").getpixel((0, 0))
    assert px[:3] == DARK_BG_RGB, (
        f"{filename}: top-left pixel {px[:3]} != dark-theme {DARK_BG_RGB}"
    )
