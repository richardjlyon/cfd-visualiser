"""Post-build smoke tests for dist/ artefacts (OPS-04 download; OPS-03 a11y).

All tests skip gracefully if dist/ has not been built yet.
Run after: npx @observablehq/framework build

Framework 1.x note: Observable Framework is a client-side runtime. JS cells are
embedded as source strings in the built HTML; runtime expressions like ${c.caption}
are evaluated in the browser, not at build time.  Smoke tests therefore:
  - verify static HTML for structure (figure, aria, heading tags)
  - verify JS cell SOURCE strings for references (c.caption, c.source_url, etc.)
  - verify the captions JSON artefact for actual copy content
  - verify the chart-3c JSON artefact exists and is valid
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

DIST = Path("dist")
CAPTIONS_PATH = Path("src/content/captions.json")

TRACKER_DOMAINS = [
    "google-analytics.com",
    "googletagmanager.com",
    "facebook.net",
    "doubleclick.net",
    "mixpanel.com",
    "hotjar.com",
]


def _require_dist() -> None:
    """Skip the test if dist/ does not exist."""
    if not DIST.exists():
        pytest.skip("dist/ not found — run `npx @observablehq/framework build` first")


def _scissors_html() -> str:
    """Return the content of the built scissors page."""
    _require_dist()
    candidates = [
        DIST / "charts" / "scissors" / "index.html",
        DIST / "charts" / "scissors.html",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text()
    pytest.skip("scissors HTML not found in dist/ — build may have failed")


def _chart_json_path() -> Path:
    """Return the path to the chart-3c JSON artefact in dist/.

    Framework 1.x places FileAttachment outputs under dist/_file/ with a
    content hash.  We find the file by glob rather than hard-coding the hash.
    """
    _require_dist()
    # Framework's hashed _file/ path
    hashed = list((DIST / "_file" / "data").glob("chart-3c.*.json"))
    if hashed:
        return hashed[0]
    # Also try canonical path (pipeline writes src/data/chart-3c.json)
    canonical = DIST / "data" / "chart-3c.json"
    if canonical.exists():
        return canonical
    pytest.skip("chart-3c.json not found in dist/ — build may have failed")


def _dist_captions_path() -> Path:
    """Return the path to the captions JSON in dist/_file/."""
    _require_dist()
    hashed = list((DIST / "_file" / "content").glob("captions.*.json"))
    if hashed:
        return hashed[0]
    pytest.skip("captions.json not found in dist/_file/ — build may have failed")


def test_dist_chart_page_exists() -> None:
    """Built scissors page exists under dist/charts/."""
    _require_dist()
    candidates = [
        DIST / "charts" / "scissors" / "index.html",
        DIST / "charts" / "scissors.html",
    ]
    found = any(p.exists() for p in candidates)
    assert found, f"Neither of {candidates} exists in dist/"


def test_chart_json_artefact_exists() -> None:
    """chart-3c.json artefact exists in dist/ and is valid JSON with records."""
    json_path = _chart_json_path()
    parsed = json.loads(json_path.read_text())
    assert isinstance(parsed, list), "chart-3c.json should be a JSON array"
    assert len(parsed) > 0, "chart-3c.json should have at least one record"


def test_page_contains_caption() -> None:
    """The captions artefact shipped with the build contains the chart-3c caption."""
    # Framework embeds JS cell source in HTML; the caption text is loaded at runtime
    # from captions.json. Verify the shipped captions.json contains the correct text.
    captions_path = _dist_captions_path()
    captions = json.loads(captions_path.read_text())
    caption = json.loads(CAPTIONS_PATH.read_text())["chart-3c"]["caption"]
    assert "chart-3c" in captions, "chart-3c key missing from shipped captions.json"
    assert captions["chart-3c"]["caption"] == caption, (
        f"Caption mismatch in shipped captions.\n"
        f"Expected: {caption!r}\n"
        f"Got: {captions['chart-3c']['caption']!r}"
    )


def test_page_contains_source_url() -> None:
    """The captions artefact shipped with the build contains the LCCC source URL."""
    captions_path = _dist_captions_path()
    captions = json.loads(captions_path.read_text())
    url = "https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions"
    assert captions["chart-3c"]["source_url"] == url, (
        f"Source URL mismatch in shipped captions.\nExpected: {url!r}"
    )


def test_page_contains_download_link() -> None:
    """Built scissors HTML contains a download reference to chart-3c.json."""
    html = _scissors_html()
    # The download link is in the JS cell source embedded in the HTML
    assert "chart-3c.json" in html, "chart-3c.json reference not found in built page"
    assert "download" in html, "No download attribute found in built page"


def test_page_contains_boxout_heading() -> None:
    """Built scissors page static HTML contains 'What does this mean?' heading."""
    html = _scissors_html()
    assert "What does this mean?" in html, (
        "'What does this mean?' heading not found in built page"
    )


def test_page_contains_round_labels() -> None:
    """Built scissors page JS cell source contains allocation round labels."""
    html = _scissors_html()
    for label in ["Investment Contract", "Allocation Round 1", "Allocation Round 5"]:
        assert label in html, f"Round label {label!r} not found in built page"


def test_no_third_party_trackers() -> None:
    """Built scissors page does not contain known tracker domains."""
    html = _scissors_html()
    found = [d for d in TRACKER_DOMAINS if d in html]
    assert not found, (
        f"Third-party tracker domains found in built page: {found}"
    )


def test_aria_labels_present() -> None:
    """Built scissors page static HTML contains aria-labelledby for the chart figure."""
    html = _scissors_html()
    assert "aria-labelledby" in html, (
        "No aria-labelledby found in built page — chart accessibility attributes missing"
    )
