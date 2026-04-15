"""Regression test: every <abbr data-glossary="slug"> in src/**/*.md resolves
to a defined entry in src/content/glossary.json.

Wave 0 state: GREEN (no abbr refs in any .md file yet). The test becomes a
live regression guard the moment Wave 3 pages ship slug-tagged prose; a
typo'd slug will fail this test before it ever reaches a browser tooltip.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ABBR_RE = re.compile(r'<abbr[^>]*\bdata-glossary="([^"]+)"')


def test_no_dangling_refs() -> None:
    """Every data-glossary slug used in src/**/*.md must be defined in glossary.json."""
    defined = set(json.loads(Path("src/content/glossary.json").read_text()).keys())
    used: set[str] = set()
    for md in Path("src").rglob("*.md"):
        used.update(ABBR_RE.findall(md.read_text()))
    dangling = used - defined
    assert not dangling, (
        f"<abbr data-glossary=...> refs with no glossary entry: {sorted(dangling)}"
    )
