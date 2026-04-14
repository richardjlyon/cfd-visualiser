# Project Research Summary

**Project:** CfD Visualiser — UK Low Carbon Contracts public-education chart site
**Domain:** Data-journalism static site — daily-rebuilt, Python pipeline, interactive charts
**Researched:** 2026-04-14
**Confidence:** HIGH

---

## Executive Summary

The CfD Visualiser is a daily-rebuilt public-education website that turns LCCC generation and subsidy data into four high-payload interactive charts, framed with pointed-but-sourced editorial captions. The canonical approach for this class of product is a Python analytics pipeline (ingest → validate → DuckDB store → derive pre-baked JSON) feeding a static site renderer that delivers lightweight chart pages to a CDN. The pipeline and the renderer share no runtime state; they communicate through a JSON file contract. This separation is the key architectural property: it keeps the pipeline testable in Python, the charts maintainable in JS, and the deployment trivially static.

The recommended stack is: Polars + DuckDB for ingest and derivation, Observable Plot as the charting library, Cloudflare Pages for zero-cost hosting, and GitHub Actions for the daily cron rebuild. The single contested question — which static-site generator to use — is resolved as a Key Decision below. For editorial annotation depth, methodology pages, and a solo-maintainer who owns both the Python pipeline and the HTML output, Observable Framework is the right choice: its data-loader primitive eliminates the bespoke plumbing that a Jinja2 approach would require to pass JSON artefacts into pages.

The dominant risks are not architectural but editorial and operational: silent upstream schema drift will silently corrupt every chart if the ingest validator is not built from day one; the GitHub Actions 60-day inactivity cutoff will silently stale the site if a keepalive is not wired in; and the £/tCO₂ avoided chart (3d) will be dismissed by critics if the methodology page is not live before that chart ships. All three risks have well-understood mitigations and must be addressed in Phase 1, not retrofitted later.

---

## Key Decision: SSG — Observable Framework vs Jinja2 + Plot Bundle

**Decision: Use Observable Framework.**

Both STACK.md and ARCHITECTURE.md agree on: DuckDB store, Polars ingest, Observable Plot as charting library, pre-baked JSON per chart, Cloudflare Pages hosting, GitHub Actions cron. The only genuine tension is the SSG layer.

ARCHITECTURE.md argues for a Python Jinja2 renderer with Observable Plot shipped as a plain JS bundle, citing a desire to keep the stack Python-only and avoid a Node.js dependency in CI.

STACK.md recommends Observable Framework 1.13.4, which uses Python data loaders at build time and produces pure static HTML/CSS/JS output.

**The call is Observable Framework, for these reasons:**

1. **Editorial annotation and methodology pages are the core differentiator.** FEATURES.md identifies the methodology note, the "what does this mean?" boxout, and the site-level about page as P1 requirements that distinguish this site from a neutral data portal. Observable Framework's Markdown pages handle prose + embedded interactive charts as a first-class primitive. A Jinja2 approach can achieve the same result, but every page requires hand-written HTML structure around chart placeholders — more boilerplate for the same output, maintained by a solo developer.

2. **The Python data-loader primitive is a tighter seam than Jinja2 + JSON files.** Framework's data loaders run Python at build time and pipe stdout directly into the page — the JSON contract between pipeline and renderer is enforced by the Framework runtime, not by file-naming conventions. This reduces the surface area for "file written to wrong path" bugs.

3. **Node.js in CI is a one-line addition.** `actions/setup-node@v4` with `node-version: '20'` adds approximately 5 seconds to the build. The claimed benefit of a Node-free CI is real but marginal against the ergonomic cost of maintaining a hand-rolled Jinja2 SSG for a site where Markdown prose + charts is the core unit.

4. **Framework's build output is pure static HTML.** No Node.js runtime is needed at serve time. Cloudflare Pages hosts the `dist/` output exactly as it would host a Jinja2-rendered `site/` directory.

5. **Future API surface is identical.** Both approaches produce `site/data/*.json` files that double as a static API. No advantage to Jinja2 here.

**The one legitimate concern from ARCHITECTURE.md stands:** do not use Framework's in-browser DuckDB-WASM for v1. Pre-bake all chart JSON at pipeline time; the browser receives a compact payload (<100 KB per chart). DuckDB-WASM is deferred to Phase 3+ if ad-hoc queries over the full dataset are ever needed.

**Agreed-upon stack (both research streams):**

| Layer | Technology |
|-------|-----------|
| Ingest | Polars + httpx |
| Validation | Pandera schema |
| Store | DuckDB (`data/cfd.duckdb`, git-committed) |
| Derivation | Python per-chart modules → JSON |
| SSG | **Observable Framework 1.13.4** |
| Charting | Observable Plot 0.6.17 |
| Design | Pico CSS 2.x (classless, Framework-compatible) |
| Hosting | Cloudflare Pages (free, unlimited bandwidth) |
| CI | GitHub Actions cron + `actions/setup-node` |

---

## Key Findings

### Recommended Stack

The Python pipeline side is uncontested: `uv` for environment management (already bootstrapped), `httpx` for the daily CSV fetch, `polars` for ingest and validation, `duckdb` as the durable columnar store, and `pyarrow` for Parquet I/O. The prototype's `main.py`/`plot_cfd_cost.py` are scaffolding only — the production pipeline rewrites them as separate importable modules under `pipeline/`. `matplotlib` is retained solely for static OG/social preview PNG generation.

Node.js 20 LTS is the single addition to the CI environment, required only for `npx @observablehq/framework build`. All package versions confirmed from registry:

**Core technologies:**
- **Observable Framework 1.13.4**: SSG + data loader runtime — purpose-built for Python-backed interactive chart sites
- **Observable Plot 0.6.17**: charting — 47 KB minified, grammar-of-graphics, bundled inside Framework
- **DuckDB 1.5.2 (Python)**: durable store + query layer — columnar, single-file, git-committable at ~5-15 MB
- **Polars 1.39.3**: CSV ingest — 5x faster than pandas, Rust-backed, multi-threaded
- **Cloudflare Pages**: hosting — unlimited bandwidth free tier, 300+ PoP CDN, atomic deploys
- **GitHub Actions cron**: scheduler — `schedule: cron('30 6 * * *')`, free for public repos
- **Pico CSS 2.x**: design system — 7 KB classless stylesheet, prose-first, no PostCSS build step

See `.planning/research/STACK.md` for full alternatives analysis and version compatibility matrix.

---

### Expected Features

The feature landscape is well-researched against OWID, Carbon Brief, Ember, Reuters Graphics, and The Pudding. The core differentiator for this site is the **editorial annotation layer**: baked-in SVG callouts that name the defect a chart exposes, paired with a collapsible methodology note. No comparable UK energy-subsidy site currently provides this combination.

**Must have (table stakes — P1):**
- Mobile-responsive layout — public chart site without this is not viable
- Plain-English headline per chart (declarative, names the defect, not the chart type)
- Source citation per chart with retrieval date
- "Last updated" timestamp pulled from build artefact, not a manual string
- Accessible colour ramps (Okabe-Ito for multi-series, viridis/cividis for sequential; WCAG 3:1)
- Fast first paint — pre-rendered SVG, JS progressive enhancement only
- Static permalink per chart — journalists must be able to link
- Screenshot-shareable design — chart legible at 1200×630 crop without prose
- Downloadable CSV per chart — low complexity, high analyst-credibility signal
- Per-chart methodology note (collapsible) — critical for 3d and 3c at minimum
- "What does this mean?" boxout per chart — distinguishes from neutral data portal
- Site-level about / methodology page — required before any chart is indexed
- Editorial annotation layer — baked SVG callouts (2022 cross on 3c; Hinkley C on 3e; Gini on 6a)
- Public GitHub repo link in footer

**Should have (competitive differentiators — P2):**
- Chart-as-deeplink with filter state in URL (`?round=AR1&year=2023`)
- OG social card images auto-generated per chart (1200×630)
- RSS/Atom feed of dataset updates
- "Compare rounds" full filter on 3d

**Defer (v2+):**
- Scrollytelling narrative for 3c scissors chart (Phase 3 only, high effort, needs engagement evidence)
- Dark mode (use CSS custom properties from day one for easy later retrofit)
- Public API (static JSON files are already the API; documentation is Phase 4)
- Capacity-factor family 1a/1b/1c (gated on CfD Register join, Phase 2)

**Anti-features (do not build):** user accounts, comments, cookie consent banners, heavy JS SPA framework, real-time data streaming, embedded third-party chart iframes, LLM chatbot.

See `.planning/research/FEATURES.md` for full chart-type feature matrix and competitor analysis.

---

### Architecture Approach

The architecture is a four-stage linear pipeline where every stage boundary is a file, not a function call. Python owns data; Framework owns HTML. They communicate through `src/data/*.json` files written by the derivation stage.

**Major components:**
1. **Fetcher + Validator** (`pipeline/fetch.py`, `pipeline/validate.py`) — HTTP download → Pandera schema assertion → hard exit on drift. Runs before any write.
2. **Store Writer** (`pipeline/store.py`) — idempotent upsert into `data/cfd.duckdb` keyed on `(Settlement_Date, CfD_ID)`. Re-runnable safely.
3. **Chart-model builders** (`pipeline/charts/scissors_3c.py`, etc.) — one Python module per chart family, each exporting a single `build(con) -> dict` function. Queries DuckDB SQL; outputs `src/data/<chart>.json`.
4. **Observable Framework** (`src/`) — Markdown pages consume JSON artefacts via data loaders; `npx @observablehq/framework build` produces `dist/` for deployment.
5. **CI scheduler** (`.github/workflows/rebuild.yml`) — daily cron at 06:05 UTC; orchestrates all stages; deploys `dist/` to Cloudflare Pages via `wrangler pages deploy`.

The `site/data/*.json` files double as a future static public API. No architecture change is required to open the API door — the files already exist at predictable stable URLs with a consistent metadata envelope.

See `.planning/research/ARCHITECTURE.md` for full data-flow diagrams, DuckDB vs alternatives decision table, and build-order dependency graph.

---

### Critical Pitfalls

The top five pitfalls, all Phase 1 concerns that cannot be retrofitted:

1. **Silent upstream schema drift** — LCCC has changed column names before. `pd.read_csv()` on an unexpected schema produces silent NaN propagation. Mitigation: Pandera schema validation before any store write; hard exit on violation; archive raw CSV with datestamp in `data/raw/`.

2. **GitHub Actions 60-day inactivity cutoff** — Scheduled workflows are disabled after 60 days with no repo activity. A stabilised site hits this exactly when it should run most reliably. Mitigation: wire a dead-man's switch (Healthchecks.io ping) and a keepalive commit/dispatch from day one.

3. **Non-idempotent pipeline producing aggregate drift** — Append-without-deduplication inflates cumulative £bn figures monotonically. Mitigation: upsert keyed on `(Settlement_Date, CfD_ID)`; assert `groupby().size().max() == 1` after each ingest.

4. **Unit confusion (MWh/GWh/TWh, £/£m/£bn, tCO₂/tCO₂e)** — The prototype already has `/ 1e6` and `/ 1e9` scattered without named constants. Mitigation: define named unit constants; assert headline aggregates against the LCCC-published ~£13bn total as a fixture.

5. **Editorial overreach on chart 3d (£/tCO₂ avoided)** — A single valid methodological objection can invalidate the site's most damning chart by association. Mitigation: use LCCC's own `Avoided_GHG_tonnes_CO2e` field as denominator without modification; publish the methodology page before 3d ships; source ETS and DEFRA SCC overlays from official GOV.UK publications.

Additional Phase 1 flags: stale CDN cache after deploy (use content-addressed filenames or `Cache-Control: no-cache` on JSON data files); mobile touch target failures on hover-only charts; accessibility failures on colour-only encoding (Okabe-Ito palette, solid/dashed line styles, SVG `<title>` elements).

See `.planning/research/PITFALLS.md` for all 16 pitfalls with detailed mitigation steps.

---

## Implications for Roadmap

### Phase 1: Foundation + Four CSV-Only Charts

**Rationale:** The four v1 charts (3c, 3d, 3b/6a, 2a) depend only on the LCCC CSV already in `data/`. No external data joins are needed. The full pipeline — ingest, store, derive, render, deploy — can be built end-to-end against this single source. This is the phase that proves the editorial thesis and validates whether the site generates interest.

**Delivers:** Live public URL with four interactive charts, editorial annotations, methodology page, downloadable CSVs, mobile-responsive layout, daily rebuild pipeline, Cloudflare Pages deployment.

**Addresses:** All P1 table stakes; editorial annotation layer; collapsible methodology notes; about page; "last updated" timestamp; permalink per chart; screenshot-shareable design.

**Build order within phase (from ARCHITECTURE.md dependency graph):**
1. DuckDB schema + store writer (unblocks everything)
2. Fetcher + Pandera validator
3. Chart-model builders for 3c, 3d, 3b+6a, 2a
4. Observable Framework scaffold + design system (Pico CSS, palette tokens, caption template)
5. Per-chart Framework pages (Markdown + Plot code)
6. CI workflow + Cloudflare Pages deploy
7. Methodology/about page (must be live before 3d ships)
8. Dead-man's switch (Healthchecks.io ping)

**Pitfalls to avoid in this phase:** schema validation (P1), keepalive (P2), CDN cache (P3), idempotent upsert (P4), timezone convention (P5), unit constants + fixtures (P6), mobile touch (P9), accessibility (P10), editorial rigour + methodology page (P12/P13/P14).

---

### Phase 2: CfD Register Join + Capacity Factor Family + Engagement Features

**Rationale:** The capacity-factor charts (1a, 1b, 1c) require the LCCC CfD Register as a second data source. This phase extends the pipeline with a new fetch+validate+store module, proving the architecture is extensible before the harder external joins in Phase 3. Phase 2 also lands deeplink filter state, OG social cards, and RSS — features deferred from Phase 1 pending evidence of usage patterns.

**Delivers:** Capacity factor time series (1a), degradation curves (1b), CF distribution (1c); deeplink URL filter state; OG social card images; RSS feed.

**Uses:** Existing pipeline pattern; new `pipeline/fetch_register.py`; DuckDB JOIN across `raw_generation` and `cfd_register` tables.

**Pitfalls to avoid:** P7 (capacity-factor denominator — pro-rate commissioning month); P8 (round/contract-type double-counting in per-round averages).

---

### Phase 3: External Data Joins (Elexon / NESO / Carbon Prices)

**Rationale:** Charts 4a/4b (cannibalisation) and 5a (curtailment) require Elexon wholesale prices and NESO BMRS data. Chart 3d's ETS/DEFRA overlays also require sourced external series. These are separate API integrations with different authentication and pagination patterns.

**Delivers:** Cannibalisation scatter (4a/4b), curtailment chart (5a), ETS/DEFRA overlays on 3d, lock-in tail (6b), 2022 clawback context (7a).

**Pitfalls to avoid:** P16 (ETS/DEFRA overlay provenance — use GOV.UK official series, not hardcoded values); P12 (methodological contestability on any chart using external data).

**Research flag:** This phase needs a `/gsd-research-phase` pass before scoping. Elexon/NESO API authentication, rate limits, and data schema require validation. The 4a cannibalisation chart may reach >1M rows (half-hourly Elexon data), at which point DuckDB-WASM in-browser is worth evaluating as a chart-specific architecture exception.

---

### Phase 4: Public API Documentation + Advanced UX

**Rationale:** The static JSON files in `site/data/` are already the public API. This phase is primarily documentation and optional Cloudflare Worker addition for CORS/rate-limit headers. Scrollytelling 3c and dark mode also land here if Phase 1/2 engagement data justifies the investment.

**Delivers:** Documented public API at `/data/*.json`; optional Cloudflare Worker; scrollytelling 3c (if warranted by engagement data); dark mode.

**Zero pipeline changes required** — the API door is already open from Phase 1.

---

### Phase Ordering Rationale

- **Phase 1 must build the pipeline seam correctly.** The JSON contract, idempotent upsert, schema validator, and dead-man's switch are correctness requirements, not hardening. Deferring any of them creates technical debt that will corrupt data before it is repaid.
- **Phase 2 is gated on Phase 1 pipeline pattern being proven.** The CfD Register join is a second instance of the same fetch→validate→store→derive pattern. Building it before that pattern is verified risks doing it wrong twice.
- **Phase 3 is gated on external API research.** Elexon/NESO rate limits and data formats are not fully documented in the research; scoping Phase 3 accurately requires a research pass.
- **Phase 4 is documentation and polish.** Sequencing it last ensures Phase 1/2 usage data informs which advanced UX features are worth the investment.

---

### Research Flags

**Needs `/gsd-research-phase` during planning:**
- **Phase 3:** Elexon API authentication and rate limits; NESO BMRS data schema and cadence; whether 4a will exceed the pre-baked JSON threshold and require DuckDB-WASM per-chart.

**Standard patterns — skip research-phase:**
- **Phase 1:** DuckDB upsert, Observable Framework data loaders, Cloudflare Pages deploy, and Pandera validation are all mature with high-confidence documentation. No novel integration required.
- **Phase 2:** The CfD Register is a second LCCC CSV — same fetch pattern as Phase 1. No novel integration required.
- **Phase 4:** Cloudflare Workers for CORS headers is a standard one-day task; API documentation is prose, not code.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions confirmed from npm/pip registries; Observable Framework architecture confirmed from official docs and independent analysis. Node.js version compatibility verified. |
| Features | HIGH | Grounded in direct inspection of OWID, Carbon Brief, Ember, Reuters Graphics; WCAG standards cited with spec references; Plausible/Fathom cookieless compliance confirmed. |
| Architecture | HIGH (pipeline) / MEDIUM (chart delivery) | Pipeline structure is well-established. The Jinja2 vs Framework tension is resolved by Key Decision above. Pre-baked JSON is correct for v1 scale; DuckDB-WASM deferred to Phase 3+. |
| Pitfalls | HIGH | LCCC schema drift confirmed from portal changelog; GitHub Actions 60-day limit is documented policy; unit confusion pitfall directly evidenced in the existing prototype code. |

**Overall confidence:** HIGH

### Gaps to Address

- **ETS price series source URL:** PITFALLS.md recommends the GOV.UK UK ETS auction clearing price series but does not confirm the exact endpoint. Must be located before 3d ships in Phase 1 (the chart requires this overlay).
- **DEFRA SCC trajectory URL:** The GOV.UK carbon valuation publication URL must be pinned before the methodology page is written.
- **LCCC `Reference_Type` column values:** The full set of unique values in the CSV determines whether Investment Contracts are correctly separated from allocation rounds. Must be inspected on the actual dataset before chart-model builders are written.
- **Observable Framework version pinning in CI:** The CI workflow should pin `@observablehq/framework@1.13.4` explicitly rather than using `latest` to prevent unexpected breaking changes on a daily build.

---

## Sources

### Primary (HIGH confidence)
- `npm view @observablehq/framework version` — confirmed 1.13.4
- `npm view @observablehq/plot version` — confirmed 0.6.17
- `pip index versions duckdb / polars / pandas / matplotlib` — all versions confirmed
- https://observablehq.com/framework/data-loaders — Python data loader architecture
- https://github.com/observablehq/framework — Framework GitHub (activity, stars)
- `pyproject.toml` in this repo — Python 3.13 confirmed, uv in use, prototype dependencies

### Secondary (MEDIUM confidence)
- https://simonwillison.net/2024/Mar/3/interesting-ideas-in-observable-framework/ — independent Framework architecture analysis
- https://bejamas.com/compare/cloudflare-pages-vs-github-pages-vs-netlify — hosting bandwidth comparison
- https://www.datacamp.com/blog/duckdb-vs-sqlite-complete-database-comparison — DuckDB vs SQLite analytical workloads
- https://www.kdnuggets.com/we-benchmarked-duckdb-sqlite-and-pandas-on-1m-rows-heres-what-happened — benchmark data
- https://ourworldindata.org/grapher/annual-co2-emissions-per-country — OWID feature inspection
- https://plausible.io/privacy-focused-web-analytics — Plausible cookieless compliance
- LCCC data portal changelog — confirms prior schema changes (2024); monitor for future changes

### Tertiary (requires validation during implementation)
- GOV.UK UK ETS auction clearing price series — URL not confirmed; must locate before 3d ships
- GOV.UK carbon valuation (DEFRA SCC) publication — exact URL must be pinned for methodology page

---

*Research completed: 2026-04-14*
*Ready for roadmap: yes*
