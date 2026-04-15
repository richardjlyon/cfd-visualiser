"""EDIT-05 grammar linter: enforce factual-only chart captions.

The UI-SPEC editorial grammar rule forbids loaded framing words inside
chart captions, titles, axis labels, and tooltips. Boxouts and prose
may use editorial voice.

Usage as CLI:
    uv run python -m pipeline.editorial [path/to/captions.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FORBIDDEN_WORDS: frozenset[str] = frozenset({
    "waste", "scandal", "outrageous", "broken",
    "unfair", "disaster", "rip-off",
})

# Build a regex that matches each forbidden word as a complete token.
# Hyphenated entries like "rip-off" need a special pattern: word boundary
# before 'rip', literal hyphen, word boundary after 'off'.
# Single-word entries use standard \b anchors.
# The alternation is sorted longest-first to prefer longer matches.
_sorted_forbidden = sorted(FORBIDDEN_WORDS, key=len, reverse=True)

def _make_pattern(word: str) -> str:
    """Return a regex pattern that matches *word* as a complete token."""
    escaped = re.escape(word)
    return r"(?<!\w)" + escaped + r"(?!\w)"

_FORBIDDEN_RE = re.compile(
    "|".join(_make_pattern(w) for w in _sorted_forbidden),
    re.IGNORECASE,
)


def lint_caption(text: str) -> list[str]:
    """Return sorted list of forbidden words present in *text* (case-insensitive, word-boundary).

    Empty list means the caption passes EDIT-05.
    """
    found: set[str] = set()
    for m in _FORBIDDEN_RE.finditer(text):
        found.add(m.group(0).lower())
    return sorted(found)


def lint_captions_file(path: Path) -> dict[str, list[str]]:
    """Lint every caption value in a captions.json file.

    Only the ``caption`` field of each chart entry is checked; the
    ``boxout`` field is intentionally excluded (editorial framing is
    permitted there per EDIT-05).

    Returns a dict mapping ``{chart_id: [offending_words]}`` for each
    failing caption. An empty dict means every caption passes.
    """
    data = json.loads(Path(path).read_text())
    violations: dict[str, list[str]] = {}
    for chart_id, payload in data.items():
        caption = payload.get("caption", "")
        bad = lint_caption(caption)
        if bad:
            violations[chart_id] = bad
    return violations


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else Path("src/content/captions.json")
    violations = lint_captions_file(path)
    if violations:
        for chart_id, words in violations.items():
            print(f"FAIL {chart_id}: forbidden words: {', '.join(words)}",
                  file=sys.stderr)
        return 1
    print(f"ok: {path} passes EDIT-05 grammar rule")
    return 0


if __name__ == "__main__":
    sys.exit(main())
