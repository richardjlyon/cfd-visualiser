"""Glossary schema tests — enforce slug-keyed {term, definition} shape.

Required slugs per UI-SPEC D-18/D-19. Legacy phrase keys must be absent.
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


def _load():
    return json.loads(GLOSSARY.read_text())


def test_required_slugs():
    data = _load()
    missing = REQUIRED_SLUGS - set(data.keys())
    assert not missing, f"missing slugs: {missing}"


def test_entry_shape():
    data = _load()
    for slug, entry in data.items():
        assert isinstance(entry, dict), (
            f"{slug}: entry must be object, got {type(entry)}"
        )
        assert (
            "term" in entry
            and isinstance(entry["term"], str)
            and entry["term"]
        ), f"{slug}: missing/empty term"
        assert (
            "definition" in entry
            and isinstance(entry["definition"], str)
            and entry["definition"]
        ), f"{slug}: missing/empty definition"


def test_no_legacy_keys():
    data = _load()
    leaked = LEGACY_KEYS & set(data.keys())
    assert not leaked, f"legacy phrase keys still present: {leaked}"
