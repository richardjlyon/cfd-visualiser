# Roadmap: CfD Visualiser

## Overview

The CfD Visualiser delivers a daily-rebuilt public-education website that turns LCCC generation and subsidy data into four high-payload interactive charts. Phase 1 constructs the full pipeline skeleton and ships CHART-01 (scissors 3c) to a live public URL — proving the Python-loader → Observable Framework → Cloudflare Pages path end-to-end. Phase 2 adds the methodology infrastructure that gates CHART-02, then ships all three remaining charts in parallel plans.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Pipeline + First Chart** - Stand up the full pipeline seam, deploy to Cloudflare Pages, and ship CHART-01 (scissors 3c) as the first live interactive chart
- [ ] **Phase 2: Methodology + Remaining Charts** - Land the methodology page gate, then ship CHART-02, CHART-03, and CHART-04 in parallel plans

## Phase Details

### Phase 1: Pipeline + First Chart
**Goal**: The pipeline runs daily, the site is live on Cloudflare Pages, and a visitor can interact with the scissors chart (CHART-01) — complete with editorial caption, source citation, and downloadable JSON — proving the entire stack end-to-end
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06, PIPE-07, PIPE-08, CHART-01, EDIT-01, EDIT-02, EDIT-04, EDIT-05, OPS-01, OPS-02, OPS-03, OPS-04, OPS-05
**Success Criteria** (what must be TRUE):
  1. A visitor can open the scissors chart (3c) on a mobile device, zoom the time series, and toggle allocation rounds — without any error or blank state
  2. Every daily run fetches the LCCC CSV, validates it against the Pandera schema, upserts into DuckDB idempotently, and exits non-zero (leaving the previous deployment intact) if the schema drifts
  3. The chart page shows a pointed one-line caption, a visible source citation with the LCCC dataset URL, a "last updated" timestamp, a "What does this mean?" plain-language boxout, and a download link for the view-model JSON — all populated automatically from the build artefacts
  4. A maintainer receives an alert (Healthchecks.io ping miss) if the daily cron fails to complete, and a keepalive mechanism prevents the GitHub Actions 60-day inactivity cutoff from silently disabling the schedule
  5. The deployed site uses a privacy-preserving analytics approach (Plausible or none) — no cookie banner is required
**Plans**: 5 plans
**UI hint**: yes

Plans:
- [x] 01-01-store-schema-units-PLAN.md — Units, Pandera schema, DuckDB upsert, Wave-0 fixtures
- [x] 01-02-fetch-validate-archive-PLAN.md — httpx fetcher, validator, raw CSV archive, CLI entry, HC ping
- [x] 01-03-framework-scaffold-editorial-PLAN.md — Framework scaffold, Pico CSS + Okabe-Ito tokens, glossary/captions, EDIT-05 linter
- [x] 01-04-chart-builder-and-page-PLAN.md — CHART-01 view-model builder, meta artefact, scissors.md page, JSON download
- [ ] 01-05-ci-deploy-keepalive-PLAN.md — CI + daily cron workflows, Cloudflare Pages deploy, keepalive, OG card, analytics

### Phase 01.1: Shock counter, chart image export, and glossary tooltip JS (INSERTED)

**Goal:** A redesigned dark-themed dashboard ships at the live URL with a hero "shock counter" (build-time YTD subsidy + JS count-up at a pre-baked £/sec rate), a 4-card landing grid linking to detail pages for all 4 v1 charts (CHART-01 fully wired with dark-themed Plot; CHART-02/03/04 as placeholder-bodied detail pages with full editorial scaffolding), per-chart downloadable PNG, and vanilla-JS glossary tooltips on every editorial page — all under Tailwind v4 (Pico ripped out).
**Requirements**: CHART-01, CHART-02, CHART-03, CHART-04, EDIT-01, EDIT-02, EDIT-04, EDIT-05, OPS-01, OPS-02, OPS-03, plus phase-local pseudo-IDs REQ-SHOCK-01..03 (ytd_subsidy_gbp, gbp_per_sec_rate clamped, ytd_as_of=data-date), REQ-GLOSS-01..05 (slug schema migration, intermittent+dispatchable, vanilla-JS tooltip, XSS guard, refs-defined check), REQ-PNG-01..03 (dark 1200×630, 4 PNGs per build, schema-drift retention), REQ-DESIGN-01..08 (dark theme, Tailwind, card grid, file-routing, placeholder bodies), REQ-VERIFY-01 (post-build smoke).
**Depends on:** Phase 1
**Plans:** 9 plans

Plans:
- [ ] 01.1-01-PLAN.md — Wave 0 test scaffolding + Pillow + bash smoke skeleton (RED state for all downstream tasks)
- [ ] 01.1-02-PLAN.md — Tailwind v4 standalone CLI integration; observablehq.config.js update; Pico removed
- [ ] 01.1-03-PLAN.md — build_meta.py extension: ytd_subsidy_gbp, gbp_per_sec_rate (clawback-clamped), ytd_as_of, ytd_label_year; schema 1.1
- [ ] 01.1-04-PLAN.md — glossary.json slug-key migration + intermittent/dispatchable; captions.json card_hook fields; EDIT-05 lint extension
- [ ] 01.1-05-PLAN.md — pipeline/export_chart_images.py (dark matplotlib renderer) + wire into __main__.py with EXIT_IMAGE_EXPORT_FAILED
- [ ] 01.1-06-PLAN.md — src/client/shock-counter.js (rAF + reduce-motion) and src/client/glossary-tooltip.js (XSS-safe textContent rendering)
- [ ] 01.1-07-PLAN.md — src/index.md landing rewrite (hero + 4-card grid + footer); src/charts/scissors.md re-skin (dark Plot, Download Image, abbr terms)
- [ ] 01.1-08-PLAN.md — 3 placeholder detail pages (co2-avoided, cumulative-subsidy, generation-heatmap) with full editorial scaffolding + placeholder PNG download
- [ ] 01.1-09-PLAN.md — Wave 4 verification: clean full-build + full pytest/node/smoke suite + checkpoint:human-verify (visual UX confirmation)

### Phase 2: Methodology + Remaining Charts
**Goal**: The methodology page is live (gating CHART-02), and all four v1 charts are public — giving visitors the complete editorial picture of CfD cost, carbon efficiency, subsidy concentration, and intermittency
**Depends on**: Phase 1
**Requirements**: EDIT-03, CHART-02, CHART-03, CHART-04
**Success Criteria** (what must be TRUE):
  1. A visitor can navigate to the methodology page before CHART-02 (3d) is public and read the full derivation, assumptions, and data-source citations for the £/tCO₂ calculation — including the ETS price and DEFRA SCC overlay sources
  2. A visitor can use the £/tCO₂ avoided explorer (CHART-02 / 3d) to filter by allocation round, technology, and year, and see the UK ETS price and DEFRA social cost of carbon as reference overlays
  3. A visitor can explore the cumulative consumer subsidy chart (CHART-03 / 3b + 6a), view the stacked technology breakdown, and interact with the Lorenz curve scatter to see subsidy concentration
  4. A visitor can view the daily generation heatmap (CHART-04 / 2a) on a mobile device at narrower than 768px and see a readable simplified fallback (weekly or monthly grid) rather than an illegible full heatmap
**Plans**: 5 plans
**UI hint**: yes

Plans:
- [ ] 02-01: Methodology page (EDIT-03) — must complete before 02-02
- [ ] 02-02: CHART-02 (3d) £/tCO₂ chart-model builder, Framework page, ETS + DEFRA overlay constants
- [ ] 02-03: CHART-03 (3b + 6a) cumulative subsidy + Lorenz chart-model builder and Framework page
- [ ] 02-04: CHART-04 (2a) heatmap chart-model builder, Framework page, mobile fallback

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Pipeline + First Chart | 0/5 | Not started | - |
| 2. Methodology + Remaining Charts | 0/4 | Not started | - |
