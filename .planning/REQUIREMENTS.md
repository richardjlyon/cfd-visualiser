# REQUIREMENTS — CfD Visualiser (v1)

## Core Value

A non-specialist can land on the site, look at a single chart, and walk away with an accurate, sourced understanding of what UK CfDs actually cost and deliver.

---

## v1 Requirements

### Pipeline

- [ ] **PIPE-01**: Daily automated fetch of the LCCC *Actual CfD Generation and Avoided GHG Emissions* CSV from the official data portal
- [ ] **PIPE-02**: Pandera schema validation on ingest — pipeline exits non-zero and does not write to the store when upstream schema drifts
- [ ] **PIPE-03**: Idempotent upsert into a DuckDB file keyed on a stable primary key (e.g., `Settlement_Date + CfD_Unit`); re-runs produce identical aggregates
- [ ] **PIPE-04**: Raw CSV archive — every daily snapshot is retained so upstream revisions can be detected by diffing historical aggregates
- [ ] **PIPE-05**: Dead-man's switch integration (Healthchecks.io free tier or equivalent) that pages the maintainer when the daily run misses
- [ ] **PIPE-06**: Keepalive commit strategy (or equivalent) to prevent GitHub Actions' 60-day inactivity cutoff from silently disabling the cron
- [ ] **PIPE-07**: Named constants for monetary and energy units (£, £m, £bn, MWh, GWh, tCO₂e) and fixture-based assertions guarding unit correctness
- [ ] **PIPE-08**: Explicit timezone convention (UTC-naive date-only OR `Europe/London`) documented and enforced at the ingest boundary

### Charts v1

- [ ] **CHART-01**: Chart **3c** — Strike price vs wholesale price "scissors" time series, interactive (zoom, toggle allocation rounds: Investment Contracts / AR1 / AR2 / AR4 / AR5)
- [ ] **CHART-02**: Chart **3d** — £/tCO₂ avoided explorer, interactive filters (round / technology / year), with UK ETS price and DEFRA social cost of carbon as reference overlays
- [ ] **CHART-03**: Chart **3b + 6a** — Cumulative consumer subsidy (£bn) stacked by technology/project, with a Lorenz curve of subsidy concentration (interactive scatter)
- [ ] **CHART-04**: Chart **2a** — Daily generation heatmap (year × day-of-year) for wind + solar CfD output, with a mobile-simplified fallback (collapsed to weekly or monthly grid below 768px)

### Editorial & Trust

- [ ] **EDIT-01**: Every chart has a one-line "pointed but sourced" caption naming the specific defect it exposes
- [ ] **EDIT-02**: Every chart shows a visible source citation (dataset name + URL) and a "last updated" stamp
- [ ] **EDIT-03**: Every chart has a methodology page explaining derivation, assumptions, and data source — must be live before the associated chart is public (hard gate for **CHART-02** / 3d)
- [ ] **EDIT-04**: Every chart has a "What does this mean?" plain-language boxout (2–3 sentences) naming the policy implication in the editorial voice
- [ ] **EDIT-05**: Editorial grammar rule — factual chart language (e.g., "consumers paid £X/MWh more than market price") is kept distinct from editorial framing (e.g., "this represents waste"); loaded words do not appear inside chart captions

### Hosting & Ops

- [ ] **OPS-01**: Static site hosted on Cloudflare Pages, deployed on every successful daily pipeline run
- [ ] **OPS-02**: Daily rebuild scheduled via GitHub Actions cron (timed to occur after the LCCC update window)
- [ ] **OPS-03**: Charts are mobile-legible — accessible colour palette, no colour-only encoding, minimum tap target sizes, readable on a narrow viewport
- [ ] **OPS-04**: Each chart exposes a downloadable CSV and/or JSON of its view-model under a stable URL (`site/data/<chart>.json`) — doubles as the seed for the deferred public API
- [ ] **OPS-05**: Privacy-preserving analytics only (Plausible-style or none) — no cookie banner required, no third-party tracking

---

## v2 / Deferred

- [ ] Chart **1a, 1b, 1c** — capacity factor family (requires CfD Register join for installed MW per unit)
- [ ] Chart **2b** — load-duration curve
- [ ] Chart **2c** — rolling 7-day minimum generation
- [ ] Chart **3a** — £/MWh subsidy time series by allocation round
- [ ] Chart **3e** — project-level bang-for-buck scatter (total subsidy £m vs total tCO₂ avoided)
- [ ] Chart **6b** — stacked bar of future CfD subsidy obligations by contract expiry year
- [ ] Chart **7a** — monthly net CfD settlement alongside cumulative subsidy (2022 clawback in context)
- [ ] Public query/JSON API with documented endpoints (the `site/data/*.json` files become the API surface)
- [ ] Deeplinkable filter state (share a URL that reopens the chart at a specific filter combination)
- [ ] Auto-generated OG social-card images per chart
- [ ] RSS / Atom feed of meaningful updates

## v3 / External Data

- [ ] Chart **4a** — wholesale capture price vs fleet wind output (Elexon / NESO wholesale prices)
- [ ] Chart **4b** — capture-price ratio by year
- [ ] Chart **5a** — estimated curtailment vs generation (NESO BMRS constraint payments)
- [ ] UK ETS price overlay on 3d sourced from a live official series (rather than static constants)
- [ ] DEFRA social cost of carbon overlay on 3d sourced from the current GOV.UK trajectory

## Out of Scope

- Renewables Obligation Certificate (ROC) revenues — separate subsidy regime, not in this dataset
- Embedded benefits and network-charge avoidance — out of the CfD envelope
- Capacity Market payments to backup gas — different scheme entirely
- Lifecycle emissions accounting (manufacture, decommissioning) — different project
- User accounts, comments, login of any kind — no user-generated content on this site
- Paid hosting or any non-trivial running cost — stays on free-tier static hosting
- Scrollytelling — deferred until engagement data justifies the implementation complexity
- Server-side rendering, live Python web process (Streamlit/Dash), or any non-static backend
- Heavy JS frameworks (Next.js / React SPA) — wrong tool for Markdown-first static content

---

## Traceability

*Filled in during roadmap creation — maps each REQ-ID to the phase that delivers it.*

| REQ-ID | Phase |
|--------|-------|
| — | — |
