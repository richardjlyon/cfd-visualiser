# Feature Research

**Domain:** Public-education data-journalism chart suite — UK CfD subsidy visualiser
**Researched:** 2026-04-14
**Confidence:** HIGH (peer site survey + verified patterns from OWID, Carbon Brief, Ember, Reuters Graphics, The Pudding)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that users assume exist in any credible data-journalism site. Missing any one of these causes credibility loss or immediate bounce. Noted against the specific chart types from `visualisation_scope.md` where the stakes are chart-type-specific.

| Feature | Why Expected | Complexity | When to Land | Chart-Type Notes |
|---------|--------------|------------|--------------|-----------------|
| **Mobile-responsive layout** | Every public site is consumed on phones; energy stories spike on social traffic from mobile | S | Phase 1 (v1 launch) | Heatmap (2a) is the hardest: a 365-column grid must reflow to a coarser monthly or weekly summary on narrow screens. Scissors chart (3c) and Lorenz (6a) survive well as SVG-scaled. Scatter (3e) needs touch-pan not hover. |
| **Plain-English one-line headline per chart** | Non-specialists skip charts without a declarative caption that names the point. This is the editorial thesis made concrete. | S | Phase 1 | All charts. Caption must name the defect, not describe the chart type ("CfD payments cost 3× the government's own carbon price in 2023", not "Bar chart of subsidy cost"). |
| **Visible data source citation per chart** | Journalists and analysts will not share or cite without a clear source. One bad chart with no citation destroys site credibility. | S | Phase 1 | All charts. Format: "Source: LCCC Actual CfD Generation dataset, [date retrieved]". External overlays (ETS price on 3d, DEFRA SCC) each need their own citation line. |
| **Fast first paint / minimal JS payload** | Public education traffic is high-bounce. Users on slow mobile connections abandon after ~3 seconds. Core vitals matter for search ranking too. | M | Phase 1 | Prefer server-rendered SVG or pre-built static charts for initial load; hydrate interactivity after. Heavy JS charting frameworks (Plotly full bundle = ~3MB) require aggressive code-splitting. |
| **Accessible colour ramps** | Colour-blind users (8% of men) must be able to read sequential and diverging scales. WCAG 3:1 for chart elements. | S | Phase 1 | Heatmap (2a): sequential single-hue (e.g., viridis or cividis). Scissors (3c): two-line diverging needs strong contrast on both lines. Lorenz (6a): equality diagonal vs curve needs accessible pair. Scatter (3e, 3b): use shape+colour not colour alone for tech categories. |
| **No-eyestrain palette / light-mode default** | Public-facing sites default light. Dark-mode optional. Low-contrast or saturated palettes cause fatigue in long reads. | S | Phase 1 | A single design-token palette (4-6 colours + sequential ramp) defined once and applied to all charts. |
| **"Last updated" timestamp per chart or page** | Daily-refresh dataset: users and journalists need to know the data is current. Stale data seen as broken. | S | Phase 1 | Display in footer of each chart: "Data through [date]. Updated daily." Pulls from build artefact, not a manually edited string. |
| **Static URL per chart (permalink)** | Journalists link to specific charts. Unstable URLs destroy shareability and incoming links. | S | Phase 1 | Each chart has its own `#chart-id` anchor or dedicated route. Navigable from the homepage chart index. |
| **Screenshot-shareable chart design** | Charts circulate on Twitter/X, Bluesky, LinkedIn without wrapper UI. Must be legible at ~1200×630 crop. | S | Phase 1 | Design charts with enough internal margin and font-size that they read without the surrounding prose. Pointed caption should be baked into the chart title area, not only the prose below. |
| **Source code / data reproducibility statement** | Analyst-grade audience will ask "how was this calculated?" A public GitHub repo with the pipeline is table stakes for credibility. | S | Phase 1 | Link from every page footer: "Pipeline code: [GitHub URL]". Separate from per-chart methodology (see Differentiators). |

---

### Differentiators (Competitive Advantage)

Features that set this site apart from a static chart dump or a generic dashboard. Chosen to reinforce the "pointed but sourced" editorial stance and serve the analyst secondary audience without burdening the primary public audience.

| Feature | Value Proposition | Complexity | When to Land | Chart-Type Notes |
|---------|-------------------|------------|--------------|-----------------|
| **Editorial annotation layer on charts** | Named callouts baked into the SVG ("2022: prices cross; CfDs briefly save consumers money", "Hinkley C: 35-year lock-in") make the point impossible to miss and survive screenshots. Core differentiator vs a neutral data explorer. | M | Phase 1 | Scissors (3c): annotate the 2022 cross and the re-opening. Scatter (3e): label Hinkley Point C and the Investment Contract cluster explicitly. Lorenz (6a): label the Gini coefficient and the "top 10 projects = X% of subsidy" reading. Heatmap (2a): annotate notable dunkelflaute events. |
| **Chart-as-deeplink with filtered state in URL** | A journalist can share `?round=AR1&year=2023` and the chart opens pre-filtered. Multiplies virality of pointed findings. | M | Phase 2 (after v1 stable) | Most valuable for 3d (round/technology/year explorer) and 3b/6a (project filter). Scissors (3c) benefits from zoom-range in URL. Heatmap (2a) lower priority — no filter state. |
| **Downloadable CSV per chart** | Analysts want to verify, extend, or incorporate data. OWID does this for every chart; it is standard for credibility at the analyst tier. Low cost, high trust signal. | S | Phase 1 | Each chart's underlying aggregated data (not raw LCCC dump) as a clean CSV. Button positioned below chart. Include column headers and units in CSV. |
| **Per-chart methodology note (collapsible)** | "How was £/tCO₂ avoided calculated?" is a reasonable question from an energy analyst. A one-paragraph explanation with formula, caveats, and source DOIs is sufficient. Collapsible so it doesn't interrupt public-first reading. | S | Phase 1 | Critical for 3d (£/tCO₂ avoided — divisor definition, what counts as "avoided"), 3c (which wholesale price series, spot vs forward), 6a (Lorenz: unit of analysis = project or allocation round?). Lower priority for 2a heatmap. |
| **Open Graph social-card images auto-generated per chart** | When a journalist shares a chart URL on social media, the preview shows the chart image with headline. Without this, the link preview is blank — kills click-through rate. Build-time generation via Playwright/Puppeteer screenshot is reliable on a static build. | M | Phase 1 or 2 | One OG image per chart page. Dimensions 1200×630. Include chart title and site name in image. Can be generated as part of daily rebuild. |
| **RSS/Atom feed of dataset updates** | Analysts and journalists can subscribe to be notified when new LCCC data arrives. Low implementation cost; strongly signals "live" data commitment. | S | Phase 2 | Single feed for the whole site. Entry per build that includes the date range newly added and a brief note on any anomalies detected. |
| **Scrollytelling narrative for the 3c scissors chart** | The scissors opening-and-closing is the site's most cinematic chart. A short scroll-driven narrative ("in 2022, lines crossed… but here's why that was temporary") would be the most powerful public-education moment. High effort, high reward. | L | Phase 2 or 3 | Only worthwhile for 3c. The Pudding's approach: pin the chart, use scroll to advance annotations. On mobile, fall back to static annotated chart — simpler and faster to code. |
| **"Compare rounds" toggle on 3d and 3a** | Lets users switch between allocation rounds to see how cost/tonne varies. Reinforces the editorial point that Investment Contracts are the cost millstone. | M | Phase 1 for basic, Phase 2 for full filter | 3d is the primary beneficiary. Also useful for 3a (£/MWh by round). |
| **"What does this mean?" plain-language aside per chart** | A 2–3 sentence boxout ("Why does this matter? CfD payments for offshore wind in AR1 cost more per tonne of CO₂ avoided than buying carbon credits directly on the ETS.") increases comprehension and shareability for the public audience. Distinguishes site from a neutral data portal. | S | Phase 1 | Can be static prose, no interactivity needed. Positioned prominently below chart headline and before methodology note. |
| **Site-level methodology / about page** | Explains the editorial thesis, what CfDs are, who the LCCC is, and why the data is trustworthy. Essential for first-time visitors who arrive via a social share. | S | Phase 1 | Static markdown page. One-time effort with occasional updates. Includes link to LCCC data portal, link to pipeline repo, and brief author bio. |
| **Dark mode** | Nice-to-have for late-night readers and system-preference users. Not urgent. | S | Phase 3 | Use CSS custom properties from the start (easy retrofit). Do not block launch on this. Sequential colour ramps need verified dark-mode variants. |

---

### Anti-Features (Deliberately NOT Build)

Features that are commonly requested or that seem natural but are wrong for this project's constraints, editorial voice, or audience.

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| **User accounts / login** | "Users could save their favourite charts or filter states" | Adds auth infrastructure, cost, GDPR complexity. Completely wrong for an anonymous public-education site. PROJECT.md explicitly out-of-scope. | Deeplink URLs serve the same function for analysts. No personal data needed. |
| **Comments section** | "Engagement and feedback" | Moderation overhead, troll and industry-lobby astroturfing risk. A pointed-but-sourced editorial site cannot afford to host unmoderated debate next to claims. | Contact email in footer. Public GitHub issues for data corrections. |
| **Cookie consent banner** | "Legal compliance" | Plausible/Fathom analytics are cookieless and PECR-compliant, eliminating the legal trigger for a banner. A banner on a public-education site signals surveillance and harms trust. | Use Plausible or Fathom. Confirm with legal review before launch. If any doubt, omit analytics entirely — a static build has server-log traffic data anyway. |
| **Heavy JS framework (React/Vue/Angular SPA)** | "Component reuse, interactivity" | A 3MB+ JS bundle for what is primarily a chart-reading experience is hostile to mobile users on slow connections. Initial page load is critical. | Python-generated static SVG/HTML with lightweight progressive enhancement. Observable Plot or Vega-Lite with selective hydration is sufficient for the interactivity needed. |
| **Splash animation / hero video** | "Polished, modern feel" | Delays time-to-first-chart. Public-education sites succeed through immediate credibility, not entertainment. | Strong typography, a clear headline chart, and a well-designed palette achieve polish without latency. |
| **Modal newsletter prompt** | "Build audience" | Interrupts first visit. Hostile to the pointed-editorial trust-building goal. | Opt-in email subscription in footer only. Or RSS, which serves the analyst audience better anyway. |
| **Paywall / premium tier** | "Revenue" | Incompatible with public education mission. Data is public (LCCC dataset). Any paywall would be indefensible. | Donation link in footer acceptable if needed. Open data, open pipeline. |
| **Real-time WebSocket data streaming** | "Live dashboard feel" | LCCC data is daily batch, not a live stream. Real-time infrastructure adds cost and complexity for zero benefit. | Daily rebuild via scheduled CI is the right cadence. |
| **External advertising / tracking pixels** | "Monetisation, analytics" | Third-party trackers (GA, Meta pixel) require cookie banners and are incompatible with the privacy-first stance. They also slow page load. | Cookieless first-party analytics (Plausible/Fathom) or none at all. |
| **Embedded third-party iframes (Datawrapper, Flourish)** | "Faster chart publishing" | Third-party embeds introduce GDPR liability, reduce site control, may change or disappear, and limit the custom annotation layer that is central to the editorial thesis. | Own the chart stack. Python-generated SVG with lightweight JS hydration is reproducible and fully controlled. |
| **Natural language query interface / LLM chatbot** | "AI-powered data exploration" | Engineering overhead, API cost, hallucination risk on factual energy data claims. A pointed editorial site should not have a plausible-sounding but possibly wrong chatbot. | Clear chart titles and methodology notes do the job. The "what does this mean?" boxout replaces the chatbot use-case. |

---

## Feature Dependencies

```
Mobile-responsive layout
    └──enables──> Screenshot-shareable chart design
    └──enables──> OG social cards (correct crop dimensions)

Source citation per chart
    └──is required for──> Downloadable CSV per chart (the CSV needs its own citation/README)
    └──is required for──> Per-chart methodology note (methodology references the same sources)
    └──is required for──> Site credibility with analyst audience

Editorial annotation layer
    └──requires──> Design token palette (annotations must be styled consistently)
    └──enhances──> Screenshot-shareable design (annotations survive the crop)
    └──enables──> Scrollytelling 3c (annotations become the scroll steps)

Static URL per chart
    └──enables──> Chart-as-deeplink with filter state (filter state extends the base permalink)
    └──enables──> OG social card (one card per stable URL)

Downloadable CSV per chart
    └──requires──> Build pipeline produces per-chart aggregated data artefact (not just charts)

"Last updated" timestamp
    └──requires──> Build pipeline exposes build date to template (trivial if CI-driven)

Per-chart methodology note
    └──requires──> Source citation per chart (methodology references sources)
    └──enables──> Analyst credibility gate (without this, analysts distrust the derived metrics)

OG social card images
    └──requires──> Static URL per chart
    └──requires──> Playwright/Puppeteer in build environment (or equivalent headless screenshot)

RSS/Atom feed
    └──requires──> Build pipeline produces feed artefact (structured list of rebuild events)

Chart-as-deeplink with filter state
    └──requires──> Static URL per chart
    └──requires──> Lightweight JS filter/toggle (small progressive enhancement, not full SPA)

Scrollytelling (3c)
    └──requires──> Annotated scissors chart (static version) exists first
    └──requires──> Intersection Observer / scroll library in build
    └──conflicts──> Heavy JS framework (must remain lightweight)
```

### Key Dependency Notes

- **Annotation layer must precede scrollytelling:** The scrollytelling version of 3c is just the static annotated chart animated by scroll. Build the static annotated chart in Phase 1; add scroll-drive in Phase 2 or 3 only if warranted.
- **CSV download is Phase 1, not deferred:** It is low complexity (S) and the analyst audience will ask for it immediately. Deferring it signals the site does not take reproducibility seriously.
- **OG images can be Phase 1 or 2:** Social sharing starts at launch. Auto-generated OG images significantly improve link-preview click-through. Worth attempting in Phase 1 if using a Python static-site generator (Playwright headless screenshot is straightforward in CI).
- **Deeplink filter state requires stable URL design decision upfront:** Choose URL scheme in Phase 1 even if filter state is not yet implemented, so Phase 2 can extend it without breaking existing links.

---

## Chart-Type Specific Feature Matrix

| Chart | Type | Mobile strategy | Key annotation | CSV download | Deeplink useful? | Methodology needed? |
|-------|------|----------------|----------------|--------------|-----------------|---------------------|
| **3c** Scissors | Time-series, two lines | Scales well; simplify to single-year zoom on narrow | Annotate 2022 cross, reopen | Yes (date, strike, wholesale) | Yes (zoom range) | Yes (which wholesale price series) |
| **3d** £/tCO₂ | Bar/scatter by round+year | Toggle rounds replaces side-by-side on mobile | Label ETS and DEFRA SCC reference lines | Yes (year, round, tech, £/t) | Yes (round+year+tech filters) | Critical (divisor, avoided GHG definition) |
| **3b/6a** Cumulative + Lorenz | Stacked area + Lorenz curve | Stack area legible narrow; Lorenz needs minimum ~300px width | Label Hinkley, offshore wind cluster; Gini value | Yes (project, cumulative £m) | Yes (filter by tech) | Yes (Lorenz: unit = project?) |
| **2a** Heatmap | Year × day-of-year grid | Collapse to month×year grid on mobile (<768px); add week selector | Annotate dunkelflaute weeks by year | Yes (date, MWh) | Low (no filter state needed) | Low |
| **3e** Bang-for-buck scatter | Scatter, one point per project | Reduce to top-N labeled; pan/zoom touch | Label Hinkley C, Investment Contract cluster | Yes (project, £m, tCO₂) | Yes (filter by round/tech) | Medium (tCO₂ definition) |
| **6b** Lock-in tail | Stacked bar by expiry year | Readable narrow; reduce stacks | Annotate Hinkley 2060 tail | Yes (year, project, £bn) | Low | Low |
| **7a** 2022 clawback | Monthly net + cumulative | Scales well | Annotate refund vs rising curve | Yes (month, net, cumulative) | Low | Low |

---

## MVP Definition

### Launch With (v1 — Phase 1)

The minimum feature set that makes the site credible to both public and analyst audiences from day one.

- [ ] Mobile-responsive layout — without this no public chart site is viable
- [ ] Plain-English headline per chart (editorial annotation at title level) — this is the thesis made concrete
- [ ] Source citation per chart — credibility is non-negotiable
- [ ] "Last updated" timestamp — daily-refresh site without a date stamp looks broken
- [ ] Accessible colour ramps — WCAG 3:1 for chart elements; use viridis/cividis for sequential, accessible pairs for diverging
- [ ] Fast first paint (static SVG or pre-rendered chart, JS progressive enhancement only) — mobile users will not wait
- [ ] Static URL / permalink per chart — journalists must be able to link to specific charts
- [ ] Screenshot-shareable chart design (headline + chart legible without prose) — social circulation starts at launch
- [ ] Downloadable CSV per chart — analysts expect this; low complexity
- [ ] Per-chart methodology note (collapsible, 1–2 paragraphs) — critical for 3d and 3c at minimum
- [ ] "What does this mean?" plain-language boxout per chart — differentiates from neutral data portal
- [ ] Site-level about / methodology page — required for first-time visitors from social shares
- [ ] Public GitHub repo link in footer — reproducibility signal

### Add After Validation (v1.x — Phase 2)

Add once Phase 1 is live and social sharing patterns are observable.

- [ ] Chart-as-deeplink with filter state in URL — add once usage shows analysts sharing filtered views
- [ ] OG social card images auto-generated per chart — if social sharing is happening but preview images are blank
- [ ] RSS/Atom feed — once there is evidence of repeat analyst visitors who want update notifications
- [ ] "Compare rounds" full filter on 3d and 3a — once basic version is validated

### Future Consideration (v2+)

Defer until Phase 1 value is proven or external data joins are complete.

- [ ] Scrollytelling narrative for 3c scissors — high effort, only worthwhile with evidence of engagement on that chart
- [ ] Dark mode — low urgency; use CSS custom properties from the start for easy retrofit
- [ ] Capacity-factor family (1a/1b/1c) interactive features — gated on CfD Register join (Phase 2 data work)
- [ ] Public API — PROJECT.md explicitly defers this; adds hosting cost and rate-limit concerns

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Mobile-responsive layout | HIGH | LOW–MEDIUM | P1 |
| Plain-English headline per chart | HIGH | LOW | P1 |
| Source citation per chart | HIGH | LOW | P1 |
| Last updated timestamp | HIGH | LOW | P1 |
| Accessible colour ramps | HIGH | LOW | P1 |
| Fast first paint | HIGH | MEDIUM | P1 |
| Static URL per chart | HIGH | LOW | P1 |
| Screenshot-shareable design | HIGH | LOW | P1 |
| Downloadable CSV per chart | MEDIUM–HIGH | LOW | P1 |
| Per-chart methodology note | HIGH (analysts) | LOW | P1 |
| What does this mean? boxout | HIGH (public) | LOW | P1 |
| About / methodology page | HIGH | LOW | P1 |
| Editorial annotation layer | HIGH | MEDIUM | P1 |
| OG social card images | MEDIUM | MEDIUM | P2 |
| Chart-as-deeplink with filter state | MEDIUM | MEDIUM | P2 |
| RSS/Atom feed | LOW–MEDIUM | LOW | P2 |
| Scrollytelling (3c only) | MEDIUM | HIGH | P3 |
| Dark mode | LOW | LOW (if CSS vars used) | P3 |

**Priority key:**
- P1: Must have for Phase 1 launch
- P2: Should have; add in Phase 2 when core is validated
- P3: Nice to have; future consideration

---

## Competitor Feature Analysis

| Feature | Our World in Data | Carbon Brief | Ember Climate | Reuters/FT Graphics | Our Approach |
|---------|-------------------|--------------|---------------|---------------------|--------------|
| Source citation | Per chart, prominent | Per article/chart | Per dataset download | Per graphic caption | Per chart, with retrieval date |
| Methodology | Per-chart collapsible + full explainer article | Linked methodology paper | Separate PDF document | Not always public | Collapsible per-chart note + about page |
| CSV download | Yes, per chart, multiple formats | Occasional | Yes, full dataset | Rarely | Yes, per chart, aggregated clean CSV |
| Deeplink / filter URL | Yes, full state in URL (OWID Grapher) | Partial | No | No | Phase 2; URL scheme decided in Phase 1 |
| Annotations | Limited (tooltip, no baked text) | Strong in long-form pieces | Minimal | Strong, editorial | Strong baked editorial annotations (core differentiator) |
| OG social cards | Yes | Yes | Yes | Yes | Phase 1 or 2 |
| Mobile | Responsive, some charts simplify | Responsive | Responsive | Responsive | Responsive, chart-type specific simplification |
| Analytics | GA (with consent) | GA (with consent) | GA | GA | Plausible/Fathom or none (no cookie banner) |
| Dark mode | No | No | No | Rare | Phase 3 |
| Scrollytelling | No (OWID) | Occasional | No | Frequent | Phase 3, 3c only |
| Newsletter / RSS | Newsletter | RSS + newsletter | Newsletter | No | RSS in footer, no modal prompt |

---

## Sources

- Our World in Data chart interface (direct inspection): https://ourworldindata.org/grapher/annual-co2-emissions-per-country
- The Pudding responsive scrollytelling guide: https://pudding.cool/process/responsive-scrollytelling/
- Datawrapper blog: https://www.datawrapper.de/blog/color-contrast-check-data-vis-wcag-apca
- Highcharts DataViz Accessibility guidelines: https://www.highcharts.com/blog/tutorials/10-guidelines-for-dataviz-accessibility/
- Smashing Magazine — Accessibility standards for chart visual design (2024): https://www.smashingmagazine.com/2024/02/accessibility-standards-empower-better-chart-visual-design/
- Plausible Analytics cookieless compliance: https://plausible.io/privacy-focused-web-analytics
- Ember Climate data explorer: https://ember-energy.org/data/electricity-data-explorer/
- Ofgem data portal (CSV download + citation pattern): https://www.ofgem.gov.uk/news-and-insight/data/data-portal
- Reuters Graphics GitHub (patterns): https://github.com/reuters-graphics
- GIJN data journalism toolkit: https://gijn.org/stories/a-data-journalism-experts-personal-toolkit/
- Vercel OG image generation (build-time screenshot approach): https://vercel.com/docs/og-image-generation
- Astro social card automation example: https://www.emgoto.com/astro-social-card/

---

*Feature research for: CfD Visualiser — public-education chart suite*
*Researched: 2026-04-14*
