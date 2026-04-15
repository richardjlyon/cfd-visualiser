---
phase: "01"
plan: "03"
subsystem: frontend-scaffold
tags: [observable-framework, pico-css, editorial, accessibility, tdd]
dependency_graph:
  requires: []
  provides:
    - Observable Framework 1.13.4 build scaffold (src/ → dist/)
    - Okabe-Ito design tokens in src/assets/custom.css
    - Pico CSS 2.x classless stylesheet vendored to src/assets/
    - Editorial glossary at src/content/glossary.json
    - Editorial captions at src/content/captions.json (chart-3c seeded)
    - EDIT-05 grammar linter at pipeline/editorial.py (lint_caption, lint_captions_file, CLI)
    - pyproject.toml with full production + test dependency set
    - uv.lock for reproducible Python environment
  affects:
    - Plan 01-04 (chart builder page): consumes src/assets/custom.css tokens, src/content/captions.json, src/content/glossary.json
    - Plan 01-05 (CI/deploy): wires pipeline/editorial.py into the build gate
tech_stack:
  added:
    - "@observablehq/framework@1.13.4 (npm)"
    - "Pico CSS 2.x classless build (vendored CDN)"
    - "polars>=1.39.3, duckdb>=1.5.2, httpx, pyarrow, pytest (uv dependency set)"
  patterns:
    - "observablehq.config.js at repo root with root: 'src' — Framework convention"
    - "src/assets/ for vendored CSS; src/content/ for editorial JSON"
    - "TDD: RED commit (test(01-03)) then GREEN commit (feat(01-03)) for linter"
key_files:
  created:
    - package.json
    - package-lock.json
    - observablehq.config.js
    - src/index.md
    - src/assets/pico.min.css
    - src/assets/custom.css
    - src/content/glossary.json
    - src/content/captions.json
    - pipeline/__init__.py
    - pipeline/editorial.py
    - tests/__init__.py
    - tests/test_editorial_grammar.py
    - tests/fixtures/captions_valid.json
    - tests/fixtures/captions_invalid.json
    - pyproject.toml
    - uv.lock
    - .gitignore
  modified: []
decisions:
  - "observablehq.config.js placed at repo root (not inside src/) with root: 'src' — matches RESEARCH recommended project structure and eliminates framework root-option warning"
  - "Pico CSS classless variant downloaded at 71 KB (not ~7 KB as CLAUDE.md stated — full classless build includes responsive styles; no impact on functionality)"
  - "rip-off matched using negative lookahead/lookbehind ((?<!\\w)rip-off(?!\\w)) rather than \\b — hyphens are not \\w chars so standard \\b would split on the hyphen"
  - "pyproject.toml created in worktree with expanded dependency set (polars, duckdb, httpx, pyarrow, pytest) — main branch pyproject.toml only had matplotlib+pandas"
metrics:
  completed_date: "2026-04-15"
  tasks_completed: 3
  files_created: 17
  files_modified: 1
---

# Phase 01 Plan 03: Framework Scaffold and Editorial Guardrails Summary

Observable Framework 1.13.4 scaffolded with Pico CSS classless stylesheet, Okabe-Ito colour tokens, 720px content measure, EDIT-05 grammar linter (10 TDD tests, all green), and editorial content files seeded for chart-3c.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Observable Framework scaffold + Pico CSS + Okabe-Ito tokens | 043916f | package.json, observablehq.config.js, src/index.md, src/assets/custom.css, src/assets/pico.min.css |
| 2 | Editorial content — glossary + captions JSON | 690c9c3 | src/content/glossary.json, src/content/captions.json |
| 3 (RED) | EDIT-05 grammar linter tests (failing) | cd46b55 | tests/test_editorial_grammar.py, tests/fixtures/*.json, pyproject.toml |
| 3 (GREEN) | EDIT-05 grammar linter implementation | 1b7f486 | pipeline/editorial.py |
| — | uv.lock + .gitignore cleanup | 13f8900 | uv.lock, .gitignore |

## Verification Results

- `npx @observablehq/framework build` — exits 0; dist/index.html contains "CfD Visualiser" and both CSS asset links
- `uv run pytest tests/test_editorial_grammar.py -x -q` — 10 passed
- `uv run python -m pipeline.editorial src/content/captions.json` — exits 0 ("ok: passes EDIT-05")
- `uv run python -m pipeline.editorial tests/fixtures/captions_invalid.json` — exits 1 (FAIL bad-a, FAIL bad-b)
- `uv run pytest tests/ -x -q` — 10 passed (full suite)

## Framework Version Actually Installed

`@observablehq/framework@1.13.4` — exactly as pinned. Observable Plot `0.6.17` bundled transitively (confirmed in build output: `npm:@observablehq/plot@0.6.17`).

## Pico CSS Variant Used

**Classless build** (`pico.classless.min.css`). Downloaded from jsDelivr CDN and vendored to `src/assets/pico.min.css`. File size: 71,040 bytes. The classless variant styles HTML elements directly (no class attributes needed in Markdown-generated HTML).

## Linter Forbidden-Word List

```python
FORBIDDEN_WORDS = frozenset({
    "waste", "scandal", "outrageous", "broken",
    "unfair", "disaster", "rip-off",
})
```

`rip-off` is matched as a complete hyphenated token using `(?<!\w)rip\-off(?!\w)` to avoid false positives from substring matches.

## UI-SPEC Copy Deviations

None. All glossary strings, caption text, boxout copy, and source URLs were taken verbatim from UI-SPEC Copywriting Contract and RESEARCH CHART-01 specification. The `Investment Contract` glossary entry includes a Q7-deferral note as specified by RESEARCH Open Q7 resolution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Config location] observablehq.config.js moved from src/ to repo root**
- **Found during:** Task 1
- **Issue:** Plan action step 3 implied writing the config inside `src/`, but Framework looks for the config in the working directory (repo root). Building with `root: "."` from inside `src/` would cause asset path confusion. RESEARCH recommended project structure explicitly shows the config at the repo root with `root: "src"`.
- **Fix:** Created config at repo root with `root: "src"`; ran build to confirm no warnings.
- **Files modified:** observablehq.config.js (created at repo root, not src/)
- **Commit:** 043916f

**2. [Rule 2 - Missing infra] pyproject.toml created in worktree with full dependency set**
- **Found during:** Task 3 (TDD setup)
- **Issue:** The worktree had no pyproject.toml (main branch version excluded pytest, polars, duckdb, httpx, pyarrow). `uv run pytest` would fail without it.
- **Fix:** Created pyproject.toml with the full CLAUDE.md-recommended dependency set; committed uv.lock.
- **Files modified:** pyproject.toml, uv.lock
- **Commit:** cd46b55

**3. [Rule 1 - Bug] rip-off regex pattern uses lookahead/lookbehind instead of \b**
- **Found during:** Task 3 implementation (GREEN phase)
- **Issue:** The plan's suggested regex `\b(\w[\w-]*)\b` tokenises on `\w` characters, meaning the hyphen in `rip-off` acts as a word boundary and splits the token into `rip` and `off` — neither of which is in FORBIDDEN_WORDS. The test `test_rip_off_hyphenated` would fail with the suggested regex.
- **Fix:** Used `(?<!\w)` and `(?!\w)` (negative lookahead/lookbehind) to match `rip-off` as a complete unit regardless of hyphen handling.
- **Files modified:** pipeline/editorial.py
- **Commit:** 1b7f486

## Known Stubs

None. All files contain real content (no placeholder text, no empty data sources). The `src/index.md` page mentions "The scissors chart lands next" — this is intentional editorial prose, not a data stub. The chart arrives in Plan 01-04.

## Threat Flags

No new security-relevant surface introduced beyond the plan's threat model. No network endpoints, no auth paths, no user input paths. The EDIT-05 linter processes local JSON files only.

## TDD Gate Compliance

- RED gate: commit `cd46b55` — `test(01-03): add failing tests for EDIT-05 grammar linter (RED phase)`
- GREEN gate: commit `1b7f486` — `feat(01-03): implement EDIT-05 grammar linter pipeline/editorial.py (GREEN phase)`
- REFACTOR: not needed; implementation was clean on first pass.

## Self-Check: PASSED

Files verified present:
- package.json: FOUND
- observablehq.config.js: FOUND
- src/index.md: FOUND
- src/assets/pico.min.css: FOUND
- src/assets/custom.css: FOUND
- src/content/glossary.json: FOUND
- src/content/captions.json: FOUND
- pipeline/editorial.py: FOUND
- tests/test_editorial_grammar.py: FOUND
- pyproject.toml: FOUND
- uv.lock: FOUND

Commits verified:
- 043916f: FOUND
- 690c9c3: FOUND
- cd46b55: FOUND
- 1b7f486: FOUND
- 13f8900: FOUND
