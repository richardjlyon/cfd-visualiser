# Architecture Research

**Domain:** Daily-rebuilt public-education data visualisation site (UK CfD economics)
**Researched:** 2026-04-14
**Confidence:** HIGH for pipeline structure and store choice; MEDIUM for chart-delivery tradeoffs (context-dependent)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SCHEDULED TRIGGER (daily cron)                   │
│                     GitHub Actions  schedule: cron                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                        INGEST LAYER (Python)                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │
│  │   Fetcher    │──▶│  Validator   │──▶│  Store Writer            │ │
│  │ (HTTP → CSV) │   │ (Pandera     │   │  (CSV → DuckDB .db file) │ │
│  │              │   │  schema)     │   │                          │ │
│  └──────────────┘   └──────────────┘   └──────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      DURABLE STORE                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  data/cfd.duckdb   (columnar, ~5–15 MB, git-committed)       │   │
│  │  ├─ table: raw_generation  (verbatim LCCC rows, append-only) │   │
│  │  ├─ table: cfd_register    (LCCC capacity register, Phase 2) │   │
│  │  └─ table: external_*      (Elexon/NESO, Phase 3+)           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    DERIVATION LAYER (Python)                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │
│  │ Chart-model  │   │ Chart-model  │   │  Chart-model             │ │
│  │ builder 3c   │   │ builder 3d   │   │  builder 2a / 3b+6a      │ │
│  │              │   │              │   │                          │ │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬──────────────┘ │
│         │                  │                       │                │
│         ▼                  ▼                       ▼                │
│  site/data/3c.json  site/data/3d.json    site/data/2a.json         │
│                     site/data/lorenz.json                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      RENDER LAYER (Python / Jinja2)                  │
│  ┌──────────────┐   ┌──────────────────────────────────────────┐    │
│  │  HTML pages  │   │  Asset pipeline                          │    │
│  │  (Jinja2     │◀──│  (CSS, JS bundles, chart spec includes)  │    │
│  │   templates) │   │                                          │    │
│  └──────┬───────┘   └──────────────────────────────────────────┘    │
└─────────┼───────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────────┐
│                    OUTPUT: site/ directory (static)                  │
│  index.html, /charts/3c/, /charts/3d/, /charts/2a/, /charts/3b/     │
│  /data/3c.json, /data/3d.json ... (future: public JSON API)         │
│  /assets/ (CSS, JS)                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                  DEPLOY (GitHub Actions → Cloudflare Pages)          │
│                  git push → CF Pages build hook OR                   │
│                  wrangler pages deploy site/                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Responsibility | What it owns |
|-----------|---------------|-------------|
| **Fetcher** | Download LCCC CSV; detect upstream format changes; fail loudly on schema drift | `pipeline/fetch.py` |
| **Validator** | Assert column presence, dtypes, value ranges, row-count sanity; raise hard error on failure | `pipeline/validate.py` |
| **Store Writer** | Upsert new rows into DuckDB; idempotent on Settlement_Date + CfD_ID composite key | `pipeline/store.py` |
| **Durable Store** | Single `data/cfd.duckdb` file; append-only raw table + derived views | `data/cfd.duckdb` |
| **Chart-model builders** | Query DuckDB → produce chart-specific JSON view-models; one Python module per chart family | `pipeline/charts/` |
| **Renderer** | Consume JSON view-models + Jinja2 templates → emit static HTML | `pipeline/render.py` |
| **Site output** | Deployable artefact; static HTML + JSON data files + assets | `site/` |
| **CI / Scheduler** | Daily cron (GitHub Actions); orchestrates fetch→validate→store→derive→render→deploy | `.github/workflows/rebuild.yml` |

---

## Recommended Project Structure

```
lowcarboncontracts/
├── data/
│   ├── cfd.duckdb              # durable store (git-committed; binary but small)
│   └── raw/                    # last-fetched CSV snapshots (gitignored, for debug)
│
├── pipeline/
│   ├── fetch.py                # HTTP download, schema-drift detection
│   ├── validate.py             # Pandera schema; hard-fail on violations
│   ├── store.py                # DuckDB upsert; idempotency logic
│   ├── derive.py               # Orchestrates chart-model builders
│   └── charts/
│       ├── scissors_3c.py      # strike vs market JSON
│       ├── cost_per_tonne_3d.py
│       ├── cumulative_3b.py    # cumulative subsidy + Lorenz
│       └── heatmap_2a.py       # dunkelflaute heatmap
│
├── render/
│   ├── render.py               # Jinja2 → site/
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── chart.html          # per-chart page template
│
├── site/                       # built artefact (gitignored or branch-deploy)
│   ├── index.html
│   ├── charts/
│   │   ├── scissors/index.html
│   │   ├── cost-per-tonne/index.html
│   │   ├── cumulative/index.html
│   │   └── heatmap/index.html
│   ├── data/                   # JSON view-models (doubles as future API)
│   │   ├── scissors.json
│   │   ├── cost-per-tonne.json
│   │   ├── cumulative.json
│   │   └── heatmap.json
│   └── assets/
│       ├── main.css
│       └── charts.js           # Observable Plot bundle
│
├── .github/
│   └── workflows/
│       └── rebuild.yml         # cron: '5 6 * * *' + deploy step
│
├── pyproject.toml
└── uv.lock
```

### Structure rationale

- **`pipeline/` vs `render/`:** Separation between "data transformation" and "HTML production" is the critical seam. Either side can be rewritten without touching the other, because the contract is `site/data/*.json`.
- **`data/cfd.duckdb` committed to git:** At 5–15 MB, the DuckDB file is comfortably within git LFS territory or even plain git. Committing it means the CI job does not need to re-fetch every row from LCCC on each run — only the daily delta. This is important for resilience if the upstream URL is temporarily unavailable.
- **`site/data/` as the API seam:** Pre-baked JSON files in `site/data/` are both the chart data source today and the public API surface later. No code change required to flip to "public API" — just document the URL convention.

---

## Durable Store Decision: DuckDB

**Recommendation: `data/cfd.duckdb` — a single DuckDB file.**

Rationale:

| Criterion | DuckDB file | SQLite file | Parquet directory | Raw CSV |
|-----------|-------------|-------------|-------------------|---------|
| Analytical query performance | Excellent (columnar) | Poor on aggregations | Excellent | Poor |
| Python ergonomics | Native, no ORM needed | Good | Good via DuckDB | pandas-only |
| Schema enforcement | SQL DDL | SQL DDL | None (inferred) | None |
| Single-file commit to git | Yes (~5 MB compressed) | Yes | No (many files) | Yes (18 MB, grows) |
| Direct Parquet export | `COPY TO 'x.parquet'` | No | Native | No |
| Future API query layer | DuckDB-WASM can read .db | Not WASM-friendly | DuckDB-WASM reads parquet | — |
| Joins across sources | SQL | SQL | Possible but awkward | Hard |

DuckDB is the right choice because:
1. The data is purely analytical (no transactional writes); columnar storage wins on every aggregate query the charts need.
2. DuckDB queries the raw CSV directly during ingest (`INSERT INTO raw SELECT * FROM read_csv_auto(...)`) — no pandas intermediate required.
3. A single `.duckdb` file can be exported to Parquet for DuckDB-WASM later with a single SQL command; no architecture change needed.
4. At ~100k rows and ~18 MB CSV, the `.duckdb` file will compress to ~3–8 MB — well within git's practical limits.
5. The same file is the build-time query source and a future API backend (serve Parquet export or expose via DuckDB-WASM).

**SQLite is rejected** because row-based storage forces full-table scans for the weighted-average and time-series aggregates these charts require.

**Parquet directory is rejected** for v1 because it lacks schema enforcement, makes joins awkward, and requires a separate tool for upsert logic. It can be an export format but not the primary store.

**Raw CSV is rejected** as the primary store because it grows unboundedly, has no schema enforcement, and forces pandas to re-parse 18 MB+ on every build.

---

## Chart Data Delivery Decision: Pre-baked JSON

**Recommendation: Pre-baked JSON files per chart, served as static files.**

| Criterion | Pre-baked JSON | DuckDB-WASM + Parquet in-browser |
|-----------|---------------|----------------------------------|
| Mobile compatibility | Excellent | WASM download adds 6–20 MB cold start |
| Build complexity | Low (one Python function per chart) | High (requires JS build toolchain) |
| Shareability as screenshots | Unaffected | Unaffected |
| Interactive filtering | Handled by chart library (Observable Plot) over small JSON | More powerful but overkill for this data scale |
| Future public API | JSON files ARE the API | Separate concern |
| Offline / slow connection | 10–100 KB per chart JSON loads fast | 6+ MB WASM + Parquet is a barrier |
| Data size per chart | ~10–100 KB after aggregation | Full dataset in Parquet (3–8 MB) |

At this scale (~100k rows), Python can pre-aggregate all chart data at build time into compact JSON view-models (typically 10–100 KB per chart). There is no need to push query execution into the browser. DuckDB-WASM is the right architecture when you need ad-hoc user-driven queries over the full dataset (e.g., "filter by any technology, any year, any project"). The v1 charts have fixed analytical frames — they benefit from editorial curation, not open-ended exploration.

**Exception to revisit in Phase 3:** Chart 4a (cannibalisation scatter over half-hourly Elexon data) may reach millions of rows. At that point, a Parquet export + DuckDB-WASM in-browser becomes worth evaluating for that chart only.

---

## Data Flow

### Daily pipeline flow

```
GitHub Actions cron trigger (06:05 UTC daily)
    │
    ▼
fetch.py
  - GET https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions
  - Download latest CSV to data/raw/cfd_YYYYMMDD.csv
  - Compare column headers to expected schema → FAIL LOUD if changed
    │
    ▼
validate.py
  - Load CSV into pandas / DuckDB
  - Pandera schema: assert columns, dtypes, non-null keys, value ranges
    (Settlement_Date parseable, CFD_Generation_MWh >= 0, etc.)
  - Exit code 1 on violation → CI job fails → no stale deploy
    │
    ▼
store.py
  - UPSERT into raw_generation: INSERT OR REPLACE WHERE (Settlement_Date, CfD_ID)
  - Idempotent: safe to re-run; duplicate rows are replaced, not doubled
  - Write metadata: last_ingested_at, row_count, source_hash
    │
    ▼
derive.py  (orchestrates chart builders)
  ├── scissors_3c.py   → DuckDB query → site/data/scissors.json
  ├── cost_per_tonne_3d.py → site/data/cost-per-tonne.json
  ├── cumulative_3b.py → site/data/cumulative.json + site/data/lorenz.json
  └── heatmap_2a.py    → site/data/heatmap.json
    │
    ▼
render.py
  - Jinja2 templates + JSON filenames → site/charts/*/index.html
  - site/index.html (chart gallery / landing page)
  - Injects build timestamp + source citation into every page
    │
    ▼
Deploy
  - Push site/ to Cloudflare Pages via wrangler OR
  - Push to gh-pages branch for GitHub Pages
  - No CDN purge step needed: Cloudflare Pages deploys atomic;
    GitHub Pages cache-busts via commit hash in asset filenames
```

### Chart data flow (browser side)

```
User requests /charts/scissors/
    │
    ▼
Browser fetches pre-rendered HTML (inline <script> tags reference)
    │
    ▼
Browser fetches /data/scissors.json  (~20 KB)
    │
    ▼
Observable Plot JS renders chart from JSON
  - Zoom/pan/toggle handled entirely in browser JS over the small JSON payload
  - No server round-trip; no WASM startup cost
```

### External data joins flow (Phase 2 / Phase 3)

```
External source (CfD Register, Elexon, NESO BMRS)
    │
    ▼
Separate fetch_*.py scripts (one per source)
  - Each produces its own raw table in cfd.duckdb
  - Separate validation schemas per source
    │
    ▼
derive.py joins across tables with SQL
  (e.g., JOIN raw_generation ON cfd_id, JOIN cfd_register ON cfd_id)
    │
    ▼
Same chart-model pipeline as above
```

External data joins are NOT separate DAGs — they are additional fetch+validate+store modules called in sequence before the derive step, with the join logic living in the chart-model SQL queries. This keeps the pipeline linear and avoids DAG orchestration complexity (Airflow, Prefect) which would be overkill at this scale.

---

## API-Door-Open Strategy

The static JSON files in `site/data/` are the API. No extra work is required.

**Naming convention to establish from day one:**

```
/data/scissors.json          → time-series for chart 3c
/data/cost-per-tonne.json    → time-series for chart 3d
/data/cumulative.json        → cumulative subsidy series for chart 3b
/data/lorenz.json            → Lorenz curve data for chart 6a
/data/heatmap.json           → daily generation matrix for chart 2a
/data/meta.json              → last_updated, row_count, source_url, schema_version
```

Each file uses a consistent envelope:

```json
{
  "meta": {
    "generated_at": "2026-04-14T06:12:00Z",
    "source": "LCCC Actual CfD Generation and Avoided GHG Emissions",
    "schema_version": 1
  },
  "data": [ ... ]
}
```

When the public API milestone arrives, the transition is:
1. Document the `site/data/*.json` URLs as the public API (they already exist).
2. Optionally add a Cloudflare Worker in front for rate-limiting, CORS headers, or versioning.
3. Optionally add DuckDB-WASM endpoint for ad-hoc queries (separate effort, not blocking).

This means zero architecture changes to "open the API door" — the door is already open, it just isn't documented yet.

---

## Architectural Patterns

### Pattern 1: Pipeline Seam = JSON Contract

**What:** Each stage writes to an agreed file format that the next stage reads. The stages share no in-memory state and no function calls across boundaries.

**When to use:** Always, for this project. The pipeline stages are: `raw CSV → DuckDB table → per-chart JSON → HTML`.

**Why:** Enables independent rewriting of any stage, easy debugging (inspect intermediate files), and the JSON seam doubles as the public API surface.

**Trade-offs:** Slightly more I/O than an in-memory pipeline. Completely acceptable at this data scale.

### Pattern 2: Fail Loud on Schema Drift

**What:** The validator exits with a non-zero code if the upstream CSV columns change, column types shift, or row counts drop unexpectedly. CI fails; the old site stays live.

**When to use:** Every run, before any write to the store.

**Why:** LCCC has changed its CSV format before (column renames, added columns). A silent failure would serve charts derived from partially-wrong data. Credibility loss from one bad chart is the project's highest risk.

**Trade-offs:** Occasional false positives if LCCC adds innocent new columns. Mitigation: validate required columns only, not exact column set.

### Pattern 3: Idempotent Upsert Store

**What:** Ingest uses `INSERT OR REPLACE` (or equivalent DuckDB `ON CONFLICT DO UPDATE`) keyed on `(Settlement_Date, CfD_ID)`. Running the pipeline twice produces the same result.

**When to use:** Every run.

**Why:** The pipeline will be re-run on failures, on schema migrations, and on historic backfills. Non-idempotent appends would corrupt the store.

### Pattern 4: Per-Chart View-Model Modules

**What:** One Python module per chart family, each exporting a single `build(con: duckdb.DuckDBPyConnection) -> dict` function that returns the JSON payload.

**When to use:** For every chart added to the pipeline.

**Why:** Chart logic is isolated. Adding a new chart = add a file and wire it in `derive.py`. No risk of one chart's query logic breaking another.

---

## Site Organisation

**Recommendation: `/charts/<slug>/index.html` per chart + `/index.html` gallery page.**

```
/                          → gallery / landing page, all chart thumbnails + captions
/charts/scissors/          → chart 3c full page (strike vs market scissors)
/charts/cost-per-tonne/    → chart 3d full page
/charts/cumulative/        → charts 3b + 6a combined page
/charts/heatmap/           → chart 2a full page
```

Rationale:
- Per-chart pages are directly shareable URLs (journalists can link to one chart).
- Gallery index serves the "one page, understand the whole story" use case.
- Each chart page embeds its own JSON `<script>` fetch, source citation, and editorial caption.
- A single long-scroll page is an anti-pattern here: chart 3c is a zoom-interactive time series, chart 2a is a 2D heatmap — they need different viewport heights and controls. Mixing them on one page degrades UX.

---

## External Data Joins (Phase Mapping)

| Phase | Source | Integration point | What it unlocks |
|-------|--------|-------------------|-----------------|
| 1 | LCCC generation CSV | Primary store | Charts 3c, 3d, 3b/6a, 2a |
| 2 | LCCC CfD Register | `pipeline/fetch_register.py` → `cfd_register` table | Charts 1a, 1b, 1c (capacity factor) |
| 3a | Elexon / NESO wholesale prices | `pipeline/fetch_elexon.py` → `external_wholesale` table | Charts 4a, 4b (cannibalisation) |
| 3b | NESO BMRS constraint payments | `pipeline/fetch_bmrs.py` → `external_constraints` table | Chart 5a (curtailment) |
| 3c | UK ETS + DEFRA carbon series | `pipeline/fetch_carbon.py` → `external_carbon` table | Chart 3d overlays |

Each external source is a separate, optional fetch module. Failing to fetch an external source fails only the charts that depend on it — it does not prevent the primary LCCC charts from rebuilding.

---

## Update Cadence and Cache Invalidation

| Step | Detail |
|------|--------|
| Trigger | GitHub Actions `schedule: cron('5 6 * * *')` — runs at 06:05 UTC, after LCCC's typical overnight update window |
| Build time | Expected ~60–90 seconds (fetch + DuckDB query + Jinja2 render) |
| Deploy | `wrangler pages deploy site/` or push to `gh-pages` branch |
| Cache invalidation | Cloudflare Pages: atomic deployment; new deployment URL invalidates automatically. GitHub Pages: asset filenames include a build-date hash injected by the render step, forcing browser cache busts. |
| Stale-on-failure | If CI fails (schema drift, LCCC unreachable), the previous deployment stays live unchanged. No stale data is served — the old data is served. The CI failure triggers a GitHub notification. |
| Data freshness indicator | `meta.json` and a footer timestamp on every page show the last successful ingest date, so users know if they're seeing yesterday's data. |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Fetching raw CSV at browser render time

**What people do:** Chart JS code fetches the 18 MB+ CSV directly from LCCC at page load.

**Why it's wrong:** 18 MB over mobile, LCCC has no SLA, CORS headers may not be set, and it exposes the site to LCCC uptime. Also makes reproducibility impossible.

**Do this instead:** Python pipeline fetches and aggregates at build time; browser receives pre-baked JSON (<100 KB per chart).

### Anti-Pattern 2: Pandas-only pipeline without a store

**What people do:** Every build re-reads the CSV with `pd.read_csv()`, re-derives everything, re-renders. (This is what the existing prototype does.)

**Why it's wrong:** As the CSV grows, build time grows linearly. More importantly, there is no stable query layer to add cross-source joins or support a future API. Hard to make idempotent.

**Do this instead:** CSV → DuckDB upsert (fast, incremental). All derivations query DuckDB SQL. Build time stays constant regardless of CSV growth.

### Anti-Pattern 3: Putting chart business logic in Jinja2 templates

**What people do:** Aggregation or formatting logic bleeds into templates (e.g., Jinja2 filters that compute sums, group-bys).

**Why it's wrong:** Templates are untested. Logic in templates is invisible in diffs, hard to unit-test, and breaks the pipeline seam contract.

**Do this instead:** Templates receive fully-computed, display-ready JSON. They perform only string interpolation and HTML structure.

### Anti-Pattern 4: Single monolithic pipeline script

**What people do:** One `build.py` that fetches, validates, derives, and renders in a single file with shared mutable state.

**Why it's wrong:** Any stage failure rolls back all context. Impossible to run stages independently for debugging. The existing `plot_cfd_cost.py` is this pattern — acceptable as a prototype, not as the final shape.

**Do this instead:** Stages are separate importable modules, each runnable in isolation with `python -m pipeline.fetch`, `python -m pipeline.derive`, etc.

---

## Suggested Build Order (Phase → Component Dependencies)

```
Phase 1 (Foundation)
  Step 1.1  DuckDB schema + Store Writer
            → unblocks: everything else
  Step 1.2  Fetcher + Validator
            → depends on: Step 1.1 (schema definition)
  Step 1.3  Chart-model builders (3c, 3d, 3b/6a, 2a)
            → depends on: Step 1.1 (populated store)
  Step 1.4  Renderer + HTML templates + design system
            → depends on: Step 1.3 (JSON output exists)
  Step 1.5  CI workflow (cron + deploy)
            → depends on: Steps 1.1–1.4 all green

Phase 2 (CfD Register join)
  Step 2.1  Fetcher + validator for CfD Register CSV
            → depends on: Phase 1 store pattern established
  Step 2.2  Chart-model builders 1a, 1b, 1c
            → depends on: Step 2.1

Phase 3 (External data joins)
  Step 3.1  Elexon wholesale fetcher + store
  Step 3.2  NESO BMRS fetcher + store
  Step 3.3  Chart-model builders 4a/4b, 5a
            → depends on: Steps 3.1/3.2
  Step 3.4  Evaluate DuckDB-WASM for chart 4a if Elexon data exceeds ~1M rows

Phase 4 (Public API)
  Step 4.1  Document site/data/*.json URLs as public API
  Step 4.2  Add meta.json with schema_version, last_updated
  Step 4.3  Optional: Cloudflare Worker for CORS + rate limit headers
  → Zero pipeline changes; API already exists as static files
```

---

## Integration Points

### External Services

| Service | Integration Pattern | Cadence | Failure mode |
|---------|---------------------|---------|--------------|
| LCCC data portal | HTTP GET CSV; no auth | Daily | Fail loud; keep previous store |
| LCCC CfD Register | HTTP GET CSV; no auth | Weekly or on-change | Fail loud for Phase 2 charts only |
| Elexon / NESO APIs | REST API; may need API key | Daily (Phase 3) | Fail loud for Phase 3 charts only |
| GitHub Actions | `schedule:` cron trigger | Daily | Re-run manually if missed |
| Cloudflare Pages | `wrangler pages deploy` | On build success | Zero downtime atomic deploy |

### Internal Boundaries

| Boundary | Contract | Notes |
|----------|----------|-------|
| Fetcher → Validator | Raw CSV file on disk | Validator never calls Fetcher |
| Validator → Store | Validated DataFrame / CSV path | Store never calls Validator directly |
| Store → Derive | DuckDB connection / file path | Derive queries via SQL, no ORM |
| Derive → Render | `site/data/*.json` files | Render reads files; does not call Derive |
| Render → Deploy | `site/` directory | Deploy does not know about pipeline stages |

Every boundary is a file or directory, not a function call across modules. This is the property that makes stages independently runnable and debuggable.

---

## Scaling Considerations

This is a static site serving pre-baked files. "Scaling" means CDN throughput, not compute.

| Scale | Implication |
|-------|------------|
| 0–10k daily visitors | No changes needed; Cloudflare Pages free tier serves this easily |
| 10k–1M daily visitors | Still zero cost on Cloudflare Pages; CDN absorbs all load |
| Viral spike (1M+ in a day) | Static files on Cloudflare absorb any spike; no origin server to protect |
| Dataset growth (10M rows) | DuckDB columnar queries stay fast; `.duckdb` file may grow to ~50 MB; consider DuckDB COPY TO Parquet + git LFS |
| Many more charts | Each chart is one Python module + one JSON file; linear cost, no architectural change |

The only scaling concern worth noting: if the DuckDB file grows beyond ~100 MB (unlikely until dataset covers 20+ years), switch to `COPY TO 'data/cfd.parquet'` at the end of the store step and query the Parquet file directly at derive time. DuckDB supports this without code changes.

---

## Sources

- [DuckDB vs SQLite: complete comparison (DataCamp)](https://www.datacamp.com/blog/duckdb-vs-sqlite-complete-database-comparison)
- [Building analytics stacks with Python, Parquet, and DuckDB (KDnuggets)](https://www.kdnuggets.com/building-your-modern-data-analytics-stack-with-python-parquet-and-duckdb)
- [High performance data viz with DuckDB and Parquet (Travis Horn)](https://travishorn.com/high-performance-data-visualization-in-the-browser-with-duckdb-and-parquet/)
- [Observable Framework data loaders docs](https://observablehq.com/framework/data-loaders) (403 on direct fetch; referenced via forum discussions)
- [GitHub Actions with pandas data loader on Observable Framework (Observable Forum)](https://talk.observablehq.com/t/github-actions-with-pandas-data-loader-on-observable-framework/9309)
- [Deploying Observable Framework on GitHub Pages with Python data loaders (Observable Forum)](https://talk.observablehq.com/t/deploying-observable-framework-on-github-pages-with-r-and-python-as-data-loaders/9043)
- [Scheduled builds for Cloudflare Pages via GitHub Actions (Benjamin Abt)](https://benjamin-abt.com/blog/2025/07/14/scheduled-builds-cloudflare-github-actions/)
- [Pandera vs Great Expectations comparison (endjin)](https://endjin.com/blog/a-look-into-pandera-and-great-expectations-for-data-validation)
- [Creating a static API from a repository (CSS-Tricks)](https://css-tricks.com/creating-static-api-repository/)
- [DuckDB WASM examples: Observable Plot + Svelte + Parquet (GitHub)](https://github.com/duckdb-wasm-examples/observableplot-svelte-typescript)

---
*Architecture research for: UK CfD public-education dataviz static site*
*Researched: 2026-04-14*
