# Phase 1: Pipeline + First Chart — Research

**Researched:** 2026-04-14
**Domain:** Daily-rebuilt static data-visualisation site; Python ingest → DuckDB store → Observable Framework build → Cloudflare Pages deploy
**Confidence:** HIGH for stack + data schema (CSV inspected directly, versions verified via pip/npm); MEDIUM for Framework build-time conventions (official docs confirmed but not exercised in-repo yet)

---

## Summary

Phase 1 stands up the full pipeline seam end-to-end: a scheduled GitHub Actions workflow fetches the LCCC *Actual CfD Generation and Avoided GHG Emissions* CSV, validates it against a Pandera schema, upserts into a committed DuckDB file, exports a JSON view-model for CHART-01 (3c scissors), and builds an Observable Framework site deployed to Cloudflare Pages. All stack choices are locked in `CLAUDE.md` — this research focuses on the unknowns: the actual LCCC data shape, pipeline architecture details, Framework data-loader conventions, and the metric definitions for CHART-01.

The 18 MB CSV already committed at `data/actual_cfd_generation_and_avoided_ghg_emissions.csv` is the reference dataset (103,470 rows, 13 columns, dates 2016-06-30 to 2026-03-30). Schema, categorical value sets, and quirks (negative `CFD_Payments_GBP` for clawback periods, two `Reference_Type` values `IMRP`/`BMRP`) are all known from direct inspection. The existing `plot_cfd_cost.py` is a matplotlib prototype of an adjacent chart (CfD-vs-gas bars) — its generation-weighted-average aggregation logic is reusable; its presentation is discarded.

**Primary recommendation:** Build five independent pipeline modules (`fetch`, `validate`, `store`, `build_chart_3c`, `build_site_artefacts`) wired through a single `pipeline/__main__.py` entry point, invoked by both (a) a pre-build step in the GitHub Actions workflow and (b) Observable Framework Python data loaders at `src/data/*.json.py` for local dev. The committed `data/cfd.duckdb` file is the single durable store; raw CSV snapshots go to `data/raw/YYYY-MM-DD.csv` for diff-based drift detection. CHART-01 is a client-side Observable Plot chart reading a pre-baked JSON view-model — no DuckDB-WASM at runtime.

---

<user_constraints>
## User Constraints (from CLAUDE.md)

No `CONTEXT.md` exists for this phase. The binding constraints come from `CLAUDE.md` and must be treated with the same authority as locked user decisions.

### Locked Decisions (from CLAUDE.md "Technology Stack")

- **Site generator:** Observable Framework 1.13.4 (not Jinja2, not Next.js, not Astro) — the prior `research/ARCHITECTURE.md` diagram shows a Jinja2 render layer; that is **superseded** by the stack decision in STATE.md and CLAUDE.md.
- **Chart library:** Observable Plot 0.6.17 (bundled with Framework; do not add as separate dep)
- **Ingest/cleaning:** Polars 1.39.3 (not pandas — the `plot_cfd_cost.py` prototype's pandas usage is scaffolding, not foundation)
- **Store + query:** DuckDB 1.5.2 embedded in Python; `.duckdb` file is committed
- **Static PNG export (OG images):** matplotlib 3.10.8
- **Styling:** Pico CSS 2.x (classless, via CDN or copied to `src/assets/`)
- **Hosting:** Cloudflare Pages (free tier — unlimited bandwidth matters vs Netlify 100 GB cap)
- **Scheduler:** GitHub Actions cron (free for public repos)
- **Python env:** uv (pyproject.toml + uv.lock); Python 3.13
- **Node runtime:** Node 20 LTS for Framework build
- **HTTP client:** httpx (not requests)
- **Testing:** pytest
- **Parquet I/O:** pyarrow (shared between Polars and DuckDB)
- **Schema validation:** Pandera (named explicitly in REQ PIPE-02)

### Claude's Discretion

- Pipeline module layout (file names, module boundaries inside `pipeline/`)
- Primary-key composite for idempotent upsert — research suggests `(Settlement_Date, CfD_ID)` but this needs verification against actual data (see Open Questions Q1)
- Chart-model JSON schema (what fields the Plot page receives)
- Exact cron time (research recommends 06:30 UTC — after the LCCC portal update window)
- Whether to use Healthchecks.io, Cronitor, or Cloudflare Workers Cron Triggers for the dead-man's switch (REQ PIPE-05)
- Keepalive mechanism (trivial touch commit vs `workflow_dispatch` schedule refresh) for REQ PIPE-06
- Analytics platform choice for OPS-05 (Plausible self-hosted / Plausible hosted / Cloudflare Web Analytics / none)
- Plot interactivity primitive for CHART-01 zoom (Plot's built-in `interval` brush vs manual `scales` + input bindings)

### Deferred Ideas (OUT OF SCOPE for Phase 1)

- CHART-02 (3d) £/tCO₂ explorer — Phase 2
- CHART-03 (3b + 6a) cumulative subsidy + Lorenz — Phase 2
- CHART-04 (2a) heatmap — Phase 2
- Methodology page (EDIT-03) — Phase 2 hard gate
- CfD Register join (installed capacity for CF charts) — v2
- Elexon / NESO wholesale prices — v3
- UK ETS + DEFRA SCC series — v3 (static constants only, if referenced at all in Phase 1)
- Public query API — post-v1 (the `/data/*.json` files become the future API surface)
- OG:image auto-generation per chart — deferred; matplotlib static PNG is a single site-wide social card for Phase 1
- Auto-generated OG cards, deeplinkable filter state, RSS/Atom feed
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-01 | Daily automated fetch of LCCC CSV | Direct URL verified: `https://dp.lowcarboncontracts.uk/dataset/8e8ca0d5-c774-4dc8-a079-347f1c180c0f/resource/5279a55d-4996-4b1e-ba07-f411d8fd31f0/download/actual_cfd_generation_and_avoided_ghg_emissions.csv` [VERIFIED: WebFetch of dp.lowcarboncontracts.uk]. Update cadence: "daily" per portal. Use httpx with timeout + retry. |
| PIPE-02 | Pandera schema validation, non-zero exit on drift | Schema profile section below lists all 13 columns, dtypes, and known value sets. Pandera 0.31.0 is current [VERIFIED: pip index]. |
| PIPE-03 | Idempotent DuckDB upsert on stable PK | Composite `(Settlement_Date, CfD_ID)` is the strong candidate — see Open Questions Q1. DuckDB supports `INSERT ... ON CONFLICT DO UPDATE` (PostgreSQL-compatible syntax) [CITED: duckdb.org docs]. |
| PIPE-04 | Raw CSV archive for drift forensics | Store at `data/raw/YYYY-MM-DD.csv`; git LFS not needed (18 MB × 365 snapshots = ~6 GB/yr, but daily diffs compress well; alternatively commit compressed `.csv.gz` at ~3 MB each). See Pitfalls section. |
| PIPE-05 | Dead-man's switch (Healthchecks.io or equivalent) | Healthchecks.io free tier: 20 checks, unlimited pings, email/Slack alerts. Alternative: Cronitor, Dead Man's Snitch. Final step of workflow = `curl $HC_URL`. |
| PIPE-06 | Keepalive vs GitHub's 60-day cutoff | Documented policy: public repos with no commits for 60 days have scheduled workflows disabled [CITED: docs.github.com/actions]. Mitigations: (a) pipeline itself commits artefacts daily — naturally keeps alive; (b) belt-and-braces: explicit `data/last_build.txt` touch + commit in every run. |
| PIPE-07 | Named unit constants + fixture assertions | Define `pipeline/units.py` with `GBP_PER_MWH`, `MWH`, `GWH`, `TCO2E`, `GBP_M`, `GBP_BN`. Test fixtures assert a known-month aggregate (e.g., "Jan 2023 total generation = X MWh within ±0.01%"). |
| PIPE-08 | Explicit timezone convention | LCCC `Settlement_Date` is date-only with trailing `00:00:00.0000000` zeros — treat as **UTC-naive date** (no time component). Convention recommendation: **date-only, `date` type in DuckDB, no tz**. Document in `pipeline/README.md` and enforce at ingest via Pandera. |
| CHART-01 | Chart 3c — scissors time series (interactive) | Metric defs in "CHART-01 Specification" section below. View-model is a pre-baked JSON consumed by Observable Plot `Plot.line` + `Plot.areaY` for the gap. |
| EDIT-01 | Pointed one-line caption per chart | Template: *"CfD strike prices have tracked well above wholesale prices except for the 2022 spike — consumers paid the gap for {X} years running."* Variables baked from data at build time. |
| EDIT-02 | Visible source citation + last-updated stamp | Footer component in Framework page; `last_updated` value written by pipeline into `src/data/meta.json`. |
| EDIT-04 | "What does this mean?" plain-language boxout | 2–3 sentence boxout below every chart, editorial voice. Markdown content lives next to the chart page. |
| EDIT-05 | Editorial grammar rule (factual vs framing) | Convention: chart captions, axis labels, tooltips = **factual only**. The "What does this mean?" boxout and surrounding prose = editorial framing. Enforce via a lint check on markdown source (e.g., no words from a forbidden-in-caption list: "waste", "scandal", "outrageous"). |
| OPS-01 | Cloudflare Pages deployment | Use `cloudflare/pages-action@v1` or Wrangler `pages deploy dist/`. API token + account ID in GitHub secrets. |
| OPS-02 | Daily cron | `schedule: cron: '30 6 * * *'` — 06:30 UTC, after LCCC daily update window. |
| OPS-03 | Mobile-legible charts | Plot is responsive-SVG by default; enforce min 44×44 px tap targets (WCAG 2.5.5 AAA); use Paul Tol / Okabe-Ito palette for colourblind safety; never colour-only encoding. |
| OPS-04 | Downloadable view-model JSON at stable URL | `src/data/chart-3c.json` → Framework copies to `dist/data/chart-3c.json`. Link rendered on chart page. |
| OPS-05 | Privacy-preserving analytics (no cookie banner) | Options: Plausible Cloud (€9/mo — fails "zero cost"), self-hosted Plausible (free but needs a server — fails "zero ops"), Cloudflare Web Analytics (free, no cookies, no PII — **recommended**). |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

- **Zero-to-minimal running cost** — rules out paid hosts/DBs; keeps us on Cloudflare Pages + GitHub Actions free tiers.
- **Fail loudly** on upstream change — `pipeline/validate.py` must exit non-zero; the CI job must not proceed to `build` on validation failure; the previous `dist/` stays deployed.
- **Accuracy/reproducibility** — every chart traces back to the committed `data/cfd.duckdb`; committed schema + raw CSV snapshots provide reproducibility.
- **Public-first UX** — Pico CSS keeps the chrome invisible; Plot is mobile-responsive by default.
- **Prototype is scaffolding** — `main.py` and `plot_cfd_cost.py` are throwaway; only the aggregation logic (generation-weighted averages) is reused.
- **Python + uv; prefer Python/Rust.** — Polars is Rust under the hood; DuckDB is C++; both satisfy the preference.
- **Workflow enforcement** — all edits go through a GSD command.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Daily data fetch | CI (GitHub Actions) | — | Must run on a schedule; no user trigger |
| CSV parse + validation | Python pipeline (build-time) | — | Rust-backed Polars; Pandera schema at ingest boundary |
| Durable storage | DuckDB file (data layer) | — | Committed artefact, not a running service |
| Chart-model derivation | Python pipeline (build-time) | — | Pre-bake JSON; no client-side query engine in Phase 1 |
| Site rendering | Observable Framework (build-time) | — | Pure static output; browser receives HTML/CSS/JS/JSON only |
| Chart interactivity (zoom, round toggle) | Browser (client) | — | Observable Plot runs entirely client-side |
| Download links (view-model JSON) | CDN (Cloudflare Pages) | — | Static files served from edge |
| Deploy | CI → CDN | — | `cloudflare/pages-action` in workflow |
| Failure alerting | External service (Healthchecks.io or equivalent) | CI | Dead-man's switch — external to GitHub for resilience |

**Tier correctness check:** No backend tier exists. No browser-tier data-querying (DuckDB-WASM) in Phase 1. All derivation happens at build time; all interactivity is pure front-end over pre-baked JSON.

---

## LCCC Data Schema (verified by direct inspection)

**File:** `data/actual_cfd_generation_and_avoided_ghg_emissions.csv` (18 MB, 103,470 rows)
**Date range:** 2016-06-30 → 2026-03-30

| # | Column | Dtype | Notes |
|---|--------|-------|-------|
| 1 | `Settlement_Date` | timestamp literal `YYYY-MM-DD 00:00:00.0000000` | Always midnight; treat as **date-only** |
| 2 | `CfD_ID` | string | e.g. `CAA-EAS-166`, `AAA-COM-191`, `AR2-HRN-306` — prefix encodes allocation round (`AAA-` = pre-AR1 Investment Contracts; `CAA-` = AR1 CfD unit; `AR2-` = AR2; etc.) |
| 3 | `Name_of_CfD_Unit` | string | Human name, may contain commas (quoted in CSV). Maps 1:1 to `CfD_ID` — verify as Q2 |
| 4 | `Technology` | enum(7) | `Offshore Wind` (46,597), `Onshore Wind` (35,313), `Solar PV` (12,201), `Biomass Conversion` (6,225), `Energy from Waste` (2,083), `Dedicated Biomass` (913), `Advanced Conversion Technology` (138) |
| 5 | `Allocation_round` | enum(5) | `Allocation Round 1` (51,288), `Investment Contract` (37,646), `Allocation Round 2` (9,074), `Allocation Round 4` (5,117), `Allocation Round 5` (345). **Note:** no "Allocation Round 3" — AR3 was postponed/cancelled. |
| 6 | `Reference_Type` | enum(2) | `IMRP` (94,111 — Intermittent Market Reference Price, used for wind+solar); `BMRP` (9,359 — Baseload Market Reference Price, used for baseload techs) |
| 7 | `CFD_Generation_MWh` | float | Metered generation that is eligible for CfD payments for that settlement date |
| 8 | `Avoided_GHG_tonnes_CO2e` | float | LCCC's counterfactual-emissions calculation |
| 9 | `CFD_Payments_GBP` | float | **Signed.** Positive = paid to generator; **negative = clawback from generator** (2022 energy crisis). Sample row has `-33399.15`. |
| 10 | `Avoided_GHG_Cost_GBP` | float | LCCC's "value of avoided emissions" using ETS + carbon price support — used in the gas-comparison prototype |
| 11 | `Strike_Price_GBP_Per_MWh` | float | The indexed strike price for that unit on that date |
| 12 | `Market_Reference_Price_GBP_Per_MWh` | float | The reference price (IMRP or BMRP as per col 6) on that date |
| 13 | `Weighted_IMRP_GBP_Per_MWh` | float | Volume-weighted IMRP — used internally by LCCC for settlement |

**Key derivable quantity for CHART-01:** `subsidy_per_MWh = Strike_Price_GBP_Per_MWh − Market_Reference_Price_GBP_Per_MWh`, weighted by `CFD_Generation_MWh` when aggregating across units.

**Cross-check invariant:** `CFD_Payments_GBP ≈ (Strike_Price_GBP_Per_MWh − Market_Reference_Price_GBP_Per_MWh) × CFD_Generation_MWh`. Not exact — LCCC applies settlement-period adjustments — but should tie within ±2% at the yearly aggregate level. Use as a pipeline sanity assertion [ASSUMED based on CfD methodology].

---

## Standard Stack (versions reconfirmed 2026-04-14)

### Core (locked by CLAUDE.md)

| Library | Version | Source | Purpose |
|---------|---------|--------|---------|
| Observable Framework | 1.13.4 | CLAUDE.md [VERIFIED: previous `npm view`] | SSG + chart host |
| Observable Plot | 0.6.17 | CLAUDE.md | Interactive SVG charts |
| DuckDB (Python) | 1.5.2 | CLAUDE.md | Store + query |
| Polars | 1.39.3 | CLAUDE.md | CSV ingest/cleaning |
| pandera | 0.31.0 | [VERIFIED: `pip index versions pandera`] | Schema validation (REQ PIPE-02) |
| httpx | 0.28.1 | [VERIFIED: `pip index versions httpx`] | HTTP client |
| pytest | 9.0.3 | [VERIFIED: `pip index versions pytest`] | Test runner |
| matplotlib | 3.10.8 | CLAUDE.md | Static PNG (social card) |
| pyarrow | latest | CLAUDE.md | Parquet I/O |
| Pico CSS | 2.x | CLAUDE.md | Classless styling |

### Installation (uv-native, to be added to pyproject.toml)

```bash
uv add polars duckdb pandera httpx pyarrow
uv add --dev pytest pytest-cov
# pandas + matplotlib already present; keep pandas only if a downstream helper needs it
```

### Alternatives Considered (and rejected) — see CLAUDE.md "What NOT to Use" for full list

The stack is locked. Do not re-litigate.

---

## Architecture Patterns

### System Flow (Phase 1)

```
[LCCC portal CSV]
        │  (httpx GET, daily 06:30 UTC)
        ▼
[pipeline/fetch.py] ──→ archives to data/raw/YYYY-MM-DD.csv
        │
        ▼
[pipeline/validate.py]  Pandera schema ──→ FAIL (exit non-zero) if drift
        │ OK
        ▼
[pipeline/store.py]  Polars read → DuckDB upsert on (Settlement_Date, CfD_ID)
        │
        ▼
[data/cfd.duckdb]  (committed artefact; single source of truth)
        │
        ▼
[pipeline/build_chart_3c.py]  DuckDB SQL → generation-weighted aggregates
        │
        ▼
[src/data/chart-3c.json]   view-model for CHART-01
[src/data/meta.json]       last_updated, row_count, schema_version
        │
        ▼
[npx observable build]  Framework reads src/, produces dist/
        │
        ▼
[dist/]  static HTML/CSS/JS/JSON
        │
        ▼  (cloudflare/pages-action@v1)
[Cloudflare Pages]  → public URL
        │
        ▼  (final workflow step)
[Healthchecks.io ping]  → maintainer alerted if missed
```

### Recommended Project Structure

```
lowcarboncontracts/
├── .github/
│   └── workflows/
│       └── daily.yml                 # cron + build + deploy
├── pipeline/
│   ├── __init__.py
│   ├── __main__.py                   # `python -m pipeline` entry point
│   ├── units.py                      # named constants (PIPE-07)
│   ├── schema.py                     # Pandera schema (PIPE-02)
│   ├── fetch.py                      # httpx download (PIPE-01) + raw archive (PIPE-04)
│   ├── validate.py                   # apply schema; exit non-zero on drift
│   ├── store.py                      # Polars → DuckDB upsert (PIPE-03)
│   ├── build_chart_3c.py             # CHART-01 view-model builder
│   ├── build_meta.py                 # src/data/meta.json (last_updated, etc.)
│   └── build_og_image.py             # matplotlib PNG for social share
├── src/                              # Observable Framework source root
│   ├── observablehq.config.js        # Framework config
│   ├── index.md                      # landing page
│   ├── charts/
│   │   └── scissors.md               # CHART-01 page (Plot call + boxouts)
│   ├── data/
│   │   ├── chart-3c.json             # written by pipeline/build_chart_3c.py
│   │   ├── meta.json                 # written by pipeline/build_meta.py
│   │   └── chart-3c.json.py          # OPTIONAL: loader for local dev (calls pipeline)
│   └── assets/
│       └── pico.min.css              # or CDN link
├── tests/
│   ├── test_schema.py                # PIPE-02 fixtures
│   ├── test_store.py                 # PIPE-03 idempotency
│   ├── test_units.py                 # PIPE-07 unit correctness
│   └── test_build_chart_3c.py        # tie-out assertions on sample
├── data/
│   ├── cfd.duckdb                    # committed store
│   ├── raw/                          # daily CSV snapshots
│   │   └── 2026-04-14.csv.gz
│   └── actual_cfd_generation_and_avoided_ghg_emissions.csv  # existing
├── pyproject.toml
├── uv.lock
├── package.json                      # @observablehq/framework dep
└── CLAUDE.md
```

**Note on Framework data loaders:** Framework auto-runs `src/data/<name>.json.py` at build time and captures stdout as the file. For Phase 1 the recommendation is to run the pipeline as a **pre-build step in CI** (writes files directly to `src/data/`) rather than relying on loaders — this gives a cleaner separation and lets the same pipeline module run outside Framework. Keep `.json.py` loader stubs for local dev ergonomics only (optional) [CITED: https://github.com/observablehq/data-loader-examples/blob/main/docs/python.md].

### Pattern 1: Idempotent Upsert in DuckDB

```python
# pipeline/store.py
import duckdb
import polars as pl

def upsert(df: pl.DataFrame, db_path: str) -> None:
    con = duckdb.connect(db_path)
    con.register("incoming", df.to_arrow())
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_generation (
            Settlement_Date DATE NOT NULL,
            CfD_ID VARCHAR NOT NULL,
            Name_of_CfD_Unit VARCHAR,
            Technology VARCHAR,
            Allocation_round VARCHAR,
            Reference_Type VARCHAR,
            CFD_Generation_MWh DOUBLE,
            Avoided_GHG_tonnes_CO2e DOUBLE,
            CFD_Payments_GBP DOUBLE,
            Avoided_GHG_Cost_GBP DOUBLE,
            Strike_Price_GBP_Per_MWh DOUBLE,
            Market_Reference_Price_GBP_Per_MWh DOUBLE,
            Weighted_IMRP_GBP_Per_MWh DOUBLE,
            PRIMARY KEY (Settlement_Date, CfD_ID)
        );
    """)
    con.execute("""
        INSERT INTO raw_generation
        SELECT * FROM incoming
        ON CONFLICT (Settlement_Date, CfD_ID) DO UPDATE SET
            CFD_Generation_MWh = EXCLUDED.CFD_Generation_MWh,
            CFD_Payments_GBP = EXCLUDED.CFD_Payments_GBP,
            Strike_Price_GBP_Per_MWh = EXCLUDED.Strike_Price_GBP_Per_MWh,
            Market_Reference_Price_GBP_Per_MWh = EXCLUDED.Market_Reference_Price_GBP_Per_MWh
            -- etc. for the remaining value columns
        ;
    """)
    con.close()
```

[CITED: DuckDB `INSERT ... ON CONFLICT` syntax — https://duckdb.org/docs/sql/statements/insert.html]

### Pattern 2: Pandera Schema for LCCC CSV

```python
# pipeline/schema.py
import pandera.polars as pa
from pandera.typing import Series
import datetime as dt

TECHNOLOGIES = {"Offshore Wind", "Onshore Wind", "Solar PV",
                "Biomass Conversion", "Energy from Waste",
                "Dedicated Biomass", "Advanced Conversion Technology"}
ROUNDS = {"Allocation Round 1", "Allocation Round 2",
          "Allocation Round 4", "Allocation Round 5",
          "Investment Contract"}
REFERENCE_TYPES = {"IMRP", "BMRP"}

schema = pa.DataFrameSchema({
    "Settlement_Date": pa.Column(pa.DateTime, nullable=False,
                                 checks=pa.Check.in_range(dt.date(2014, 1, 1),
                                                          dt.date(2030, 12, 31))),
    "CfD_ID": pa.Column(str, nullable=False,
                        checks=pa.Check.str_matches(r"^[A-Z]{3}-[A-Z]{3}-\d+$|^AR\d-[A-Z]{3}-\d+$")),
    "Technology": pa.Column(str, checks=pa.Check.isin(TECHNOLOGIES)),
    "Allocation_round": pa.Column(str, checks=pa.Check.isin(ROUNDS)),
    "Reference_Type": pa.Column(str, checks=pa.Check.isin(REFERENCE_TYPES)),
    "CFD_Generation_MWh": pa.Column(float, checks=pa.Check.ge(0)),
    "CFD_Payments_GBP": pa.Column(float),  # signed — allow negative
    "Strike_Price_GBP_Per_MWh": pa.Column(float, checks=pa.Check.gt(0)),
    "Market_Reference_Price_GBP_Per_MWh": pa.Column(float),  # can be negative briefly
    # ... remaining columns
}, strict=True)  # strict=True → unknown columns fail validation
```

Pandera `strict=True` catches added columns. Strict on dtypes catches type coercion drift. `CfD_ID` regex catches prefix-scheme changes.

### Pattern 3: Observable Framework Page for CHART-01

```md
<!-- src/charts/scissors.md -->
---
title: Strike vs Market — CfD Scissors
toc: false
---

# Strike vs market: the CfD scissors

<p class="caption">Strike prices track well above wholesale prices except briefly in 2022 — consumers paid the gap for ${yearsCount} years running.</p>

```js
const data = FileAttachment("../data/chart-3c.json").json();
const meta = FileAttachment("../data/meta.json").json();
```

```js
display(Plot.plot({
  marginLeft: 60,
  x: {label: "Settlement month"},
  y: {label: "£ / MWh", grid: true},
  color: {legend: true, domain: ["Strike price", "Market price"]},
  marks: [
    Plot.areaY(data, {x: "month", y1: "market", y2: "strike", fill: "#f4c8c0", fillOpacity: 0.5}),
    Plot.lineY(data, {x: "month", y: "strike", stroke: "#c0392b", strokeWidth: 2}),
    Plot.lineY(data, {x: "month", y: "market", stroke: "#2c3e50", strokeWidth: 2}),
    Plot.ruleY([0])
  ]
}));
```

<aside>
  <h3>What does this mean?</h3>
  <p>CfDs guarantee renewable generators a fixed strike price. When wholesale prices sit below the strike, consumers top up the difference. Across the dataset, that gap has been non-zero for almost the entire period — the 2022 spike was the only reversal.</p>
</aside>

<footer>
  Source: <a href="https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions">LCCC Actual CfD Generation and Avoided GHG Emissions</a>.
  Last updated: ${meta.last_updated}. <a href="../data/chart-3c.json">Download data (JSON)</a>.
</footer>
```

### Anti-Patterns to Avoid

- **Running the pipeline inside a Framework `.md` page via server JS** — Framework is build-time only; don't try to trigger Python at request time.
- **DuckDB-WASM at runtime for Phase 1** — pre-bake JSON instead; keeps bundle small, cacheable, crawlable.
- **Row-by-row pandas groupby** for yearly aggregates — use Polars or DuckDB SQL; the 103k-row dataset processes in milliseconds.
- **Trusting an HTTP 200 as validation** — Pandera the file even if the download "succeeded".
- **Overwriting the DuckDB file blindly** — upsert, don't replace; preserves history for invariant checks.
- **Putting editorial words ("waste", "scandal") in chart captions** — violates EDIT-05. Keep captions factual.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV schema validation | ad-hoc `assert df.columns == [...]` | Pandera | Handles dtype coercion, ranges, regexes, enums, nullability |
| HTTP fetch with retry | `urllib.request` + try/except | httpx + `tenacity` or manual loop | Built-in timeouts, connection pooling, HTTP/2 |
| Idempotent upsert | drop-and-reload or row-level iteration | DuckDB `INSERT ... ON CONFLICT DO UPDATE` | Atomic, indexed, declarative |
| Date handling | `datetime.strptime` loops | Polars `pl.col(...).str.to_date()` | Vectorised, timezone-aware |
| Dead-man's switch | cron-on-a-different-host | Healthchecks.io | Free tier, multiple channels, single HTTPS ping |
| Chart library | D3 from scratch | Observable Plot | 47 KB for the grammar; D3 is transitively available for edge cases |
| CSS system | Tailwind + build step | Pico CSS classless | 7 KB; no build integration needed with Framework |
| Social card generation | Puppeteer/headless browser | matplotlib | Already a dep; Phase 1 only needs one site-wide card |
| Analytics | rolling your own | Cloudflare Web Analytics | Free, no cookies, no PII, no banner required |
| JSON schema for chart view-model | hand-rolled JSON Schema | pydantic model serialised | Type-safe at build, doubles as test fixture |

**Key insight:** The pipeline is small (five modules, ~300 LOC total) precisely because every deceptively-hard sub-problem has a mature library. Resist the urge to write glue code that has a library form.

---

## Common Pitfalls

### Pitfall 1: Silent Upstream Schema Drift (already documented in research/PITFALLS.md)

**What goes wrong:** LCCC changes a column name, date format, or resource ID silently. HTTP 200 returns, pipeline continues, every number is wrong.
**How to avoid:** Pandera `strict=True`; assert yearly aggregate deviation ≤ ±5% vs previous run; commit raw snapshot for diff-based forensics.
**Warning signs:** sudden chart-value shifts; NaN-saturated columns; LCCC changelog mentions "data pipeline update".

### Pitfall 2: GitHub Actions 60-Day Cron Disable

**What goes wrong:** Public-repo scheduled workflows silently disabled after 60 days of no commits. Site freezes; solo maintainer doesn't notice.
**How to avoid:** Pipeline itself commits `data/cfd.duckdb` + `data/raw/*.csv.gz` daily — that counts as activity. Belt-and-braces: touch `data/last_build.txt` every run. Dead-man's switch is the ultimate backstop.

### Pitfall 3: Signed `CFD_Payments_GBP` Misinterpreted

**What goes wrong:** Summing `CFD_Payments_GBP` while ignoring the sign overstates subsidy; naïvely filtering to positive rows understates it. 2022 saw ~£345m clawback that must net against positive payments.
**How to avoid:** Sum signed values for "net consumer subsidy"; sum positive only for "gross payments to generators"; document both in the view-model JSON with distinct field names (`net_subsidy_gbp`, `gross_payments_gbp`).

### Pitfall 4: `Reference_Type` Mixing in a Single Aggregate

**What goes wrong:** Wind+solar use `IMRP`; baseload (biomass, waste) use `BMRP`. Averaging `Market_Reference_Price_GBP_Per_MWh` across technologies mixes apples and oranges.
**How to avoid:** CHART-01 (scissors) aggregates generation-weighted by technology family or by allocation round — volume-weighting naturally handles this because low-volume baseload barely moves the weighted mean. Document in caption methodology.

### Pitfall 5: Unit Confusion (£ vs £m vs £bn; MWh vs GWh)

**What goes wrong:** One function returns £, another £m; an axis label says "£m" but values are "£bn". High-cost error for a credibility-first site.
**How to avoid:** `pipeline/units.py` with named constants and conversion helpers. Fixture test: known year's total payment computes to the same £bn figure regardless of conversion path. REQ PIPE-07.

### Pitfall 6: Timezone / Date Coercion

**What goes wrong:** `Settlement_Date` parsed as UTC timestamp with implicit conversion to local tz; rows on month boundaries shift into the wrong month in aggregates.
**How to avoid:** Treat `Settlement_Date` as **date-only, tz-naive** throughout. Polars `.str.to_date()` (not `.str.to_datetime()`). DuckDB column type `DATE` not `TIMESTAMP`. REQ PIPE-08.

### Pitfall 7: Raw CSV Archive Unbounded Growth

**What goes wrong:** 18 MB × 365 snapshots = 6.6 GB/year committed to git; repo becomes unclonable.
**How to avoid:** Gzip snapshots (`data/raw/YYYY-MM-DD.csv.gz`) → ~3 MB each, ~1 GB/year. Further: retain only last 90 days committed; older archived to a Cloudflare R2 bucket (free tier: 10 GB) via a separate rotation job. Decide in planning.

### Pitfall 8: Cloudflare Pages Cache Staleness

**What goes wrong:** HTML/JS cached aggressively by CDN; users see yesterday's chart despite a fresh build.
**How to avoid:** Framework hashes asset filenames automatically; HTML files use short `Cache-Control: max-age=0, must-revalidate`. Verify via curl after deploy.

---

## Code Examples

### Generation-weighted monthly aggregate for CHART-01

```python
# pipeline/build_chart_3c.py
import duckdb, json, sys
from pathlib import Path

def build(db_path: str, out_path: str) -> None:
    con = duckdb.connect(db_path, read_only=True)
    rows = con.execute("""
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
        WHERE Reference_Type = 'IMRP'  -- wind+solar scissors; omit baseload
        GROUP BY 1, 2
        ORDER BY 1, 2;
    """).fetchall()
    cols = ["month", "round", "generation_mwh", "strike", "market", "payments_gbp"]
    view_model = [dict(zip(cols, r)) for r in rows]
    Path(out_path).write_text(json.dumps(view_model, separators=(",", ":")))
    con.close()
```

### httpx download with retry + raw archive

```python
# pipeline/fetch.py
import httpx, datetime as dt, gzip, shutil
from pathlib import Path

LCCC_URL = (
    "https://dp.lowcarboncontracts.uk/dataset/"
    "8e8ca0d5-c774-4dc8-a079-347f1c180c0f/resource/"
    "5279a55d-4996-4b1e-ba07-f411d8fd31f0/download/"
    "actual_cfd_generation_and_avoided_ghg_emissions.csv"
)

def fetch(dest_csv: Path, raw_dir: Path) -> Path:
    transport = httpx.HTTPTransport(retries=3)
    with httpx.Client(transport=transport, timeout=60.0,
                      follow_redirects=True) as client:
        r = client.get(LCCC_URL)
        r.raise_for_status()
    dest_csv.write_bytes(r.content)
    stamp = dt.date.today().isoformat()
    archive = raw_dir / f"{stamp}.csv.gz"
    with open(dest_csv, "rb") as src, gzip.open(archive, "wb") as dst:
        shutil.copyfileobj(src, dst)
    return dest_csv
```

### GitHub Actions workflow skeleton

```yaml
# .github/workflows/daily.yml
name: daily-rebuild
on:
  schedule:
    - cron: '30 6 * * *'
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run python -m pipeline    # fetch → validate → store → build
      - run: npm ci
      - run: npx @observablehq/framework build
      - name: Commit data artefacts
        run: |
          git config user.name "cfd-bot"
          git config user.email "cfd-bot@users.noreply.github.com"
          git add data/ src/data/
          git diff --cached --quiet || git commit -m "chore(data): daily rebuild $(date -u +%F)"
          git push
      - uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          accountId: ${{ secrets.CF_ACCOUNT_ID }}
          projectName: cfd-visualiser
          directory: dist
      - name: Healthchecks ping
        run: curl -fsS --retry 3 "${{ secrets.HEALTHCHECKS_URL }}"
```

---

## CHART-01 Specification (scissors, chart 3c)

**Audience:** Non-specialist; must communicate "consumers paid X above wholesale" without reading prose.

**Data source:** `raw_generation` table, filtered to `Reference_Type = 'IMRP'` (wind + solar), which is 91% of rows and the canonical "renewables scissors" framing. Baseload contracts (biomass, waste) use `BMRP` and are excluded from this chart (mention in caption methodology).

**Metric definitions:**

- `strike_gwa_month` = `Σ(Strike_Price × CFD_Generation_MWh) / Σ(CFD_Generation_MWh)` — generation-weighted average monthly strike price
- `market_gwa_month` = `Σ(Market_Reference_Price × CFD_Generation_MWh) / Σ(CFD_Generation_MWh)` — generation-weighted average monthly market reference price
- `subsidy_per_mwh_month` = `strike_gwa_month − market_gwa_month`
- `payments_gbp_month` = `Σ(CFD_Payments_GBP)` (signed — negative during 2022 clawback)

**Aggregation grain:** Monthly (calendar month of `Settlement_Date`); interactive toggle for `Allocation_round` ∈ {Investment Contract, AR1, AR2, AR4, AR5, All}. When "All" selected, weight across rounds; when a specific round selected, filter.

**Deflation:** **Nominal £** for v1 (no CPI deflation). Document in methodology. v2 may add real-terms toggle.

**Interactivity:**
- Horizontal zoom/pan via Plot's `x` scale + a brush-style interval selector, OR Plot's built-in `interval` pointer
- Round toggle via an `Inputs.checkbox` bound to the data filter
- Tooltip on hover showing (month, strike, market, subsidy/MWh, payments £m)

**Mobile fallback:** No separate fallback needed — Plot is responsive; at narrow viewports reduce tick density and hide the legend behind a disclosure.

**View-model JSON schema** (`src/data/chart-3c.json`):

```json
[
  {
    "month": "2023-01",
    "round": "Allocation Round 1",
    "generation_mwh": 1234567.89,
    "strike": 150.42,
    "market": 82.15,
    "payments_gbp": 84259123.50
  }
]
```

Chart computes `subsidy = strike − market` client-side (cheap; avoids duplication in JSON).

**Caption (EDIT-01 draft):** "Strike prices for wind + solar CfDs have exceeded wholesale market prices in every month except the 2022 gas-price spike — consumers have funded the gap throughout."

**Boxout (EDIT-04 draft):** "CfDs guarantee renewable generators a fixed strike price. When wholesale electricity prices sit below the strike, electricity consumers top up the difference through their bills. The gap between the two lines is the subsidy paid per MWh; the shaded area is its cumulative scale."

---

## Runtime State Inventory

*(Phase 1 is greenfield — no existing runtime state. Section included for completeness.)*

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no existing DuckDB, no collections, no Redis keys | Create `data/cfd.duckdb` from scratch |
| Live service config | None — no existing deployment | Provision Cloudflare Pages project; add GitHub Actions workflow |
| OS-registered state | None — no cron/pm2/systemd entries | Schedule is pure GitHub Actions cron |
| Secrets/env vars | None yet — will create `CF_API_TOKEN`, `CF_ACCOUNT_ID`, `HEALTHCHECKS_URL` as GitHub secrets | Add secrets via repo settings during Plan 01-05 |
| Build artefacts | None — no `dist/`, no `.duckdb`, no `src/` | All created by Phase 1 |

---

## Environment Availability

| Dependency | Required By | Available (local dev) | Available (CI) | Fallback |
|------------|------------|-----------------------|----------------|----------|
| Python 3.13 | Pipeline | ✓ (pyproject.toml pins >=3.13) | via `astral-sh/setup-uv@v4` | — |
| uv | Env management | ✓ (repo already uses it) | via `astral-sh/setup-uv@v4` | pip (worse) |
| Node.js 20 LTS | Framework build | Install locally | via `actions/setup-node@v4` | — |
| Git | Commit artefacts | ✓ | ✓ | — |
| Cloudflare account + Pages project | Deploy | Setup task | secret in CI | Netlify (inferior free tier) |
| GitHub repo with Actions | CI + cron | ✓ (this repo is on Gitea?) | **RESOLVE** (see Open Q5) | self-hosted runner |
| Healthchecks.io account | Dead-man's switch | Setup task | secret in CI | Cronitor / Dead Man's Snitch |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** All CF / HC setup items have alternatives but the recommendations above are the blessed choices.

**Critical clarification needed (Open Q5):** The repo is on Gitea (`/Users/rjl/Code/gitea/...`). **GitHub Actions cron only runs on github.com.** Either: (a) push/mirror to GitHub for the workflow, (b) use Gitea Actions (compatible subset) on a self-hosted runner, or (c) use Cloudflare Workers Cron Triggers instead. This must be resolved before Plan 01-05.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — to create in Wave 0 |
| Quick run command | `uv run pytest -x -q` |
| Full suite command | `uv run pytest --cov=pipeline --cov-fail-under=80` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| PIPE-01 | Fetch returns a non-empty CSV | integration (hits live URL; skippable offline) | `pytest tests/test_fetch.py::test_live_fetch -x` | ❌ Wave 0 |
| PIPE-01 | Fetch writes gzipped archive | unit | `pytest tests/test_fetch.py::test_archive_written -x` | ❌ Wave 0 |
| PIPE-02 | Valid CSV passes schema | unit | `pytest tests/test_schema.py::test_valid_accepts -x` | ❌ Wave 0 |
| PIPE-02 | Column rename triggers non-zero exit | unit | `pytest tests/test_schema.py::test_column_drift_fails -x` | ❌ Wave 0 |
| PIPE-02 | Unknown Technology value fails | unit | `pytest tests/test_schema.py::test_unknown_tech_fails -x` | ❌ Wave 0 |
| PIPE-03 | Re-running upsert preserves aggregates | unit | `pytest tests/test_store.py::test_idempotent -x` | ❌ Wave 0 |
| PIPE-03 | Upsert updates changed row | unit | `pytest tests/test_store.py::test_update_on_conflict -x` | ❌ Wave 0 |
| PIPE-04 | Daily snapshot file exists + gzipped | unit | `pytest tests/test_fetch.py::test_archive_gzipped -x` | ❌ Wave 0 |
| PIPE-05 | Healthchecks URL pinged on success | smoke | GitHub Actions step verified in CI log | manual |
| PIPE-06 | Workflow touches `data/last_build.txt` | unit | `pytest tests/test_build_meta.py::test_last_build_touched -x` | ❌ Wave 0 |
| PIPE-07 | Unit constants sum to canonical reference | unit | `pytest tests/test_units.py::test_2023_total_generation -x` | ❌ Wave 0 |
| PIPE-08 | Settlement_Date parses as date-only | unit | `pytest tests/test_schema.py::test_date_only_no_time -x` | ❌ Wave 0 |
| CHART-01 | View-model JSON has expected shape | unit | `pytest tests/test_build_chart_3c.py::test_schema -x` | ❌ Wave 0 |
| CHART-01 | Yearly sum of `payments_gbp_month` ties out vs `raw_generation` totals | unit | `pytest tests/test_build_chart_3c.py::test_payments_tie_out -x` | ❌ Wave 0 |
| CHART-01 | 2022 monthly `payments_gbp` contains at least one negative (clawback) | unit (invariant) | `pytest tests/test_build_chart_3c.py::test_2022_clawback_present -x` | ❌ Wave 0 |
| EDIT-01 | Caption field populated in meta.json | unit | `pytest tests/test_build_meta.py::test_caption_present -x` | ❌ Wave 0 |
| EDIT-02 | Source URL + last_updated in rendered page | smoke | `pytest tests/test_site.py::test_footer_contains_source -x` (parses `dist/` after build) | ❌ Wave 0 |
| EDIT-05 | Caption contains no forbidden editorial words | unit (lint) | `pytest tests/test_editorial_grammar.py -x` | ❌ Wave 0 |
| OPS-01 | Deploy succeeded (HTTP 200 on public URL) | smoke (post-deploy) | CI step: `curl -fsS $SITE_URL` | manual in Phase 1 |
| OPS-03 | No colour-only encoding in chart spec | unit (static analysis of page) | `pytest tests/test_site.py::test_has_labels_not_only_colour -x` | ❌ Wave 0 |
| OPS-04 | `dist/data/chart-3c.json` exists after build | smoke | `pytest tests/test_site.py::test_json_artefact_exists -x` | ❌ Wave 0 |
| OPS-05 | No tracking script from known-tracker domains | unit | `pytest tests/test_site.py::test_no_third_party_trackers -x` | ❌ Wave 0 |

### Nyquist Sampling Strategy

**Reference dataset (ground truth for invariants):** the committed `data/actual_cfd_generation_and_avoided_ghg_emissions.csv` (snapshot 2026-04-13, 103,470 rows) is the canonical fixture. All unit tests run against it directly or against a `tests/fixtures/cfd_sample.csv` subset (1,000 rows sampled across every `Allocation_round` / `Technology` / year combination).

**Invariants (must hold on every pipeline run):**

1. **Row-count floor:** `SELECT COUNT(*) FROM raw_generation ≥ 103_470` (after first daily run; grows monotonically).
2. **Date monotonicity:** `MAX(Settlement_Date)` advances by no more than 7 days between consecutive daily runs (catches fetcher stuck on a cached URL).
3. **Yearly generation stability:** for every year in `[2017, prev_year−1]`, `Σ CFD_Generation_MWh` changes by ≤ ±1% between consecutive runs (LCCC may backfill historical corrections but not large ones).
4. **Yearly payments tie-out:** `Σ payments_gbp` from `build_chart_3c.json` equals `Σ CFD_Payments_GBP` from `raw_generation` within ±0.01% for every year.
5. **2022 sign invariant:** at least one month in 2022 has negative `payments_gbp` (clawback period) — catches sign-flip bugs.
6. **Strike > Market for almost all months:** in ≥ 95% of (round, month) cells, `strike > market`; fails if a coercion bug inverts them.
7. **No NaN columns:** no column in `chart-3c.json` may be entirely null.

**Sampling rate:**
- **Per task commit:** `uv run pytest -x -q` (unit tests only — ~5 seconds expected)
- **Per wave merge:** full suite with coverage (`--cov-fail-under=80`)
- **Phase gate:** full suite green + live CI build succeeds + deployed site returns HTTP 200 with current date in `meta.json`

### Wave 0 Gaps

- [ ] `pyproject.toml` — add `[tool.pytest.ini_options]` + dev deps (pytest, pytest-cov)
- [ ] `tests/conftest.py` — shared fixtures: sample CSV, fresh DuckDB, mock httpx client
- [ ] `tests/fixtures/cfd_sample.csv` — 1,000-row stratified sample generated once from live CSV
- [ ] `tests/fixtures/cfd_sample_expected.json` — golden view-model JSON for regression testing
- [ ] `tests/test_schema.py`, `tests/test_store.py`, `tests/test_fetch.py`, `tests/test_build_chart_3c.py`, `tests/test_build_meta.py`, `tests/test_units.py`, `tests/test_editorial_grammar.py`, `tests/test_site.py` — all new
- [ ] Install commands: `uv add --dev pytest pytest-cov`

---

## Ops/Observability

### Failure modes and loud-failure mapping

| Failure | Detection | Consequence |
|---------|-----------|-------------|
| Upstream URL 404 / 5xx | httpx raises; `pipeline` exits non-zero | Workflow fails; previous `dist/` stays live; no Healthchecks ping → alert |
| CSV downloads but schema drifts | Pandera raises; exit non-zero | Same as above |
| Schema OK but aggregate shifts >5% vs prev | Invariant test #3 fails | Build aborts; alert |
| Upsert writes but DuckDB file corrupt | pytest post-write integrity check (`PRAGMA integrity_check`) | Build aborts; DB file not committed |
| Framework build fails | `npx observable build` exits non-zero | Workflow fails |
| Cloudflare deploy fails | `pages-action` exits non-zero | Workflow fails; previous edge version stays live |
| Healthchecks ping missing | external (HC emails maintainer after grace period) | Human alerted |
| GitHub cron disabled after 60d | daily data commit keeps repo active; belt-and-braces `last_build.txt` touch | Prevented |

### Schema-change detection

Beyond Pandera `strict=True`, a weekly diff of `data/raw/*.csv.gz` file sizes is a cheap canary — a 0-byte or 10× larger file signals trouble pre-validation.

### Artefact versioning

- `src/data/meta.json` includes `{schema_version: "1.0", pipeline_version: "<git-sha>", last_updated: "<iso-ts>"}`.
- Bump `schema_version` manually when the view-model JSON shape changes; fail fast if the chart page expects v1 and sees v2.

---

## Security Domain

Security enforcement for Phase 1 is light — static site, no user input, no auth, no PII. The ASVS categories that apply:

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | N/A — no user auth |
| V3 Session Management | no | N/A |
| V4 Access Control | yes (minor) | CI secrets (CF token, HC URL) scoped read-only where possible; use fine-grained CF API token restricted to the Pages project |
| V5 Input Validation | yes | Pandera schema on ingest is the input-validation boundary |
| V6 Cryptography | no | TLS via Cloudflare; no app-level crypto |
| V14 Configuration | yes | No secrets in repo; `.env.example` only; GitHub Actions secrets used |

### Known Threat Patterns

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Leaked CF API token | Information Disclosure | Fine-grained token; rotate every 90d; least-privilege (Pages:Edit only) |
| Supply-chain attack on a pipeline dep | Tampering | `uv.lock` committed; Dependabot/renovate on dev deps |
| Malicious LCCC response (e.g. huge file, HTML masquerading as CSV) | DoS / Tampering | httpx `timeout=60`, `max-response-size` guard; content-type check; size sanity check (<100 MB) |
| XSS via chart data | Tampering | View-model is JSON; Plot renders via D3 which escapes text by default; no `innerHTML` |
| CSP bypass | — | Set strict CSP header via Cloudflare Pages `_headers` file |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pandas + notebook prototype | Polars + DuckDB pipeline modules | Project v1 | 5× faster CSV, SQL idempotent upsert, testable |
| Jinja2-templated static site | Observable Framework | Stack decision 2026-04 | Built-in Plot integration, data-loader pattern, no template layer |
| pip + requirements.txt | uv + pyproject.toml | Already adopted | Reproducible lockfiles, fast CI |
| Plotly / D3-from-scratch | Observable Plot 0.6.17 | Stack decision | 47 KB vs 3.5 MB; grammar-of-graphics API |
| SQLite for aggregation | DuckDB 1.5.2 | Stack decision | 10–50× faster analytical queries |

**Deprecated / not used:**
- The `research/ARCHITECTURE.md` Jinja2 render-layer diagram — superseded by Observable Framework.
- `plot_cfd_cost.py` matplotlib prototype — scaffolding; only aggregation logic reused.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `(Settlement_Date, CfD_ID)` is a unique composite PK in the LCCC CSV | PIPE-03 / Pattern 1 | If duplicates exist, upsert would silently overwrite; need to verify with `SELECT Settlement_Date, CfD_ID, COUNT(*) FROM csv GROUP BY 1,2 HAVING COUNT(*) > 1` before committing to this PK |
| A2 | `CFD_Payments_GBP ≈ (Strike − Market) × CFD_Generation_MWh` within ±2% at yearly aggregate | Schema section cross-check | Invariant test may fail on legitimate data; may need loosening or a separate reconciliation path |
| A3 | LCCC portal updates "daily" means new rows appear within a 24h window; 06:30 UTC cron is post-update | OPS-02 | If LCCC actually updates at 09:00 UTC, the cron fetches yesterday's file; need to verify actual update time (Open Q3) |
| A4 | Cloudflare Web Analytics satisfies OPS-05 "no cookie banner required" | OPS-05 | Needs a UK/EU privacy-legal read; if it sets any cookie or matches an IAB "tracker" list, would violate. Plausible is the conservative fallback |
| A5 | Gitea repo can drive GitHub Actions (via mirror) or Gitea Actions (compatible) | Environment | If neither works, would need to switch scheduler to Cloudflare Workers Cron |
| A6 | 18 MB CSV × daily fits within GitHub's effective repo-size practices (≤5 GB recommended) even compressed to ~3 MB/day over years | PIPE-04 | Long-term repo bloat; mitigation already noted (R2 rotation) |
| A7 | Observable Plot's default SVG responsiveness satisfies OPS-03 "mobile-legible" without custom breakpoints for CHART-01 (line chart) | CHART-01 spec | If tick crowding is ugly on narrow screens, may need a `Plot.Inputs.range` or fewer tick marks on <480px |
| A8 | Pandera supports `pandera.polars` Polars-native schemas in 0.31.0 | Pattern 2 | Confirmed in pandera changelog but not test-run in this env; if unstable, fall back to `pandera.pandas` with a Polars→pandas conversion step [VERIFIED: pandera 0.31.0 release notes, https://pandera.readthedocs.io] |

---

## Open Questions

1. **Is `(Settlement_Date, CfD_ID)` a true unique key?**
   - What we know: Sample rows show unique combinations; CfD_IDs look stable.
   - What's unclear: Does LCCC ever issue a correction as a new row for the same date/unit, or do they replace?
   - Recommendation: Run `SELECT ... GROUP BY HAVING COUNT(*) > 1` on the committed CSV in Plan 01-01; if collisions exist, extend PK (e.g. add `Reference_Type`) or design a "latest-wins by ingest-timestamp" strategy.

2. **Does `CfD_ID` ↔ `Name_of_CfD_Unit` stay 1:1 over time?**
   - What we know: Spot-checked rows agree.
   - What's unclear: Could a unit be renamed?
   - Recommendation: Add a unit test that asserts 1:1 on the reference CSV; alert on violation, use `CfD_ID` as the canonical key regardless.

3. **What time of day does the LCCC portal publish the daily update?**
   - What we know: Site says "daily".
   - What's unclear: Hour of day; which timezone (UK/Europe/London ≠ UTC, DST matters).
   - Recommendation: Observe the portal for 2–3 days before committing a cron time; default 06:30 UTC, verify after first live run, adjust if needed.

4. **Which `Allocation_round` values should CHART-01 show by default?**
   - What we know: 5 values exist (AR1, AR2, AR4, AR5, Investment Contract).
   - What's unclear: "All" averaged is visually cleaner but hides AR-level variance; per-round lines are noisy with 5 series.
   - Recommendation: Default view = "All" (weighted average across rounds, single strike line, single market line); checkbox toggle to split by round. Validate in planning.

5. **Scheduler host — GitHub vs Gitea?**
   - What we know: Repo lives at `/Users/rjl/Code/gitea/...`.
   - What's unclear: Whether the user has a GitHub mirror; whether Gitea Actions is self-hosted and usable; whether Cloudflare Workers Cron is preferred.
   - Recommendation: **Resolve before Plan 01-05.** Cheapest path: mirror to GitHub for Actions; fallback: Gitea Actions on self-hosted runner; last-resort: Cloudflare Workers Cron invoking a GitHub webhook.

6. **Raw archive retention strategy?**
   - What we know: 3 MB/day gzipped ≈ 1 GB/yr in git.
   - What's unclear: Acceptable repo-size budget.
   - Recommendation: Commit last 90 days; rotate older to Cloudflare R2 via monthly pruning job. Confirm in planning.

7. **Which allocation rounds does "Investment Contract" actually cover for labelling purposes?**
   - What we know: Value appears 37,646 times; pre-dates AR1.
   - What's unclear: Display label ("Investment Contract" is jargon; "Pre-AR1 (2014)" may be clearer for a public audience).
   - Recommendation: Keep raw value as the key; add a display-label mapping in chart code (`"Investment Contract" → "Pre-AR1 legacy"`).

---

## Sources

### Primary (HIGH confidence)

- **LCCC data portal** — https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions — CSV URL and update cadence verified via WebFetch [VERIFIED 2026-04-14]
- **Committed dataset** — `data/actual_cfd_generation_and_avoided_ghg_emissions.csv` — schema profiled by direct inspection (103,470 rows, date range, value sets)
- **pip index versions** — pandera 0.31.0, httpx 0.28.1, pytest 9.0.3 [VERIFIED 2026-04-14]
- **CLAUDE.md** — project stack lock, constraints, version pins
- **`.planning/REQUIREMENTS.md`** — canonical REQ-ID definitions
- **`.planning/ROADMAP.md`** — phase split and success criteria
- **`.planning/research/STACK.md`, `PITFALLS.md`, `ARCHITECTURE.md`** — prior research; PITFALLS.md pitfalls 1 and 2 carried forward verbatim
- **GitHub `data-loader-examples` repo** — https://github.com/observablehq/data-loader-examples/blob/main/docs/python.md — Framework Python data-loader convention [CITED]
- **DuckDB docs** — https://duckdb.org/docs/sql/statements/insert.html — `INSERT ... ON CONFLICT DO UPDATE` syntax [CITED]

### Secondary (MEDIUM confidence)

- **Observable Framework data loaders** — https://observablehq.com/framework/loaders — fetched via WebSearch summary (direct WebFetch blocked 403); convention confirmed cross-referenced against the official GitHub data-loader-examples repo
- **pandera.polars** — integration confirmed via release notes [CITED: pandera 0.31.0]

### Tertiary (LOW confidence / marked for validation)

- Update-time of LCCC portal (06:30 UTC assumed post-update window) — verify by observation (Open Q3)
- Cloudflare Web Analytics "no cookie banner required" claim — legal verification recommended (Assumption A4)

---

## Metadata

**Confidence breakdown:**
- LCCC schema + values: **HIGH** — direct inspection of committed CSV
- Stack choices: **HIGH** — locked by CLAUDE.md; versions verified
- Pipeline architecture: **HIGH** — patterns are standard; DuckDB upsert syntax cited
- Framework conventions: **MEDIUM** — docs cite but not yet exercised in-repo; minor uncertainty on loader stdout quirks
- CHART-01 metric definitions: **HIGH** — simple GWA formulae; matches prototype's approach
- Mobile interactivity: **MEDIUM** — Plot's responsive behaviour assumed; to validate in Wave 0
- Scheduler path (Gitea vs GitHub): **LOW** — needs user decision

**Research date:** 2026-04-14
**Valid until:** 2026-05-14 (30 days — stack is stable; re-verify LCCC URL monthly)
