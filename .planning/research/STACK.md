# Stack Research

**Domain:** Data-journalism / public-education dataviz static site — daily-rebuilt, Python pipeline, interactive charts
**Researched:** 2026-04-14
**Confidence:** HIGH (versions confirmed from npm/pip registries; architecture confirmed from official docs)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Observable Framework** | 1.13.4 | Static site generator + chart host | Purpose-built for exactly this use case: polyglot data loaders (Python runs at build time), Markdown pages with embedded JS, outputs pure static HTML/CSS/JS with zero server runtime. Every other SSG requires bolting on a charting framework and routing data by hand. |
| **Observable Plot** | 0.6.17 | Interactive charts (time series, heatmap, scatter, Lorenz) | Grammar-of-graphics API that ships 47 KB minified. Produces analyst-credible charts (e.g. NYT, Financial Times derivations) with minimal boilerplate. Has native `rect`/`cell` for heatmaps, `dot` for scatter, `line` + `area` for time series. Mobile-responsive SVG by default. First-class citizen inside Framework pages — `display(Plot.plot(...))` just works. |
| **DuckDB (Python)** | 1.5.2 | Data store + query engine for cleaned data | Columnar analytics engine embedded in Python. Reads CSV natively, runs SQL aggregations 10–50x faster than pandas for analytical queries, outputs Parquet or JSON. The `.duckdb` file is a single portable artefact. Framework has a first-party `DuckDBClient` for in-browser WASM queries too (opening the door to static API endpoints later). |
| **Polars** | 1.39.3 | CSV ingest, cleaning, validation | Rust-backed DataFrame library. 5x faster CSV reads than pandas, 87% less memory, multi-threaded. Replaces the current `pandas` prototype for the daily ingest step. Polars outputs directly to Parquet/CSV for DuckDB to consume. |
| **matplotlib** | 3.10.8 | Static PNG export for OG/social previews | Existing dependency. Generates `<meta og:image>` PNGs at build time — one per chart. Not used in the interactive page; only for social sharing and SEO crawlers that cannot execute JS. The prototype's `plot_cfd_cost.py` is the template. |
| **Cloudflare Pages** | — | Static hosting + global CDN | Free tier: unlimited bandwidth, 500 builds/month, 300+ edge locations. Recommended over alternatives (see below). |
| **GitHub Actions (cron)** | — | Daily rebuild scheduler | `schedule: cron: '30 6 * * *'` runs the Python pipeline, commits artefacts, triggers Cloudflare Pages deploy. Free for public repos. |
| **uv** | latest | Python environment + dependency management | Already in use (`pyproject.toml`, `.python-version`). Faster than pip/poetry, reproducible lockfiles, native GitHub Actions support. |

---

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **Pico CSS** | 2.x | Baseline design system | Applied as a classless stylesheet to Framework Markdown pages. Gives clean typography, sensible spacing, and responsive prose layout with zero custom CSS. Layer chart-specific CSS tokens on top (palette variables, font sizes). Use instead of Tailwind — the site is content-first, not component-heavy. |
| **D3** (subset) | 7.x | Scale helpers, Lorenz curve geometry | Observable Plot is built on D3 internals. For the Lorenz curve (chart 6a) and any bespoke curve geometry not in Plot's mark library, use D3's `scaleLinear`, `line`, and `area` directly. Already included transitively with Plot — no extra bundle cost. |
| **pyarrow** | latest | Parquet read/write from Python | Required by Polars for Parquet I/O; also used when DuckDB exports `.parquet` artefacts for the Framework data loaders. |
| **httpx** | latest | HTTP client for daily CSV fetch | Replaces bare `urllib` / `requests`. Async-capable, built-in timeout+retry semantics. Use for the daily LCCC download and future Elexon/NESO API calls. |
| **pytest** | latest | Pipeline unit tests | Test idempotency of the ingest step, schema validation of cleaned data, and column-computation correctness (CF formula, subsidy calc). Run in CI before build. |

---

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **uv** | Python env + lockfile | `uv run python pipeline/ingest.py` in CI; `uv sync` in dev. Already bootstrapped. |
| **Node.js 20 LTS** | Observable Framework build | Framework is an npm package; `npx @observablehq/framework build` produces `dist/`. Pin Node 20 in CI with `actions/setup-node`. |
| **GitHub Actions** | CI + cron schedule | One workflow: `schedule` trigger → run Python pipeline → `npx @observablehq/framework build` → deploy to Cloudflare Pages via `cloudflare/pages-action`. |
| **Wrangler / Cloudflare Pages Action** | Deploy | `cloudflare/pages-action@v1` in the workflow pushes `dist/` to Cloudflare Pages on every successful build. |
| **CronTab Guru** | Cron expression validation | Use at https://crontab.guru to verify schedule expressions before committing. |

---

## Installation

```bash
# Python pipeline (uv — already configured)
uv add polars duckdb pyarrow httpx
uv add --dev pytest

# Observable Framework (creates src/ scaffold)
npx @observablehq/framework@1.13.4 create
# Choose: TypeScript: no, npm, project directory: src/

# Pico CSS (copied into src/assets/ or linked via CDN in Framework config)
# No npm install needed — link from picocs.io CDN or download 7 KB file
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Observable Framework | Quarto | Use Quarto if the primary output format is PDF/Word scientific reports, or if the team is heavily R-based and wants Shiny integration. For public-facing interactive web charts with Python back-ends, Framework is better: data loaders are a cleaner primitive than Quarto's OJS cells. |
| Observable Framework | Astro + custom chart code | Use Astro if you need a full CMS, blog with hundreds of posts, or React/Svelte component ecosystem. For a chart-first data site with O(10) pages, Astro's flexibility is overhead, not benefit. |
| Observable Framework | 11ty / Jekyll + Plotly embeds | Use for pure prose publishing where charts are incidental. For a site where charts ARE the content, Framework's data loader → Plot pipeline is far tighter. |
| Observable Plot | Plotly.js | Use Plotly when you need 3D charts, statistical traces (box/violin), or built-in download buttons without custom code. Plotly's 3.5 MB bundle is a hard penalty on mobile. For this project's chart types (time series, heatmap, scatter, Lorenz), Plot produces equivalent results in 47 KB. |
| Observable Plot | Vega-Lite | Vega-Lite is a reasonable alternative — declarative JSON specs are reproducible and server-renderable. The ergonomics are clumsier inside Framework's reactive JS cells compared to Plot's imperative API. Choose Vega-Lite if you need spec portability across Python/R/JS (e.g., Altair interop). |
| Observable Plot | ECharts | ECharts has excellent mobile performance and rich built-in chart types. Choose it for dashboards targeting low-powered Android devices or requiring animated transitions. The API is more verbose for data-journalism style exploratory charts. |
| DuckDB (store) | SQLite | Use SQLite if the data model is primarily transactional (many small row inserts, foreign-key joins, user data). For aggregated analytical queries over time-series energy data, DuckDB is 10–50x faster and its SQL dialect handles window functions and `PIVOT` natively. |
| DuckDB (store) | Flat Parquet files | Use Parquet-only if the pipeline is purely batch (no ad-hoc queries needed). Parquet files are excellent artefacts for the Framework data loaders to consume; the recommendation is: ingest → DuckDB (store + compute) → export Parquet/JSON/CSV artefacts → Framework consumes the artefacts. Both technologies are in play; DuckDB is the query layer, Parquet is the export format. |
| Polars | pandas | Use pandas if the team is more familiar with it and dataset sizes stay below ~500 K rows. The prototype already uses pandas and could remain for v1 if rewrite cost is high. For a production daily pipeline that may grow to multi-year, multi-project resolution (daily × ~100 CfD units × 8 years ≈ 300 K rows today, scaling), Polars is the right default. Migration cost is low — the API is similar. |
| Cloudflare Pages | GitHub Pages | Use GitHub Pages for trivial sites with no build step and no CDN requirement. It has no concept of build commands for non-Jekyll sites without Action gymnastics, and its CDN footprint is smaller than Cloudflare's 300+ PoPs. The inactivity-disable risk of GitHub Actions cron (60-day cutoff) is manageable with a keep-alive step. |
| Cloudflare Pages | Netlify | Netlify is equivalent in capability and slightly better DX (UI, deploy previews). The differentiator here is bandwidth: Netlify's free tier caps at 100 GB/month; Cloudflare Pages is unlimited. A chart site with og:image PNGs and Parquet artefacts can hit 100 GB if it gets any press coverage. |
| Pico CSS | Tailwind CSS | Use Tailwind if the team is building a component-heavy UI with many custom variants. For a Markdown-first data site inside Observable Framework, adding Tailwind's PostCSS build step to the Framework pipeline is friction for marginal gain. Pico's 7 KB classless approach pairs better with Framework's Markdown pages. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Next.js / React SPA** | A full React build adds 100–200 KB of framework JS, requires a Node runtime or SSR host (Vercel, not free at scale), and solves problems this project doesn't have (routing, auth, state management). Charts are the product — the shell should be invisible. | Observable Framework |
| **Django / Flask** | A Python web server requires a persistent process (rules out zero-cost static hosting), complicates daily rebuild (you'd need to restart the server), and adds a security surface area. The data is static by nature — build it statically. | Python pipeline → Observable Framework build → static host |
| **Tableau / Flourish / Datawrapper** | Paid BI tools or embeds create vendor lock-in, limit chart customisation (the scissors chart and Lorenz curve require bespoke geometry), and don't support a reproducible open pipeline from source data. | Observable Plot in Framework |
| **Plotly.js (as primary library)** | 3.5 MB minified is a hard mobile penalty. Plotly's chart types are geared toward scientific dashboards; its defaults produce analyst-facing (dense) charts, not public-education (legible) ones. Customising Plotly to look clean costs as much effort as just using Plot. | Observable Plot |
| **D3 from scratch** | D3 is the right tool for bespoke interactive journalism pieces with custom layouts. For a suite of 15+ standard chart types that need to be maintained by one or two people, the low-level D3 API is disproportionate — it adds weeks to each chart. Use D3 selectively for geometry helpers where Plot falls short (Lorenz curve custom path). | Observable Plot (with D3 primitives for edge cases) |
| **Jupyter notebooks as the pipeline** | Notebooks are excellent for exploration but fragile as production pipelines (hidden state, non-idempotent, hard to test, version-control noise). The daily rebuild must be a deterministic CLI-runnable script. | Plain `.py` scripts called by `uv run` |
| **pandas (as the only pipeline tool)** | pandas 3.x is good, but its single-threaded CSV reader and row-oriented GroupBy are the bottleneck in a daily analytical pipeline. Using pandas for heavy aggregations (grouped by unit, by year, by allocation round) will be noticeably slow as the dataset grows. | Polars for ingest + aggregation; pandas only if a library requires it |
| **Streamlit / Dash / Panel** | These frameworks produce server-rendered interactive dashboards that require a live Python process — incompatible with free static hosting. They're the right choice if you need server-side query execution at user request time. | Observable Framework (build-time Python + browser-side WASM) |

---

## Stack Patterns by Variant

**If chart complexity stays within Observable Plot's mark library (v1 scope — scissors, heatmap, scatter, Lorenz approximation):**
- Use Plot exclusively; no D3 primitives needed
- Keep all chart code inside Framework `.md` pages as inline `js` blocks

**If the Lorenz curve requires a precise area-under-curve geometry not in Plot 0.6:**
- Import `d3-shape` line/area generators directly in the Framework page
- D3 is a transitive dependency of Plot — zero bundle cost

**If future milestones add a static JSON API endpoint:**
- DuckDB exports named JSON files to `src/data/api/` during the Python pipeline step
- Framework copies them verbatim to `dist/data/api/` — instant static API with no server
- No architecture change required; this is already a first-class Framework pattern

**If future milestones need Elexon / NESO API joins:**
- Add `httpx`-based fetchers as separate pipeline modules
- Store external data in the same DuckDB file under separate tables
- No SSG or hosting change needed

**If the GitHub Actions 60-day inactivity limit becomes a concern:**
- Add a `workflow_dispatch` step at the top of the cron workflow
- Or: push a no-op commit to `data/` on every successful run (the pipeline artefacts already do this)

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `@observablehq/framework@1.13.4` | Node.js 18+ (20 LTS recommended) | Framework 1.x requires Node 18+; pin 20 LTS in CI |
| `@observablehq/plot@0.6.17` | Bundled inside Framework | Framework includes Plot via `npm:@observablehq/plot` — do not add as separate dep unless you need a specific patch version |
| `duckdb@1.5.2` (Python) | Python >=3.10 | Project uses Python 3.13 (pyproject.toml) — compatible |
| `polars@1.39.3` | Python >=3.9 | Compatible with Python 3.13 |
| `pandas@3.0.2` | Python >=3.9 | Keep as optional dep for any libraries that require it (e.g. some matplotlib helpers) |
| `matplotlib@3.10.8` | Python >=3.9 | Already in pyproject.toml; used only for static PNG export |
| `pyarrow` | Polars and DuckDB | Both Polars and DuckDB use pyarrow for Parquet I/O; install once, shared |

---

## Architecture Shape (brief)

```
data/
  raw/          # downloaded CSV from LCCC (gitignored)
  clean.duckdb  # single DuckDB file — the durable store

pipeline/
  ingest.py     # httpx download → Polars validation → DuckDB load
  compute.py    # DuckDB SQL: aggregations, derived columns, export artefacts

src/            # Observable Framework project root
  data/         # Framework data loader outputs (Parquet/JSON/CSV artefacts)
  pages/        # .md files — one per chart family
  components/   # shared JS chart helpers (colour scale, caption template)
  assets/       # pico.css, brand fonts, favicon

dist/           # Framework build output — deployed to Cloudflare Pages

.github/
  workflows/
    daily.yml   # cron: '30 6 * * *' → pipeline → framework build → CF deploy
```

The pipeline and the SSG are deliberately separate processes. Python owns the data; Framework owns the HTML. They communicate via files in `src/data/`, which are Framework data loader outputs.

---

## Sources

- `npm view @observablehq/framework version` — confirmed 1.13.4 (HIGH confidence)
- `npm view @observablehq/plot version` — confirmed 0.6.17 (HIGH confidence)
- `pip index versions duckdb` — confirmed 1.5.2 (HIGH confidence)
- `pip index versions polars` — confirmed 1.39.3 (HIGH confidence)
- `pip index versions pandas` — confirmed 3.0.2 (HIGH confidence)
- `pip index versions matplotlib` — confirmed 3.10.8 (HIGH confidence)
- https://observablehq.com/framework/data-loaders — Python data loader documentation (HIGH confidence)
- https://observablehq.com/framework/lib/duckdb — DuckDB WASM client in Framework (HIGH confidence)
- https://duckdb.org/2025/09/16/announcing-duckdb-140 — DuckDB 1.4.0 LTS announcement (HIGH confidence)
- https://www.datacamp.com/blog/duckdb-vs-sqlite-complete-database-comparison — DuckDB vs SQLite analytical workloads (MEDIUM confidence)
- https://www.kdnuggets.com/we-benchmarked-duckdb-sqlite-and-pandas-on-1m-rows-heres-what-happened — benchmark data (MEDIUM confidence)
- https://bejamas.com/compare/cloudflare-pages-vs-github-pages-vs-netlify — hosting comparison (MEDIUM confidence)
- https://hosted.md/blog/github-pages-vs-netlify-vs-cloudflare-pages-which-is-best-for-markdown-sites — bandwidth limits (MEDIUM confidence)
- https://github.com/observablehq/framework — Framework GitHub, stars and activity (HIGH confidence)
- https://simonwillison.net/2024/Mar/3/interesting-ideas-in-observable-framework/ — independent analysis of Framework architecture (MEDIUM confidence)
- pyproject.toml in this repo — Python 3.13 confirmed, uv in use, pandas + matplotlib already installed

---

*Stack research for: CfD Visualiser — data-journalism static site*
*Researched: 2026-04-14*
