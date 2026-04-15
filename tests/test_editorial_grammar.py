"""Tests for the EDIT-05 grammar linter (pipeline/editorial.py).

RED phase: all tests import from pipeline.editorial which does not yet exist —
these tests are expected to FAIL until the implementation is written (GREEN phase).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.editorial import lint_caption, lint_captions_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_factual_caption_passes():
    assert lint_caption("Consumers paid the gap") == []


def test_scandal_and_waste_both_flagged():
    result = lint_caption("This is a scandal and a waste")
    assert set(result) == {"scandal", "waste"}


def test_word_boundary_hyphen():
    # "waste" is a word on its own (adjacent to hyphen boundary); must be flagged
    assert lint_caption("waste-heat recovery") == ["waste"]


def test_substring_not_flagged():
    # "wasted" and "scandalous" are not exact-word matches
    assert lint_caption("wasted") == []
    assert lint_caption("scandalous") == []


def test_case_insensitive():
    assert lint_caption("Scandal") == ["scandal"]


def test_rip_off_hyphenated():
    # "rip-off" is a multi-token forbidden word; must be matched as a unit
    assert lint_caption("A rip-off for consumers") == ["rip-off"]


def test_valid_fixture_file_passes():
    result = lint_captions_file(FIXTURES / "captions_valid.json")
    assert result == {}


def test_invalid_fixture_file_fails():
    result = lint_captions_file(FIXTURES / "captions_invalid.json")
    # Both bad-a and bad-b should appear as violations
    assert "bad-a" in result
    assert "bad-b" in result
    # bad-a caption contains both "scandal" and "waste"
    assert "scandal" in result["bad-a"]
    assert "waste" in result["bad-a"]
    # bad-b caption contains "rip-off"
    assert "rip-off" in result["bad-b"]


def test_real_captions_file_passes():
    real = Path("src/content/captions.json")
    assert lint_captions_file(real) == {}


def test_boxout_not_linted():
    # captions_valid.json test-a has "waste" in boxout but a clean caption
    result = lint_captions_file(FIXTURES / "captions_valid.json")
    # Confirm that test-a (which has "waste" in boxout) does NOT appear as violation
    assert "test-a" not in result
