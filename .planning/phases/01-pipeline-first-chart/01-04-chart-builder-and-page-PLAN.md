---
phase: 01-pipeline-first-chart
plan: 04
type: execute
wave: 3
depends_on: ["01-01", "01-02", "01-03"]
files_modified:
  - pipeline/build_chart_3c.py
  - pipeline/build_meta.py
  - pipeline/__main__.py
  - src/data/chart-3c.json.py
  - src/data/meta.json.py
  - src/charts/scissors.md
  - src/index.md
  - src/observablehq.config.js
  - tests/test_build_chart_3c.py
  - tests/test_build_meta.py
  - tests/test_site_artefacts.py
  - tests/fixtures/cfd_sample_expected_3c.json
autonomous: true
requirements: [CHART-01, EDIT-01, EDIT-02, EDIT-04, OPS-03, OPS-04]
tags: [chart, observable-plot, view-model, accessibility]

must_haves:
  truths:
    - "pipeline/build_chart_3c.py produces a JSON view-model with shape {month, round, generation_mwh, strike, market, payments_gbp} aggregated by IMRP-only monthly grain"
    - "Σ payments_gbp across the view-model equals Σ CFD_Payments_GBP in raw_generation (IMRP rows only) within ±0.01%"
    - "The 2022 calendar year contains at least one month with payments_gbp < 0 (clawback invariant — sign preserved end-to-end)"
    - "src/charts/scissors.md renders two Plot lines (strike + market) plus an area fill for the subsidy gap, with Okabe-Ito colours from custom.css tokens"
    - "The deployed page shows caption, source line with dataset URL and last_updated stamp, 'What does this mean?' boxout, round-toggle control, and a 'Download this chart's data (JSON)' link pointing to /data/chart-3c.json"
    - "`npx @observablehq/framework build` produces dist/data/chart-3c.json and dist/charts/scissors.html; the chart page references the JSON and the glossary"
    - "pipeline/__main__.py runs build_chart_3c and build_meta after store in the same `python -m pipeline` invocation"
  artifacts:
    - path: "pipeline/build_chart_3c.py"
      provides: "build(db_path, out_path) — generation-weighted monthly aggregate writer"
      contains: "Reference_Type = 'IMRP'"
    - path: "pipeline/build_meta.py"
      provides: "build(db_path, captions_path, out_path) — writes last_updated, row_count, pipeline_version, caption"
      contains: "last_updated"
    - path: "src/charts/scissors.md"
      provides: "CHART-01 page with Plot code + editorial layout per UI-SPEC"
      contains: "chart-3c.json"
    - path: "src/data/chart-3c.json.py"
      provides: "Framework data loader invoking pipeline.build_chart_3c (dev ergonomics)"
    - path: "src/data/meta.json.py"
      provides: "Framework data loader invoking pipeline.build_meta"
    - path: "tests/test_build_chart_3c.py"
      provides: "Schema + payments tie-out + 2022 clawback invariant tests"
    - path: "tests/test_build_meta.py"
      provides: "meta.json shape + caption-present tests"
    - path: "tests/test_site_artefacts.py"
      provides: "Post-build dist/ smoke tests: JSON artefact exists, page references it, no third-party trackers"
    - path: "tests/fixtures/cfd_sample_expected_3c.json"
      provides: "Golden view-model regression fixture computed from cfd_sample.csv"
  key_links:
    - from: "src/charts/scissors.md"
      to: "src/data/chart-3c.json"
      via: "FileAttachment('../data/chart-3c.json').json()"
      pattern: "chart-3c\\.json"
    - from: "src/charts/scissors.md"
      to: "src/data/meta.json"
      via: "FileAttachment('../data/meta.json').json()"
      pattern: "meta\\.json"
    - from: "src/charts/scissors.md"
      to: "src/content/captions.json"
      via: "FileAttachment('../content/captions.json').json()"
      pattern: "captions\\.json"
    - from: "pipeline/__main__.py"
      to: "pipeline.build_chart_3c.build"
      via: "called after upsert"
      pattern: "build_chart_3c"
    - from: "pipeline/build_chart_3c.py"
      to: "data/cfd.duckdb"
      via: "duckdb.connect(db_path, read_only=True)"
      pattern: "read_only=True"
---

<objective>
Derive the CHART-01 view-model from DuckDB, wire it into an Observable Framework page, and make the whole path build deterministically. This is the first user-visible output: a scissors chart that renders from a pre-baked JSON, with caption + source + boxout + round toggle + download link per UI-SPEC — and an end-to-end test that proves the yearly payments tie out within 0.01%.

Purpose: Everything upstream was infrastructure. This plan turns it into a chart a non-specialist can read on a mobile phone and walk away informed. It is the phase's proof-of-value.

Output: Chart-model builder, meta builder, Framework chart page, pipeline main integration, three test modules, golden regression fixture.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/phases/01-pipeline-first-chart/01-RESEARCH.md
@.planning/phases/01-pipeline-first-chart/01-UI-SPEC.md
@.planning/phases/01-pipeline-first-chart/01-VALIDATION.md
@.planning/phases/01-pipeline-first-chart/01-01-SUMMARY.md
@.planning/phases/01-pipeline-first-chart/01-02-SUMMARY.md
@.planning/phases/01-pipeline-first-chart/01-03-SUMMARY.md
@pipeline/units.py
@pipeline/store.py
@pipeline/__main__.py
@src/observablehq.config.js
@src/content/captions.json

<interfaces>
<!-- New contracts this plan creates -->

```python
# pipeline/build_chart_3c.py
def build(db_path: str | Path, out_path: str | Path) -> dict:
    """Read raw_generation, filter to Reference_Type='IMRP',
    compute generation-weighted monthly aggregates per allocation round,
    write view-model JSON to out_path, return the dict written."""

# View-model JSON schema (list of records):
# [
#   {
#     "month": "YYYY-MM",         # ISO month string
#     "round": "Allocation Round 1" | "AR2" | ... | "Investment Contract",
#     "generation_mwh": float,    # Σ CFD_Generation_MWh
#     "strike": float,            # generation-weighted mean £/MWh
#     "market": float,            # generation-weighted mean £/MWh
#     "payments_gbp": float       # Σ CFD_Payments_GBP (signed)
#   },
#   ...
# ]
```

```python
# pipeline/build_meta.py
def build(
    db_path: str | Path,
    captions_path: str | Path,
    out_path: str | Path,
    *,
    pipeline_version: str | None = None,
    now_iso: str | None = None,
) -> dict: ...
# Writes: {
#   "last_updated": "2026-04-14T06:30:00Z",
#   "row_count": 103470,
#   "max_settlement_date": "2026-03-30",
#   "pipeline_version": "<git-sha or 'dev'>",
#   "schema_version": "1.0",
#   "captions": { ...copy of captions.json... }
# }
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: pipeline/build_chart_3c.py view-model builder + golden-fixture tests (CHART-01 + tie-out)</name>
  <files>pipeline/build_chart_3c.py, tests/test_build_chart_3c.py, tests/fixtures/cfd_sample_expected_3c.json</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (CHART-01 Specification lines 569-610; generation-weighted aggregate example lines 470-497; Nyquist Sampling Strategy invariants)
    - pipeline/store.py (table name = raw_generation, PK = (Settlement_Date, CfD_ID))
    - tests/fixtures/cfd_sample.csv
    - .planning/phases/01-pipeline-first-chart/01-VALIDATION.md (Invariants table)
  </read_first>
  <behavior>
    - `build(db_path, out_path)` writes a JSON array whose length equals the number of distinct (month, allocation_round) combinations in IMRP rows
    - Every record has exactly six keys: `month`, `round`, `generation_mwh`, `strike`, `market`, `payments_gbp`
    - `month` is a string matching regex `^\d{4}-\d{2}$`
    - For every record, `generation_mwh > 0` (zero-generation cells should not appear; NULLIF in SQL prevents divide-by-zero)
    - The sum of `payments_gbp` across the output equals the sum of `CFD_Payments_GBP` in `raw_generation` filtered to `Reference_Type='IMRP'` within ±0.01%
    - At least one record in calendar year 2022 has `payments_gbp < 0` (clawback invariant)
    - In >= 95% of records, `strike > market` (scissors shape)
    - Output is stable (idempotent): running build twice produces byte-identical JSON (sorted keys, sorted record order by (month, round))
    - The view-model matches a committed golden fixture within numeric tolerance ±0.001 on every numeric field
  </behavior>
  <action>
    1. Create `pipeline/build_chart_3c.py`:
       ```python
       """CHART-01 scissors view-model builder (CHART-01)."""
       from __future__ import annotations
       import json
       from pathlib import Path
       import duckdb

       _SQL = """
       SELECT
           strftime('%Y-%m', Settlement_Date) AS month,
           Allocation_round AS round,
           SUM(CFD_Generation_MWh) AS generation_mwh,
           SUM(Strike_Price_GBP_Per_MWh * CFD_Generation_MWh)
             / NULLIF(SUM(CFD_Generation_MWh), 0) AS strike,
           SUM(Market_Reference_Price_GBP_Per_MWh * CFD_Generation_MWh)
             / NULLIF(SUM(CFD_Generation_MWh), 0) AS market,
           SUM(CFD_Payments_GBP) AS payments_gbp
       FROM raw_generation
       WHERE Reference_Type = 'IMRP'
       GROUP BY 1, 2
       HAVING SUM(CFD_Generation_MWh) > 0
       ORDER BY 1, 2;
       """

       def build(db_path: str | Path, out_path: str | Path) -> list[dict]:
           con = duckdb.connect(str(db_path), read_only=True)
           try:
               rows = con.execute(_SQL).fetchall()
           finally:
               con.close()
           cols = ["month", "round", "generation_mwh", "strike", "market", "payments_gbp"]
           view_model = [
               {c: (float(v) if isinstance(v, (int, float)) else v)
                for c, v in zip(cols, r)}
               for r in rows
           ]
           # Round numeric fields to 6 dp to stabilise golden fixture
           for rec in view_model:
               for k in ("generation_mwh", "strike", "market", "payments_gbp"):
                   rec[k] = round(rec[k], 6)
           Path(out_path).parent.mkdir(parents=True, exist_ok=True)
           Path(out_path).write_text(
               json.dumps(view_model, separators=(",", ":"), sort_keys=True)
           )
           return view_model
       ```
    2. Generate the golden fixture once:
       - Run a one-shot Python snippet: load `tests/fixtures/cfd_sample.csv` via `pipeline.validate.read_and_validate`, upsert into a tmp DuckDB, invoke `build`, write output to `tests/fixtures/cfd_sample_expected_3c.json`.
       - Commit the fixture.
    3. Create `tests/test_build_chart_3c.py`:
       - `test_schema_shape(tmp_path, sample_csv_path)`: build end-to-end from fixture; assert each record has exactly {month, round, generation_mwh, strike, market, payments_gbp} keys.
       - `test_month_format(tmp_path, sample_csv_path)`: all month strings match `^\d{4}-\d{2}$`.
       - `test_generation_positive(tmp_path, sample_csv_path)`: every record's generation_mwh > 0.
       - `test_payments_tie_out(tmp_path, sample_csv_path)`: Σ view_model.payments_gbp equals raw_generation IMRP-filtered Σ CFD_Payments_GBP within ±0.01% (use DuckDB to compute expected).
       - `test_2022_clawback_present(tmp_path, sample_csv_path)`: at least one record with month starting "2022-" has payments_gbp < 0. (If fixture doesn't include 2022 clawback rows in IMRP after aggregation, flag this — the Task 1 fixture-generation step in Plan 01-01 was required to include 2022 negative-payments rows; if this test fails, fix the fixture, do not loosen the invariant.)
       - `test_scissors_shape(tmp_path, sample_csv_path)`: >= 95% of records have strike > market.
       - `test_idempotent_bytes(tmp_path, sample_csv_path)`: build twice to two different paths; files are byte-identical.
       - `test_matches_golden_fixture(tmp_path, sample_csv_path)`: build, load, compare against `tests/fixtures/cfd_sample_expected_3c.json` record-by-record with numeric tolerance 0.001.
  </action>
  <verify>
    <automated>uv run pytest tests/test_build_chart_3c.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_build_chart_3c.py -x -q` exits 0
    - `test -f tests/fixtures/cfd_sample_expected_3c.json` succeeds
    - `grep -q "Reference_Type = 'IMRP'" pipeline/build_chart_3c.py` succeeds
    - `grep -q "NULLIF" pipeline/build_chart_3c.py` succeeds
    - `grep -q "read_only=True" pipeline/build_chart_3c.py` succeeds
    - Test file defines at least 8 test functions covering behavior bullets
    - `uv run python -c "import json; rows=json.load(open('tests/fixtures/cfd_sample_expected_3c.json')); assert len(rows) > 10"` exits 0
  </acceptance_criteria>
  <done>
    View-model builder green; tie-out proven; 2022 clawback sign preserved end-to-end.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: pipeline/build_meta.py + test_build_meta.py + wire into pipeline/__main__.py</name>
  <files>pipeline/build_meta.py, pipeline/__main__.py, tests/test_build_meta.py, src/data/chart-3c.json.py, src/data/meta.json.py</files>
  <read_first>
    - pipeline/__main__.py (from Plan 01-02 — extend, do not rewrite)
    - pipeline/build_chart_3c.py (just created)
    - src/content/captions.json
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (Artefact versioning section ~line 738)
  </read_first>
  <behavior>
    - `build(db_path, captions_path, out_path)` writes a JSON object with keys: `last_updated`, `row_count`, `max_settlement_date`, `pipeline_version`, `schema_version`, `captions`
    - `last_updated` is an ISO-8601 UTC timestamp ending in `Z`
    - `row_count` equals `SELECT COUNT(*) FROM raw_generation`
    - `max_settlement_date` equals `SELECT MAX(Settlement_Date)` as YYYY-MM-DD string
    - `schema_version` is the literal string `"1.0"`
    - `pipeline_version` is either a git SHA (7+ hex chars) or the literal `"dev"`
    - `captions` is a deep copy of the content of `captions.json`
    - `python -m pipeline` runs fetch -> validate -> store -> build_chart_3c -> build_meta -> healthcheck in that order; failure in chart-model or meta build exits non-zero with distinct code
    - Framework data loaders `src/data/chart-3c.json.py` and `src/data/meta.json.py` emit the same output to stdout when run via `python src/data/chart-3c.json.py`
  </behavior>
  <action>
    1. Create `pipeline/build_meta.py`:
       ```python
       """Meta artefact builder: last_updated, versions, captions (EDIT-02)."""
       from __future__ import annotations
       import datetime as dt
       import json
       import os
       import subprocess
       from pathlib import Path
       import duckdb

       SCHEMA_VERSION = "1.0"

       def _git_sha() -> str:
           try:
               out = subprocess.check_output(
                   ["git", "rev-parse", "--short", "HEAD"],
                   stderr=subprocess.DEVNULL, timeout=5
               )
               return out.decode().strip() or "dev"
           except Exception:
               return "dev"

       def build(
           db_path: str | Path,
           captions_path: str | Path,
           out_path: str | Path,
           *,
           pipeline_version: str | None = None,
           now_iso: str | None = None,
       ) -> dict:
           con = duckdb.connect(str(db_path), read_only=True)
           try:
               row_count = con.execute(
                   "SELECT COUNT(*) FROM raw_generation"
               ).fetchone()[0]
               max_date = con.execute(
                   "SELECT CAST(MAX(Settlement_Date) AS VARCHAR) FROM raw_generation"
               ).fetchone()[0]
           finally:
               con.close()
           captions = json.loads(Path(captions_path).read_text())
           meta = {
               "last_updated": now_iso or dt.datetime.now(dt.timezone.utc)
                                                 .strftime("%Y-%m-%dT%H:%M:%SZ"),
               "row_count": int(row_count),
               "max_settlement_date": max_date,
               "pipeline_version": pipeline_version or _git_sha(),
               "schema_version": SCHEMA_VERSION,
               "captions": captions,
           }
           Path(out_path).parent.mkdir(parents=True, exist_ok=True)
           Path(out_path).write_text(json.dumps(meta, separators=(",", ":"),
                                                sort_keys=True))
           return meta
       ```
    2. Extend `pipeline/__main__.py` — insert between the `upsert` block and the healthcheck block:
       ```python
       from pipeline.build_chart_3c import build as build_chart_3c
       from pipeline.build_meta import build as build_meta

       EXIT_CHART_BUILD_FAILED = 5

       # ... inside run(), after upsert succeeds:
       try:
           build_chart_3c(db_path, Path("src/data/chart-3c.json"))
           build_meta(
               db_path,
               Path("src/content/captions.json"),
               Path("src/data/meta.json"),
           )
       except Exception as e:
           print(f"ERROR: chart/meta build failed: {e}", file=sys.stderr)
           return EXIT_CHART_BUILD_FAILED
       ```
    3. Create `src/data/chart-3c.json.py` (Framework data loader for local dev):
       ```python
       #!/usr/bin/env python3
       """Framework data loader — emit view-model JSON to stdout."""
       import json
       import sys
       import tempfile
       from pathlib import Path
       from pipeline.build_chart_3c import build

       out = Path(tempfile.mkstemp(suffix=".json")[1])
       build("data/cfd.duckdb", out)
       sys.stdout.write(out.read_text())
       ```
    4. Create `src/data/meta.json.py`:
       ```python
       #!/usr/bin/env python3
       import sys, tempfile
       from pathlib import Path
       from pipeline.build_meta import build

       out = Path(tempfile.mkstemp(suffix=".json")[1])
       build("data/cfd.duckdb", "src/content/captions.json", out)
       sys.stdout.write(out.read_text())
       ```
    5. Create `tests/test_build_meta.py`:
       - `test_meta_keys_present(fresh_duckdb, sample_csv_path, tmp_path)`: upsert fixture; build meta; assert all 6 keys.
       - `test_last_updated_iso_z`: regex match `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`.
       - `test_row_count_matches_db`.
       - `test_max_settlement_date_format`: matches `^\d{4}-\d{2}-\d{2}$`.
       - `test_schema_version_literal`: equals "1.0".
       - `test_captions_deep_copy`: captions payload equals `json.loads(Path("src/content/captions.json").read_text())`.
       - `test_pipeline_version_override`: passing `pipeline_version="abc1234"` uses that value.
       - `test_main_integration(tmp_path, monkeypatch)`: run `pipeline.__main__.run(...)` with mocked transport; assert `src/data/chart-3c.json` (or a redirected tmp path) and `src/data/meta.json` both exist with valid JSON.
  </action>
  <verify>
    <automated>uv run pytest tests/test_build_meta.py tests/test_build_chart_3c.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_build_meta.py -x -q` exits 0
    - `grep -q "from pipeline.build_chart_3c" pipeline/__main__.py` succeeds
    - `grep -q "from pipeline.build_meta" pipeline/__main__.py` succeeds
    - `grep -q "EXIT_CHART_BUILD_FAILED" pipeline/__main__.py` succeeds
    - `grep -q "last_updated" pipeline/build_meta.py` succeeds
    - `grep -q "schema_version" pipeline/build_meta.py` succeeds
    - Test file defines at least 8 test functions
    - `test -f src/data/chart-3c.json.py` succeeds
    - `test -f src/data/meta.json.py` succeeds
  </acceptance_criteria>
  <done>
    Meta artefact shape locked; pipeline CLI runs end-to-end including chart + meta build; Framework data loaders wired.
  </done>
</task>

<task type="auto">
  <name>Task 3: src/charts/scissors.md Plot page + index link + post-build smoke tests (CHART-01 UX; OPS-04 download; OPS-03 a11y)</name>
  <files>src/charts/scissors.md, src/index.md, src/observablehq.config.js, tests/test_site_artefacts.py</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-UI-SPEC.md (entire file — page shell, interactions, copywriting, a11y)
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (Pattern 3 Framework page example lines 350-390)
    - src/data/chart-3c.json (produced by a prior test run) — inspect shape before writing Plot code
    - src/content/captions.json
    - src/observablehq.config.js (from Plan 01-03)
  </read_first>
  <behavior>
    - `npx @observablehq/framework build` with `data/cfd.duckdb` populated produces `dist/charts/scissors.html` and `dist/data/chart-3c.json`
    - The built page contains the EDIT-01 caption string verbatim from captions.json
    - The built page contains the source dataset URL `https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions`
    - The built page contains a literal anchor `<a ... href="/data/chart-3c.json"` with text containing "Download" and "JSON"
    - The built page contains a "What does this mean?" heading (EDIT-04 boxout)
    - The built page contains round-toggle controls labelled `All`, `Investment Contract`, `AR1`, `AR2`, `AR4`, `AR5`
    - The built page does NOT contain any `<script>` tag referencing known-tracker domains (`google-analytics.com`, `googletagmanager.com`, `facebook.net`, `doubleclick.net`, `mixpanel.com`, `hotjar.com`)
    - The built page contains aria-label or figure/aria-describedby references for the chart (OPS-03 a11y)
    - `dist/data/chart-3c.json` parses as valid JSON and is identical to the file the builder produced
    - `src/index.md` links to `charts/scissors`
  </behavior>
  <action>
    1. Create `src/charts/scissors.md` per UI-SPEC Copywriting Contract. Use Framework Markdown with inline JS cells:
       ```md
       ---
       title: Strike vs market — CfD scissors
       toc: false
       ---

       # UK CfD: what consumers pay vs the market

       ```js
       const data = FileAttachment("../data/chart-3c.json").json();
       const meta = FileAttachment("../data/meta.json").json();
       const captions = FileAttachment("../content/captions.json").json();
       ```

       ```js
       const c = captions["chart-3c"];
       ```

       <p class="caption">${c.caption}</p>

       ```js
       const rounds = ["All", "Investment Contract", "Allocation Round 1",
                       "Allocation Round 2", "Allocation Round 4", "Allocation Round 5"];
       const selectedRound = view(Inputs.radio(rounds, {
         label: "Show allocation rounds:",
         value: "All"
       }));
       ```

       ```js
       const filtered = selectedRound === "All"
         ? rollupAllRounds(data)
         : data.filter(d => d.round === selectedRound);

       function rollupAllRounds(rows) {
         const byMonth = d3.rollups(
           rows,
           v => ({
             strike: d3.sum(v, d => d.strike * d.generation_mwh) /
                     d3.sum(v, d => d.generation_mwh),
             market: d3.sum(v, d => d.market * d.generation_mwh) /
                     d3.sum(v, d => d.generation_mwh),
             payments_gbp: d3.sum(v, d => d.payments_gbp),
             generation_mwh: d3.sum(v, d => d.generation_mwh)
           }),
           d => d.month
         );
         return byMonth.map(([month, agg]) => ({month, round: "All", ...agg}));
       }
       ```

       <figure class="chart" role="img"
               aria-labelledby="chart-3c-title"
               aria-describedby="chart-3c-caption">
         <div id="chart-3c-title" hidden>
           Strike price vs market reference price over time.
         </div>

       ```js
       display(Plot.plot({
         marginLeft: 60,
         marginBottom: 40,
         style: { fontSize: "14px" },
         x: { label: "Settlement month", type: "utc", tickFormat: "%Y" },
         y: { label: "£ / MWh", grid: true },
         color: {
           legend: true,
           domain: ["Strike price", "Market reference price"],
           range: ["var(--okabe-blue)", "var(--okabe-orange)"]
         },
         marks: [
           Plot.areaY(filtered, {
             x: d => new Date(d.month + "-01"),
             y1: "market", y2: "strike",
             fill: d => d.strike >= d.market
                        ? "var(--okabe-vermillion)"
                        : "var(--okabe-green)",
             fillOpacity: 0.18
           }),
           Plot.lineY(filtered, {
             x: d => new Date(d.month + "-01"),
             y: "strike", stroke: "var(--okabe-blue)", strokeWidth: 2,
             tip: true
           }),
           Plot.lineY(filtered, {
             x: d => new Date(d.month + "-01"),
             y: "market", stroke: "var(--okabe-orange)", strokeWidth: 2,
             tip: true
           }),
           Plot.ruleY([0])
         ],
         width: 720,
         height: 480
       }));
       ```

         <figcaption id="chart-3c-caption">${c.caption}</figcaption>
       </figure>

       <p class="source-line">
         Source: <a href="${c.source_url}">${c.source_name}</a>.
         Last updated: ${meta.last_updated}.
       </p>

       <aside class="boxout">
         <h3>What does this mean?</h3>
         <p>${c.boxout}</p>
       </aside>

       <p><a class="download" href="/data/chart-3c.json" download>Download this chart's data (JSON)</a></p>
       ```
    2. Update `src/index.md` to link to the chart page:
       - Replace the placeholder paragraph with a link: `[View the scissors chart](charts/scissors)`.
       - Keep wordmark + boxout + source line.
    3. Update `src/observablehq.config.js` `pages` array to include `{ name: "Scissors", path: "/charts/scissors" }`.
    4. Create `tests/test_site_artefacts.py` (smoke tests run AFTER `npx framework build`):
       - All tests first check if `dist/` exists; if not, they `pytest.skip("run npx framework build first")`.
       - `test_dist_chart_page_exists`: `Path("dist/charts/scissors/index.html").exists()` OR `Path("dist/charts/scissors.html").exists()` (Framework may use either; test accepts either).
       - `test_chart_json_artefact_exists`: `Path("dist/data/chart-3c.json").exists()` AND is valid JSON.
       - `test_page_contains_caption`: the scissors html contains the `chart-3c` caption string from `src/content/captions.json`.
       - `test_page_contains_source_url`: contains `https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions`.
       - `test_page_contains_download_link`: contains `href="/data/chart-3c.json"` or `href="../data/chart-3c.json"`.
       - `test_page_contains_boxout_heading`: contains `What does this mean?`.
       - `test_page_contains_round_labels`: contains `Investment Contract`, `Allocation Round 1`, `Allocation Round 5`.
       - `test_no_third_party_trackers`: scissors html does not contain any of: `google-analytics.com`, `googletagmanager.com`, `facebook.net`, `doubleclick.net`, `mixpanel.com`, `hotjar.com`.
       - `test_aria_labels_present`: contains `aria-labelledby` or `aria-label` referencing the chart.
    5. To run the verification: first seed a populated `data/cfd.duckdb` by running the pipeline against the fixture (via `python -m pipeline` with a mock transport is too invasive for this step — instead add a one-shot test helper that calls `upsert` with the fixture directly, OR require the verify step below to run build after pipeline against fixture).
  </action>
  <verify>
    <automated>uv run python -c "from pathlib import Path; from pipeline.validate import read_and_validate; from pipeline.store import upsert; from pipeline.build_chart_3c import build as bc; from pipeline.build_meta import build as bm; Path('data').mkdir(exist_ok=True); Path('src/data').mkdir(exist_ok=True); df = read_and_validate(Path('tests/fixtures/cfd_sample.csv')); upsert(df, 'data/cfd.duckdb'); bc('data/cfd.duckdb', 'src/data/chart-3c.json'); bm('data/cfd.duckdb', 'src/content/captions.json', 'src/data/meta.json'); print('seeded')" &amp;&amp; npx @observablehq/framework build &amp;&amp; uv run pytest tests/test_site_artefacts.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `npx @observablehq/framework build` exits 0
    - `test -f dist/data/chart-3c.json` succeeds
    - `uv run pytest tests/test_site_artefacts.py -x -q` exits 0
    - `grep -q "chart-3c.json" src/charts/scissors.md` succeeds
    - `grep -q "What does this mean" src/charts/scissors.md` succeeds
    - `grep -q "aria-labelledby" src/charts/scissors.md` succeeds
    - `grep -q "download" src/charts/scissors.md` succeeds
    - `grep -q "charts/scissors" src/index.md` succeeds
    - `grep -q "var(--okabe-blue)" src/charts/scissors.md` succeeds
    - `grep -q "var(--okabe-orange)" src/charts/scissors.md` succeeds
    - Full phase suite green: `uv run pytest tests/ -x -q` exits 0
    - `grep -c "allocation" dist/charts/scissors*.html || grep -c "Allocation" dist/charts/scissors*.html || find dist -name 'scissors*' -exec grep -l 'Allocation' {} \;` returns at least one match
  </acceptance_criteria>
  <done>
    Scissors page renders locally; view-model JSON downloadable; captions/source/boxout/round-toggle all present; no third-party trackers.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| DuckDB -> build_chart_3c | Read-only connection; no user input in SQL; query is hard-coded |
| build_chart_3c -> src/data/*.json | Writes to known filesystem path; content is bounded-size derived aggregate |
| dist/ -> visitor browser | Static JSON + HTML; no runtime code execution from data (Plot escapes text via D3) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-04-01 | Tampering | pipeline/build_chart_3c.py | mitigate | read_only=True DuckDB connection; SQL is hard-coded, no string interpolation of user/env data |
| T-01-04-02 | Tampering (XSS) | src/charts/scissors.md Plot rendering | mitigate | Observable Plot renders via D3 which escapes text nodes; caption string sourced from committed captions.json (linted by EDIT-05) |
| T-01-04-03 | Information Disclosure | dist/data/chart-3c.json | accept | Public dataset aggregate; no PII; OPS-04 explicitly wants it public |
| T-01-04-04 | Tampering | src/data/meta.json git-sha field | accept | pipeline_version is best-effort provenance; failure returns "dev"; not security-critical |
</threat_model>

<verification>
- End-to-end path passes: pipeline seeds DuckDB -> build_chart_3c -> build_meta -> framework build -> smoke tests
- `uv run pytest tests/ -x -q` exits 0
- `dist/data/chart-3c.json` exists and matches the view-model produced by the builder
- EDIT-01 caption, EDIT-02 source line, EDIT-04 boxout all present in built HTML
</verification>

<success_criteria>
- `python -m pipeline` runs fetch -> validate -> store -> build_chart_3c -> build_meta -> HC ping in order
- View-model tie-out passes on fixture (≤ 0.01% deviation)
- 2022 clawback sign preserved (invariant test green)
- Chart page builds; round toggle, tooltip, download link all present
- Okabe-Ito palette tokens consumed from custom.css (no hex literals in scissors.md chart colours)
- Golden fixture regression test green
</success_criteria>

<output>
After completion, create `.planning/phases/01-pipeline-first-chart/01-04-SUMMARY.md` documenting: actual view-model record count from fixture, tie-out deviation observed, any Plot/Framework quirks discovered (e.g. date parsing, legend placement), golden fixture hash.
</output>
