"""Tests for src/content/glossary.json shape (Phase 01.1 plan 04 target).

Wave 0 RED: current glossary.json is phrase-keyed with string values, whereas
plan 04 migrates to slug-keyed with {term, definition} entries.

Canonical shape (plan 04 target):
    {"cfd": {"term": "CfD", "definition": "..."}, ...}

The field name is "definition" (RESEARCH Pattern 4). Do NOT use "gloss"
despite its appearance in earlier Phase 01 UI-SPEC drafts.
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED_SLUGS = {
    "cfd",
    "strike_price",
    "reference_price",
    "imrp",
    "allocation_round",
    "intermittent",
    "dispatchable",
}
LEGACY_KEYS = {
    "CfD",
    "Strike price",
    "Reference price",
    "IMRP",
    "Allocation round",
    "Investment Contract",
}
GLOSSARY = Path("src/content/glossary.json")


def _load() -> dict:
    return json.loads(GLOSSARY.read_text())


def test_required_slugs() -> None:
    """All 7 required slugs must be present as top-level keys."""
    data = _load()
    missing = REQUIRED_SLUGS - set(data.keys())
    assert not missing, f"missing required slugs: {sorted(missing)}"


def test_entry_shape() -> None:
    """Every entry is an object with non-empty string 'term' and 'definition'."""
    data = _load()
    for slug, entry in data.items():
        assert isinstance(entry, dict), (
            f"{slug}: entry must be object, got {type(entry).__name__}"
        )
        assert "term" in entry and isinstance(entry["term"], str) and entry["term"], (
            f"{slug}: missing or empty 'term'"
        )
        assert (
            "definition" in entry
            and isinstance(entry["definition"], str)
            and entry["definition"]
        ), f"{slug}: missing or empty 'definition' (not 'gloss')"


def test_no_legacy_keys() -> None:
    """Phrase-keyed legacy entries must be fully removed."""
    data = _load()
    leaked = LEGACY_KEYS & set(data.keys())
    assert not leaked, f"legacy phrase keys still present: {sorted(leaked)}"
