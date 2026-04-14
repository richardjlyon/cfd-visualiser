# CfD Visualiser (working title)

## What This Is

A public-facing, daily-updated website that turns the UK Low Carbon Contracts Company (LCCC) *Actual CfD Generation and Avoided GHG Emissions* dataset into a family of crisp, attractive charts that expose the scale and nature of the subsidy cost associated with the UK Contract for Difference scheme. Primary audience is the general public, but charts must stand up to scrutiny from journalists and energy analysts. A public API is explicitly deferred to a later milestone.

## Core Value

A non-specialist can land on the site, look at a single chart, and walk away with an accurate, sourced understanding of what UK CfDs actually cost and deliver.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Daily automated ingest of the LCCC *Actual CfD Generation and Avoided GHG Emissions* dataset into a local database
- [ ] Public static website auto-rebuilt daily and hosted on a zero-to-low-cost static host (GitHub Pages / Cloudflare Pages / Netlify)
- [ ] "Pointed but sourced" editorial framing: every chart has a one-line caption naming the weakness it exposes, plus a visible data source citation
- [ ] Chart **3c**: Strike price vs wholesale price "scissors" time series (interactive: zoom + toggle allocation rounds)
- [ ] Chart **3d**: £/tCO₂ avoided explorer by round/technology/year, overlaid with UK ETS price and DEFRA social cost of carbon (interactive)
- [ ] Chart **3b + 6a**: Cumulative consumer subsidy (£bn) stacked by technology/project, with Lorenz curve of subsidy concentration (interactive scatter)
- [ ] Chart **2a**: Daily generation heatmap (year × day-of-year) for wind + solar CfD output
- [ ] Capacity factor explorer (1a–1c) as stretch/later goal once CfD Register join is done
- [ ] Reproducible daily rebuild pipeline (idempotent, safe to re-run)
- [ ] Visually coherent design system (typography, palette, chart styling) that reads as "modern, attractive, easy to interpret"

### Out of Scope (for v1)

- Public query/JSON API — deferred to a later milestone once the site proves the thesis
- Renewables Obligation Certificate (ROC) revenues — separate subsidy regime, not in this dataset
- Embedded benefits and network-charge avoidance — out of the CfD envelope
- Capacity Market payments to backup gas — different scheme
- Lifecycle emissions accounting (manufacture, decommissioning) — different project
- External-data charts (4a/4b cannibalisation, 5a curtailment) — deferred to a later milestone that adds Elexon/NESO joins
- User accounts, comments, or any form of login
- Paid hosting / anything with non-trivial running cost

## Context

**The dataset.** LCCC publishes a daily-refreshed spreadsheet of actual CfD generation and avoided GHG emissions at https://dp.lowcarboncontracts.uk/dataset/actual-cfd-generation-and-avoided-ghg-emissions. The existing repo contains a small prototype (`main.py`, `plot_cfd_cost.py`, `data/`) that already pulls and plots from this source — useful as scaffolding but not the final shape.

**The editorial thesis.** `visualisation_scope.md` catalogues 15+ charts, each framed around a specific defect in the CfD regime it is meant to expose (degradation curves, £/tCO₂ vs ETS, cannibalisation, curtailment, Lorenz concentration, lock-in tail, the 2022 clawback in context, etc.). v1 focuses on the four highest-payload, CSV-only charts; later milestones unlock capacity-factor and external-join families.

**The audience stance.** Public-first framing with analyst-grade rigour. Captions are pointed (name the weakness) but every number is sourced. Charts should be shareable as screenshots.

**The stack stance.** No hosting preference from the user — defer the concrete stack choice to the research phase. Likely shape: Python for ingest + static-site generation, a modern interactive-charting library (candidates: Plotly, Observable Plot, Vega-Lite), and a static host with a scheduled rebuild.

## Constraints

- **Budget**: Zero-to-minimal running cost — rules out paid servers/databases. Pushes toward static hosting + scheduled CI rebuild.
- **Data dependency**: Daily LCCC CSV is the authoritative primary source. If upstream format/URL changes, pipeline must fail loudly rather than silently serve stale data.
- **Accuracy**: Every chart must cite its source(s) and be reproducible from the committed data pipeline. Credibility loss from one bad chart is expensive and hard to repair.
- **Public-first UX**: Charts must be legible on mobile and intelligible without reading the prose. No jargon without a one-line gloss.
- **Prototype baggage**: Existing `main.py` / `plot_cfd_cost.py` are scaffolding, not a foundation — expect to rewrite rather than extend them where it makes sense.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Defer public API to later milestone | Focus v1 on site + charts; API adds hosting/cost/rate-limit concerns without proving the thesis | — Pending |
| v1 = four CSV-only charts (3c, 3d, 3b/6a, 2a) on a public URL | Maximum informational payload with zero external-data dependencies | — Pending |
| Pointed-but-sourced editorial voice | Balances public impact with analyst credibility | — Pending |
| Daily rebuild cadence | Matches LCCC's daily update; reinforces "live" public-education positioning | — Pending |
| Public-first audience with analyst-grade rigour | All three audiences served, but tradeoffs resolve in favour of the general reader | — Pending |
| Stack choice deferred to research phase | User has no preference; static-host + scheduled-rebuild direction confirmed but specific libraries TBD | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-14 after initialization*
