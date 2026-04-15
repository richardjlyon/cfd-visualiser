---
phase: 01-pipeline-first-chart
plan: 03
type: execute
wave: 1
depends_on: []
files_modified:
  - package.json
  - package-lock.json
  - src/observablehq.config.js
  - src/index.md
  - src/assets/pico.min.css
  - src/assets/custom.css
  - src/content/glossary.json
  - src/content/captions.json
  - pipeline/editorial.py
  - tests/test_editorial_grammar.py
  - tests/fixtures/captions_valid.json
  - tests/fixtures/captions_invalid.json
  - .gitignore
autonomous: true
requirements: [EDIT-01, EDIT-02, EDIT-04, EDIT-05, OPS-03]
tags: [observable-framework, pico-css, editorial, accessibility]

must_haves:
  truths:
    - "`npx @observablehq/framework build` exits 0 on the scaffolded site"
    - "The built dist/ contains a page with the wordmark 'CfD Visualiser', Pico CSS linked, and a 720px max-width content column"
    - "An EDIT-05 grammar linter rejects any caption containing any word in the forbidden set (waste, scandal, outrageous, broken, unfair, disaster, rip-off)"
    - "Glossary JSON defines one-line entries for CfD, Strike price, Reference price, IMRP, Allocation round"
    - "The editorial grammar linter is runnable as a pytest and as a standalone CLI (pipeline/editorial.py)"
    - "Okabe-Ito chart palette tokens (#0072B2, #E69F00, #D55E00, #009E73) are defined in src/assets/custom.css"
  artifacts:
    - path: "package.json"
      provides: "Pinned @observablehq/framework 1.13.4 dependency and build script"
      contains: "@observablehq/framework"
    - path: "src/observablehq.config.js"
      provides: "Framework config: title, root, head tags, theme"
      contains: "export default"
    - path: "src/index.md"
      provides: "Landing page with site shell, wordmark, Pico + custom CSS applied"
      contains: "CfD Visualiser"
    - path: "src/assets/pico.min.css"
      provides: "Vendored Pico CSS 2.x classless stylesheet"
    - path: "src/assets/custom.css"
      provides: "Site-specific overrides: 720px measure, Okabe-Ito tokens, 44px tap targets"
      contains: "--okabe"
    - path: "src/content/glossary.json"
      provides: "Shared glossary of data-journalism jargon with one-line glosses"
      contains: "CfD"
    - path: "src/content/captions.json"
      provides: "Factual-only chart captions keyed by chart id (EDIT-01 template)"
      contains: "chart-3c"
    - path: "pipeline/editorial.py"
      provides: "EDIT-05 grammar linter: forbidden-word check on captions"
      contains: "FORBIDDEN_WORDS"
    - path: "tests/test_editorial_grammar.py"
      provides: "Linter tests: accept factual, reject loaded"
  key_links:
    - from: "src/index.md"
      to: "src/assets/custom.css"
      via: "Framework head link"
      pattern: "custom\\.css"
    - from: "src/index.md"
      to: "src/assets/pico.min.css"
      via: "Framework head link"
      pattern: "pico\\.min\\.css"
    - from: "tests/test_editorial_grammar.py"
      to: "src/content/captions.json"
      via: "load and lint real caption file"
      pattern: "captions\\.json"
---

<objective>
Scaffold the Observable Framework site, vendor Pico CSS 2.x, define the Okabe-Ito colour tokens + 720px content measure in `custom.css`, and establish the editorial contract: a glossary, a captions file, and an EDIT-05 grammar linter (factual vs loaded words). The site has no chart yet — that arrives in Plan 01-04. This plan produces the shell and the editorial guardrails every future chart will reuse.

Purpose: UI-SPEC locks typography, palette, page shell, and grammar rule. Chart-producing plans should consume these assets, not reinvent them. This plan makes them exist.

Output: Framework project under `src/`, editorial content files, grammar linter + tests.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/phases/01-pipeline-first-chart/01-RESEARCH.md
@.planning/phases/01-pipeline-first-chart/01-UI-SPEC.md
@.planning/REQUIREMENTS.md

<interfaces>
<!-- New contracts this plan creates for downstream plans (01-04, 01-05) -->

```python
# pipeline/editorial.py
FORBIDDEN_WORDS: frozenset[str]  # {"waste", "scandal", "outrageous", "broken", "unfair", "disaster", "rip-off"}

def lint_caption(text: str) -> list[str]:
    """Return list of forbidden words present in text (case-insensitive, word-boundary).
    Empty list means caption passes EDIT-05."""

def lint_captions_file(path: Path) -> dict[str, list[str]]:
    """Lint every value in captions.json; return {chart_id: [offending_words]}
    for failures. Empty dict = all pass."""
```

```json
// src/content/captions.json schema
{
  "<chart-id>": {
    "caption": "<EDIT-01 one-line factual caption>",
    "source_name": "<dataset name>",
    "source_url": "<https URL>",
    "boxout": "<EDIT-04 2-3 sentence plain-language boxout>"
  }
}
```

```json
// src/content/glossary.json schema
{
  "<term>": "<one-line gloss>"
}
```

```css
/* src/assets/custom.css tokens (downstream chart pages consume these) */
:root {
  --okabe-blue: #0072B2;     /* accent; strike price line */
  --okabe-orange: #E69F00;   /* market reference price line */
  --okabe-vermillion: #D55E00;  /* positive-subsidy fill */
  --okabe-green: #009E73;    /* clawback fill */
  --content-measure: 720px;
  --tap-target: 44px;
}
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Observable Framework scaffold + Pico CSS + Okabe-Ito tokens in custom.css</name>
  <files>package.json, package-lock.json, src/observablehq.config.js, src/index.md, src/assets/pico.min.css, src/assets/custom.css, .gitignore</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-UI-SPEC.md (Page Shell, Typography, Color, Spacing Scale sections — mandatory)
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (Pattern 3 example lines 350-390; Recommended Project Structure lines 222-266)
    - CLAUDE.md (Observable Framework 1.13.4 version lock)
  </read_first>
  <behavior>
    - `npm ci` then `npx @observablehq/framework build` exits 0 and produces `dist/index.html`
    - `dist/index.html` contains the wordmark text "CfD Visualiser"
    - `dist/index.html` links both `pico.min.css` and `custom.css` (hashed asset names are fine; content match is what matters)
    - `src/assets/custom.css` defines `--okabe-blue: #0072B2`, `--okabe-orange: #E69F00`, `--okabe-vermillion: #D55E00`, `--okabe-green: #009E73`, `--content-measure: 720px`, `--tap-target: 44px`
    - package.json pins `@observablehq/framework` to exactly `1.13.4`
    - `npm list @observablehq/plot` shows it available (bundled with Framework)
  </behavior>
  <action>
    1. Initialise npm project at repo root (next to pyproject.toml, not in src/):
       - Create `package.json`:
         ```json
         {
           "name": "cfd-visualiser",
           "private": true,
           "type": "module",
           "scripts": {
             "build": "observable build",
             "dev": "observable preview",
             "clean": "observable clean"
           },
           "dependencies": {
             "@observablehq/framework": "1.13.4"
           },
           "engines": {
             "node": ">=20"
           }
         }
         ```
       - Run `npm install` to generate `package-lock.json`.
    2. Download Pico CSS 2.x classless build:
       ```bash
       mkdir -p src/assets
       curl -fsSL https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.classless.min.css -o src/assets/pico.min.css
       ```
       - Verify file size > 5 KB and < 50 KB (sanity check on Pico classless ~25 KB).
    3. Create `src/observablehq.config.js`:
       ```javascript
       export default {
         title: "CfD Visualiser",
         root: ".",
         pages: [
           { name: "Home", path: "/" }
         ],
         head: `
       <link rel="stylesheet" href="/assets/pico.min.css">
       <link rel="stylesheet" href="/assets/custom.css">
       <meta name="viewport" content="width=device-width, initial-scale=1">
       <meta name="description" content="UK Contracts for Difference: what consumers pay vs the market. Daily-rebuilt from LCCC data.">
         `.trim(),
         theme: "air",
         footer: "Built daily from the LCCC dataset."
       };
       ```
    4. Create `src/assets/custom.css` (tokens + page shell per UI-SPEC):
       ```css
       :root {
         /* Okabe-Ito colourblind-safe palette (UI-SPEC Color section) */
         --okabe-blue:       #0072B2; /* accent, strike price line, links */
         --okabe-orange:     #E69F00; /* market reference price line */
         --okabe-vermillion: #D55E00; /* positive subsidy fill */
         --okabe-green:      #009E73; /* clawback fill (2022) */

         /* Layout tokens */
         --content-measure: 720px;
         --tap-target: 44px;

         /* Spacing scale (8-point) */
         --space-xs:   4px;
         --space-sm:   8px;
         --space-md:  16px;
         --space-lg:  24px;
         --space-xl:  32px;
         --space-2xl: 48px;
         --space-3xl: 64px;
       }

       main, article {
         max-width: var(--content-measure);
         margin-inline: auto;
         padding-inline: var(--space-md);
       }

       /* Minimum tap target enforcement (OPS-03 / WCAG 2.5.5) */
       button, a.download, a.toggle {
         min-height: var(--tap-target);
         min-width: var(--tap-target);
         display: inline-flex;
         align-items: center;
         justify-content: center;
         padding: var(--space-sm) var(--space-md);
       }

       figure.chart {
         margin-block: var(--space-xl);
       }

       aside.boxout {
         background: var(--pico-muted-bg);
         padding: var(--space-lg);
         margin-block: var(--space-lg);
         border-radius: 8px;
       }

       p.caption {
         font-size: 1rem;
         line-height: 1.5;
         color: var(--pico-color);
         margin-block: var(--space-md);
       }

       .source-line {
         font-style: italic;
         font-size: 0.875rem;
         color: var(--pico-muted-color);
       }
       ```
    5. Create `src/index.md`:
       ```md
       ---
       title: CfD Visualiser
       toc: false
       ---

       # UK CfD: what consumers pay vs the market

       <p class="caption">The scissors chart lands next. This scaffold proves the Framework build and design system.</p>

       <aside class="boxout">
         <h3>What is this site?</h3>
         <p>A daily-rebuilt set of charts that turn the UK Low Carbon Contracts Company dataset into a clear picture of what Contracts for Difference actually cost and deliver.</p>
       </aside>

       <p class="source-line">Source: LCCC Actual CfD Generation and Avoided GHG Emissions dataset.</p>
       ```
    6. Append to `.gitignore`:
       ```
       # Observable Framework build
       node_modules/
       dist/
       .observablehq/cache/
       ```
    7. Run `npx @observablehq/framework build` to prove the build completes. On success, verify `dist/index.html` exists and contains "CfD Visualiser".
  </action>
  <verify>
    <automated>npm ci &amp;&amp; npx @observablehq/framework build &amp;&amp; grep -q "CfD Visualiser" dist/index.html &amp;&amp; grep -q "okabe" src/assets/custom.css</automated>
  </verify>
  <acceptance_criteria>
    - `npx @observablehq/framework build` exits 0
    - `test -f dist/index.html` succeeds
    - `grep -q "CfD Visualiser" dist/index.html` succeeds
    - `grep -q '"@observablehq/framework": "1.13.4"' package.json` succeeds
    - `grep -q "#0072B2" src/assets/custom.css` succeeds
    - `grep -q "#E69F00" src/assets/custom.css` succeeds
    - `grep -q "#D55E00" src/assets/custom.css` succeeds
    - `grep -q "#009E73" src/assets/custom.css` succeeds
    - `grep -q "720px" src/assets/custom.css` succeeds
    - `grep -q "44px" src/assets/custom.css` succeeds
    - `test -f src/assets/pico.min.css` succeeds AND `[ $(wc -c < src/assets/pico.min.css) -gt 5000 ]` succeeds
  </acceptance_criteria>
  <done>
    Framework site builds, shell renders wordmark, Pico + custom tokens applied.
  </done>
</task>

<task type="auto">
  <name>Task 2: Editorial content — glossary + captions JSON seeded with CHART-01 entry</name>
  <files>src/content/glossary.json, src/content/captions.json</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-UI-SPEC.md (Copywriting Contract section — verbatim strings)
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (CHART-01 Specification: EDIT-01 + EDIT-04 drafts lines 610-612)
  </read_first>
  <behavior>
    - `glossary.json` parses as valid JSON and contains keys: `CfD`, `Strike price`, `Reference price`, `IMRP`, `Allocation round`, `Investment Contract` (the last resolves RESEARCH Open Q7 — label deferral to Phase 2)
    - `captions.json` parses as valid JSON with top-level key `chart-3c` containing nested keys `caption`, `source_name`, `source_url`, `boxout`
    - `captions.json` `chart-3c.caption` contains no word from the forbidden set (EDIT-05)
    - `captions.json` `chart-3c.source_url` is exactly `https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions`
  </behavior>
  <action>
    1. Create `src/content/glossary.json` with verbatim strings from UI-SPEC Copywriting Contract glossary row:
       ```json
       {
         "CfD": "Contract for Difference — a government scheme that guarantees renewable generators a fixed price per MWh.",
         "Strike price": "The guaranteed £/MWh a generator is paid under its CfD.",
         "Reference price": "The market price the CfD is measured against.",
         "IMRP": "Intermittent Market Reference Price — the wholesale benchmark used for wind and solar.",
         "Allocation round": "A government auction round in which CfDs were awarded.",
         "Investment Contract": "Pre-AR1 legacy scheme (2014) — CfDs awarded before the formal allocation rounds began. Shown under the raw label in v1; a clearer public-facing label is deferred to Phase 2 (resolves RESEARCH Open Q7)."
       }
       ```
    2. Create `src/content/captions.json`:
       ```json
       {
         "chart-3c": {
           "caption": "CfD strike prices have tracked above wholesale prices in every year except 2022 — consumers paid the gap.",
           "source_name": "LCCC Actual CfD Generation and Avoided GHG Emissions",
           "source_url": "https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions",
           "boxout": "The strike price is what generators are guaranteed per unit of electricity. The market reference price is the going wholesale rate. Consumers pay the difference through their bills — that gap is the subsidy."
         }
       }
       ```
  </action>
  <verify>
    <automated>uv run python -c "import json; g=json.load(open('src/content/glossary.json')); c=json.load(open('src/content/captions.json')); assert 'CfD' in g and 'IMRP' in g; assert c['chart-3c']['source_url'].startswith('https://dp.lowcarboncontracts.uk'); print('ok')"</automated>
  </verify>
  <acceptance_criteria>
    - `uv run python -c "import json; json.load(open('src/content/glossary.json'))"` exits 0
    - `uv run python -c "import json; json.load(open('src/content/captions.json'))"` exits 0
    - `grep -q "IMRP" src/content/glossary.json` succeeds
    - `grep -q "Allocation round" src/content/glossary.json` succeeds
    - `grep -q "Investment Contract" src/content/glossary.json` succeeds (Q7 deferral note)
    - `grep -q "chart-3c" src/content/captions.json` succeeds
    - `grep -qi "scandal\|waste\|outrageous\|broken\|unfair\|disaster\|rip-off" src/content/captions.json` does NOT succeed (returns non-zero)
  </acceptance_criteria>
  <done>
    Editorial content seeded; downstream CHART-01 page reads these files verbatim.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: pipeline/editorial.py EDIT-05 grammar linter + test_editorial_grammar.py</name>
  <files>pipeline/editorial.py, tests/test_editorial_grammar.py, tests/fixtures/captions_valid.json, tests/fixtures/captions_invalid.json</files>
  <read_first>
    - src/content/captions.json (just created — real file under test)
    - .planning/phases/01-pipeline-first-chart/01-UI-SPEC.md (Editorial grammar rule EDIT-05 paragraph)
    - .planning/REQUIREMENTS.md (EDIT-05 definition)
  </read_first>
  <behavior>
    - `lint_caption("Consumers paid the gap")` returns `[]` (empty)
    - `lint_caption("This is a scandal and a waste")` returns `["scandal", "waste"]` (order-insensitive; both present)
    - `lint_caption("waste-heat recovery")` returns `["waste"]` (word-boundary match; hyphen counts as boundary)
    - `lint_caption("wasted")` returns `[]` (does NOT match — must be exact word, not substring)
    - Case-insensitive: `lint_caption("Scandal")` returns `["scandal"]`
    - `lint_captions_file(captions_valid.json)` returns `{}`
    - `lint_captions_file(captions_invalid.json)` returns dict with at least one entry
    - `lint_captions_file(Path("src/content/captions.json"))` returns `{}` (real captions pass)
    - Boxout body is excluded from lint (UI-SPEC: editorial framing allowed in boxout, forbidden only in captions/titles) — linter only inspects the `caption` field
  </behavior>
  <action>
    1. Create `pipeline/editorial.py`:
       ```python
       """EDIT-05 grammar linter: enforce factual-only chart captions.

       The UI-SPEC editorial grammar rule forbids loaded framing words inside
       chart captions, titles, axis labels, and tooltips. Boxouts and prose
       may use editorial voice.
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

       # Word-boundary regex; allow hyphenated compounds (e.g. "rip-off"), word-boundary
       # for single words (so "wasted" is not flagged).
       _WORD_RE = re.compile(r"\b(\w[\w-]*)\b", re.IGNORECASE)

       def lint_caption(text: str) -> list[str]:
           tokens = {m.group(1).lower() for m in _WORD_RE.finditer(text)}
           return sorted(tokens & FORBIDDEN_WORDS)

       def lint_captions_file(path: Path) -> dict[str, list[str]]:
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
       ```
    2. Create `tests/fixtures/captions_valid.json`:
       ```json
       {
         "test-a": {
           "caption": "Consumers paid the gap in every year except 2022.",
           "boxout": "This represents systematic waste by any measure."
         },
         "test-b": {
           "caption": "Strike prices exceeded market prices in 96% of months.",
           "boxout": ""
         }
       }
       ```
       (Note: `waste` in the boxout is legal; linter only checks `caption`.)
    3. Create `tests/fixtures/captions_invalid.json`:
       ```json
       {
         "bad-a": {
           "caption": "This is a scandal that exposes systemic waste.",
           "boxout": ""
         },
         "bad-b": {
           "caption": "A Rip-Off for consumers.",
           "boxout": ""
         }
       }
       ```
    4. Create `tests/test_editorial_grammar.py`:
       - `test_factual_caption_passes`: `assert lint_caption("Consumers paid the gap") == []`
       - `test_scandal_and_waste_both_flagged`: `assert set(lint_caption("This is a scandal and a waste")) == {"scandal", "waste"}`
       - `test_word_boundary_hyphen`: `assert lint_caption("waste-heat recovery") == ["waste"]`
       - `test_substring_not_flagged`: `assert lint_caption("wasted") == []` AND `assert lint_caption("scandalous") == []`
       - `test_case_insensitive`: `assert lint_caption("Scandal") == ["scandal"]`
       - `test_rip_off_hyphenated`: `assert lint_caption("A rip-off for consumers") == ["rip-off"]`
       - `test_valid_fixture_file_passes`: `assert lint_captions_file(Path("tests/fixtures/captions_valid.json")) == {}`
       - `test_invalid_fixture_file_fails`: result dict has keys `bad-a` and `bad-b`; `bad-a` contains both `scandal` and `waste`; `bad-b` contains `rip-off`
       - `test_real_captions_file_passes`: `assert lint_captions_file(Path("src/content/captions.json")) == {}`
       - `test_boxout_not_linted`: explicit test confirming `captions_valid.json` `test-a` (which has `waste` in boxout) still passes
  </action>
  <verify>
    <automated>uv run pytest tests/test_editorial_grammar.py -x -q &amp;&amp; uv run python -m pipeline.editorial src/content/captions.json</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_editorial_grammar.py -x -q` exits 0
    - `uv run python -m pipeline.editorial src/content/captions.json` exits 0
    - `uv run python -m pipeline.editorial tests/fixtures/captions_invalid.json` exits 1
    - `grep -q "FORBIDDEN_WORDS" pipeline/editorial.py` succeeds
    - `grep -q "rip-off" pipeline/editorial.py` succeeds
    - Test file defines at least 10 test functions covering behavior bullets
    - Full phase suite still green: `uv run pytest tests/ -x -q` exits 0
  </acceptance_criteria>
  <done>
    EDIT-05 linter enforced by tests; real captions file passes; CLI usable from CI.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| author -> captions.json | Editorial input; must pass EDIT-05 lint before build |
| framework build -> dist/ | Static output; no runtime input; no XSS surface from user data |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-03-01 | Tampering | src/content/captions.json | mitigate | EDIT-05 linter run in CI (Plan 01-05 wires into workflow); any loaded-word commit fails CI |
| T-01-03-02 | Information Disclosure | src/assets/pico.min.css | accept | Vendored public CSS; no secrets; file integrity acceptable at MIN_BYTES sanity check |
| T-01-03-03 | Tampering | Observable Framework build | accept | Framework 1.13.4 pinned in package.json; npm-lockfile committed; future SRI/SBOM is a v2 concern |
</threat_model>

<verification>
- `npx @observablehq/framework build` exits 0
- `uv run pytest tests/test_editorial_grammar.py -x -q` exits 0
- `uv run python -m pipeline.editorial src/content/captions.json` exits 0
- Full suite green: `uv run pytest tests/ -x -q` exits 0
</verification>

<success_criteria>
- Framework builds; wordmark visible; Pico + custom CSS linked
- Okabe-Ito palette tokens defined; 720px measure + 44px tap targets enforced
- Glossary + captions JSON exist with verbatim UI-SPEC strings
- EDIT-05 linter green on real captions, red on invalid fixture
</success_criteria>

<output>
After completion, create `.planning/phases/01-pipeline-first-chart/01-03-SUMMARY.md` documenting: Framework version actually installed, Pico CSS variant used (classless vs classed), linter forbidden-word list, any UI-SPEC copy deviations discovered.
</output>
