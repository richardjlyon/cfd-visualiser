# Pitfalls Research

**Domain:** Public-facing data-journalism static site — UK CfD renewables subsidies
**Researched:** 2026-04-14
**Confidence:** HIGH (domain-specific; verified against LCCC portal behaviour, GitHub Actions documented limits, WCAG standards, and energy-sector literature)

---

## Critical Pitfalls

### Pitfall 1: Silent Upstream Schema or URL Drift

**What goes wrong:**
The LCCC data portal has previously patched a pipeline bug where JSON resource IDs changed silently. Column names, date formats, or the CSV download URL could shift between portal releases without versioned notice. `pd.read_csv()` on an unexpected schema produces NaN columns that propagate silently through all derived charts — the site rebuilds successfully and looks fine, but every number is wrong.

**Why it happens:**
The ingest step treats a successful HTTP 200 + non-empty file as a success. It never validates the schema. By the time the chart looks wrong, multiple daily builds have baked in the corrupt data.

**How to avoid:**
- Define an explicit schema contract at ingest time: assert required column names, dtypes, and value ranges before any processing. Fail the build immediately with a descriptive error on contract violation.
- Pin the expected column list (e.g. `Settlement_Date`, `CfD_ID`, `CFD_Generation_MWh`, `CFD_Payments_GBP`, `Strike_Price_GBP_Per_MWh`, `Market_Reference_Price_GBP_Per_MWh`, `Avoided_GHG_tonnes_CO2e`) and assert at ingest.
- Sanity-check aggregate plausibility: total generation for any historical year should not deviate from the stored baseline by more than ±5 %. A sudden 50 % drop indicates either a schema shift or a partial fetch.
- Store the raw downloaded CSV with a datestamp in a `data/raw/` archive. If validation fails, the previous good file remains queryable.

**Warning signs:**
- Chart values change drastically overnight without a corresponding news event.
- Total generation or payment columns suddenly contain NaN or zero after a build.
- The LCCC portal changelog or news feed mentions a "data pipeline update" (they did this in 2024).

**Phase to address:** Phase 1 (ingest pipeline) — before any chart is built.

---

### Pitfall 2: GitHub Actions Cron Silently Stops Running

**What goes wrong:**
GitHub disables scheduled workflows on any public repository with no commit activity in the last 60 days. The last-updated stamp on the site freezes; the site serves stale data with no visible error. The solo maintainer may not notice for weeks.

**Why it happens:**
GitHub's documented anti-abuse policy. A data-journalism project that has stabilised (no new code commits) will hit this exactly when it should be running most reliably.

**How to avoid:**
- Add a "keepalive" workflow job that commits a trivial metadata touch (e.g. `data/last_build.txt`) or uses the GitHub API to create a repository dispatch event at least every 45 days.
- Use a dead-man's-switch service (Healthchecks.io free tier, or a simple HTTP ping to an uptime monitor) as the final step of every successful build. If the ping stops arriving within the expected window, alert fires.
- Alternatively, use Cloudflare Pages' built-in cron trigger (Workers Cron Triggers) rather than GitHub Actions — it has no inactivity kill switch.

**Warning signs:**
- GitHub Actions tab shows the scheduled workflow with the banner "This scheduled workflow is disabled because there hasn't been activity in this repository for at least 60 days."
- The site's "last updated" date stops advancing.
- No build entries in the Actions run history for >24 hours.

**Phase to address:** Phase 1 (pipeline) — wire the dead-man's switch from day one; do not treat it as optional hardening.

---

### Pitfall 3: Stale Data Served Behind CDN / Browser Cache

**What goes wrong:**
The daily rebuild produces new chart JSON and HTML. But Cloudflare Pages, Netlify, or a browser cache returns the previous day's assets for hours or days. The site's "last updated" date advances (it is baked into the HTML at build time) but the chart data does not match — a subtle and credibility-damaging inconsistency.

**Why it happens:**
Static hosts set long default cache TTLs on assets. Build-triggered deploy cache-busting works for the HTML entry point but not for chart data JSON files unless they are either content-addressed (hashed filenames) or the CDN is explicitly purged.

**How to avoid:**
- Use content-addressed filenames for chart data (e.g. `charts/scissors-{YYYYMMDD}.json` or a content hash) so that stale caches automatically miss on new content.
- Alternatively, set `Cache-Control: no-cache` on the specific chart data JSON files (both platforms allow per-path header overrides).
- Emit the build timestamp into a `meta.json` and have the chart page fetch it to confirm freshness before rendering data. If the timestamp is >25 hours old, show a "data may be delayed" banner.
- On Netlify: use `_headers` file; on Cloudflare Pages: use `_headers` file or a Pages Function.

**Warning signs:**
- "Last updated" in HTML says today; chart traces stop at yesterday or earlier.
- Hard-refresh shows different data than soft-refresh.
- CDN analytics show very low cache miss rates (< 1 %) after a deployment.

**Phase to address:** Phase 1 (static site hosting setup).

---

### Pitfall 4: Non-Idempotent Pipeline Producing Drift Over Re-Runs

**What goes wrong:**
Re-running the pipeline on the same day twice produces different chart outputs. This happens if the pipeline appends to a database rather than upserts, if it writes timestamp-tagged rows without deduplication, or if any step involves `sort=False` on a DataFrame that is ordered by insertion time rather than a stable key.

**Why it happens:**
The LCCC CSV does not appear to guarantee row ordering (the sample data shows rows from 2020, 2022, and 2025 interleaved). If the ingest appends without checking for existing `(Settlement_Date, CfD_ID)` pairs, re-runs or partial retries create duplicate rows that inflate aggregates.

**How to avoid:**
- Design the ingest as an upsert keyed on `(Settlement_Date, CfD_ID)`, not an append.
- After ingest, assert that `df.groupby(['Settlement_Date','CfD_ID']).size().max() == 1`.
- Store the derived chart data files (JSON/Parquet) under version control (git LFS or a side-branch) so that re-runs can be diffed to confirm idempotency.
- Run the pipeline twice in CI on a scheduled basis and diff outputs; fail if they diverge.

**Warning signs:**
- Total payment figures for a historical year increase monotonically across daily builds with no upstream change.
- `groupby().sum()` on `CFD_Payments_GBP` for a closed year produces a different value week-over-week.

**Phase to address:** Phase 1 (ingest / data model design).

---

### Pitfall 5: Timezone and Date-Boundary Bugs (UTC vs. BST)

**What goes wrong:**
The LCCC CSV `Settlement_Date` field (observed format: `2020-05-23 00:00:00.0000000`) is ambiguous — it has no timezone indicator. In spring/summer, UK settlement is in BST (UTC+1). A midnight settlement date in BST parsed as UTC is off by one day. Aggregations by month or by calendar year can then miscount generation at year/month boundaries.

**Why it happens:**
`pd.to_datetime()` defaults to naive (no timezone). Nothing breaks visibly. But in March/October the DST transition creates a 23- or 25-hour day in settlement terms. Any capacity-factor denominator that uses "hours in month" based on UTC calendar will be ±1 hour wrong on those months.

**How to avoid:**
- Treat `Settlement_Date` as representing a UK settlement day in clock time (Europe/London). Apply `tz_localize('Europe/London', ambiguous='infer')` or at minimum store as a date-only value with a documented convention.
- When computing "hours in month" for capacity-factor denominators, use the actual number of hours in that calendar month in the Europe/London timezone (not UTC). In October this is 745 hours, not 744.
- Write explicit unit tests: assert that the total row count for October 2023 matches the known LCCC publication, and that the BST-transition day has the expected number of half-hour settlement periods.
- Document the assumed timezone convention visibly in the methodology page.

**Warning signs:**
- Monthly generation totals for March and October are slightly off compared to LCCC published totals.
- Capacity factors for October are marginally higher than expected (25-hour day treated as 24).

**Phase to address:** Phase 1 (ingest) and Phase 2 (capacity factor calculations). Timezone convention must be locked before capacity factor work begins.

---

### Pitfall 6: Unit Confusion (MWh/GWh/TWh, £/£m/£bn, tCO₂/tCO₂e)

**What goes wrong:**
The raw CSV uses MWh for generation, GBP (not £m) for payments, and tonnes CO₂e for emissions. Chart 3b labels its y-axis "£bn" but the computation divides by 1e6 (£m) instead of 1e9, producing figures 1000× too large. Or a subsidy-per-tonne chart uses `Avoided_GHG_tonnes_CO2e` in some cells and multiplies by a factor assuming tCO₂ (not tCO₂e), introducing a ~5 % systematic error for non-CO₂ GHGs.

**Why it happens:**
Unit conversion is done inline in plotting code without named constants or intermediate validation. The prototype `plot_cfd_cost.py` already shows `/ 1e6` and `/ 1e9` scattered through the code with no named constant or assertion.

**How to avoid:**
- Define named constants for all unit conversions: `MWH_TO_GWH = 1e3`, `GBP_TO_GBP_BN = 1e9`, etc.
- After computing any headline aggregate, assert it against a known published figure. LCCC has published total payments of approximately £13bn through 2025 — use this as a sanity check fixture.
- Distinguish `CO2` from `CO2e` in variable names: `avoided_tonnes_co2e` not `carbon`.
- Add a units annotation to every chart axis label and to every tooltip (e.g. "£/tCO₂e" not just "£/t").

**Warning signs:**
- The cumulative subsidy chart (3b) shows a number outside the plausible range of £10–20bn for the 2017–2025 period.
- The £/tCO₂ avoided chart (3d) shows values below £5 or above £10,000 for any technology.
- A reviewer flags that the "£bn" label doesn't match the axis scale.

**Phase to address:** Phase 1 (all computation code). Establish a unit-testing discipline with known-good fixtures before any chart is considered done.

---

### Pitfall 7: Capacity-Factor Denominator Error

**What goes wrong:**
Chart 1a requires `CF = generation_MWh / (capacity_MW × hours_in_month)`. The `capacity_MW` comes from the CfD Register, which records *nameplate* (installed) capacity at a point in time. If a farm is commissioned mid-month, using full-month hours inflates the denominator and understates CF. If the register is fetched once and cached, farms that uprate (or partially decommission) will have wrong CFs for their full history.

**Why it happens:**
The CfD Register and the Actuals dataset have different update cadences and different granularity. The join is easy to get right for fully operational farms but subtly wrong for partial months.

**How to avoid:**
- For commissioning-month rows, pro-rate the denominator: `(days_remaining_in_month / days_in_month) × capacity_MW × hours_in_month`.
- Validate: any single farm CF > 65 % sustained over multiple months is implausible for offshore wind; flag as a data quality warning rather than presenting it.
- Keep the capacity join versioned: if the CfD Register changes a farm's capacity figure, the historical CF series should update consistently, and the change should be logged.
- Note the denominator convention explicitly on the methodology page (nameplate at commissioning, no uprate adjustments unless new evidence).

**Warning signs:**
- A farm shows CF > 70 % for its commissioning month.
- The fleet-average CF for offshore wind deviates materially from the published industry benchmark (~40–45 %).

**Phase to address:** Phase 2 (CfD Register join / capacity factor calculations).

---

### Pitfall 8: Double-Counting Across Allocation Rounds and Contract Types

**What goes wrong:**
The LCCC dataset includes both Investment Contracts (pre-CfD legacy, long-duration) and CfD Allocation Round contracts in the same file. The `Allocation_round` field distinguishes them, but any "total CfD subsidy" aggregate that sums all rows double-counts nothing — it is correct. However, chart 3a separates lines by round and adds an "Investment Contracts" line. If the denominator for "average £/MWh" uses fleet-total generation in the denominator but only AR1 payments in the numerator, the per-MWh subsidy appears artificially low for AR1. Similarly, chart 3d's "£/tCO₂ avoided" uses `Avoided_GHG_Cost_GBP` — ensure this column is not a duplication of `CFD_Payments_GBP` under a different accounting convention for some contract types.

**How to avoid:**
- Inspect the `Reference_Type` column: the sample data shows "IMRP". Document what other values exist and whether they affect payment calculation.
- For per-round averages, always filter both numerator and denominator to the same subset.
- Check whether Investment Contracts appear in `Allocation_round` as a distinct value or as a separate `Reference_Type`. The prototype code uses `df["Allocation_round"].isin(["Allocation Round 4", "Allocation Round 5"])` — verify this excludes Investment Contracts by inspection of the full unique value list.
- Write an assertion: `sum(all rounds) == grand total`. If it fails, a contract type is being missed or double-counted.

**Warning signs:**
- The sum of per-round totals does not match the grand total from the flat aggregate.
- The subsidy per MWh for a round is implausibly low compared to its strike price.

**Phase to address:** Phase 1 (data model) and Phase 2 (all multi-series charts).

---

### Pitfall 9: Chart Library Footguns on Mobile

**What goes wrong:**
Hover-only tooltips (Plotly's default mode, Observable Plot's `title` mark) are inaccessible on mobile touch screens. A user tapping a data point on the scissors chart (3c) gets no value readout. Small tap targets on a dense time series (daily generation heatmap, chart 2a) make the chart unusable on a phone.

**Why it happens:**
Interactive charts are designed on desktop. Mobile testing is skipped or deferred. Plotly's unified hover mode works well on desktop but produces overflow on small viewports. Observable Plot's `tip` mark requires explicit pointer support.

**How to avoid:**
- For Plotly: configure `hovermode='x unified'` with explicit `hoverlabel` max-width, and test on a 375px viewport. Consider providing a `tap-to-show-tooltip` fallback for mobile.
- For all interactive charts: test on actual iOS Safari and Chrome Android, not just browser devtools responsive mode (they differ in touch event handling).
- For the heatmap (2a): consider static SVG with a colour legend rather than interactive hover, or use a click-to-inspect pattern rather than hover.
- Set a minimum tap target of 44×44px (Apple HIG) / 48×48dp (Material) for interactive chart elements.
- Include a plain-text data table below or adjacent to each interactive chart as a fallback.

**Warning signs:**
- Chart renders correctly on desktop but no tooltip appears when tapping on mobile.
- Plotly legend overflows the chart container on a 375px viewport.
- A chart's interactive elements are smaller than a fingernail.

**Phase to address:** Phase 1 (design system and chart library selection). Establish mobile-first defaults before any chart is built.

---

### Pitfall 10: Accessibility Failures (Colour-Only Encoding, Missing Alt Text)

**What goes wrong:**
The scissors chart (3c) uses two lines distinguished only by colour. The Lorenz curve uses a diagonal reference line against a coloured area. For the ~8 % of male readers with red-green colour blindness, these charts convey no information. SVG charts without `<title>` and `<desc>` elements fail WCAG 2.1 SC 1.1.1 (non-text content) and will not be cited by any accessibility-conscious publisher.

**How to avoid:**
- Encode difference with both colour and line style (solid vs. dashed) at minimum. For multi-series charts, use colour-blind-safe palettes (Okabe-Ito is the standard for scientific use).
- Every SVG chart element must carry a meaningful `aria-label` or a `<title>` child element. For Plotly: use `fig.update_layout(title=...)` and ensure the surrounding `<div>` has an `aria-label`. For Observable Plot: wrap in a `<figure>` with a `<figcaption>`.
- Write a one-sentence text description of each chart's key finding adjacent to the chart (not as alt text — as visible prose). This serves both accessibility and the editorial mission.
- Use a contrast checker: all axis labels, tick marks, and chart annotations must meet WCAG AA (4.5:1 for text, 3:1 for graphical elements against background).
- Minimum: run axe DevTools or Lighthouse accessibility audit before any chart goes to production.

**Warning signs:**
- A Lighthouse accessibility score below 90 on any chart page.
- The chart passes visual review but uses red and green as the only differentiators.
- No `<title>` element inside SVG output.

**Phase to address:** Phase 1 (design system). Palette and encoding standards must be set before first chart ships.

---

### Pitfall 11: Build-Time Blowup and Chart JSON Bloat

**What goes wrong:**
The daily generation heatmap (2a) covers ~3,000 days × hundreds of CfD units. If rendered as a Plotly chart with full per-cell hover data embedded in the page as JSON, the page weight can exceed 5–10 MB. On Cloudflare Pages free tier, build time has a 20-minute limit; on Netlify, 300 build minutes/month is the free allowance. A Python pipeline that re-processes the full historical dataset on every daily build will hit these limits as the dataset grows.

**How to avoid:**
- Pre-aggregate: the heatmap only needs daily totals (not per-unit), so aggregate to a ~3,000-row daily total DataFrame before rendering. Do not embed per-unit data in chart JSON.
- Use incremental builds: maintain a processed `data/processed/daily_totals.parquet` that is cached in the repo or in GitHub Actions cache. Each daily build only processes the new rows appended since the last run.
- For Plotly, use `fig.write_json()` to externalise chart data as a separate `.json` file loaded lazily rather than inlining it in the HTML.
- Measure: `du -sh` the chart JSON files before committing. Set a budget: no single chart's data file should exceed 500 KB.

**Warning signs:**
- Build time exceeds 5 minutes on a dataset that should process in under 1 minute.
- Page load weight exceeds 2 MB on any chart page.
- Netlify build minutes approaching 200/month limit.

**Phase to address:** Phase 1 (pipeline architecture). Incremental processing must be designed in from the start, not retrofitted.

---

## Editorial / Credibility Pitfalls

### Pitfall 12: Overreach on a Single Chart That Hands Critics an Easy Rebuttal

**What goes wrong:**
Chart 3d (£/tCO₂ avoided) is described in `visualisation_scope.md` as "among the most damning single charts in the suite." If the methodology for `tCO₂ avoided` conflates CO₂ with CO₂e, uses a marginal abatement assumption rather than displacement accounting, or overlays a disputed ETS price, a critic can invalidate the entire chart with one methodological objection — and by association, cast doubt on the site.

**How to avoid:**
- Use the LCCC's own `Avoided_GHG_tonnes_CO2e` figure as the denominator without modification, and cite it as such. Do not apply your own displacement calculation — that is an analytical claim requiring peer review.
- State the assumptions: the LCCC `Avoided_GHG_Cost_GBP` column uses a published counterfactual carbon intensity; link to the LCCC methodology document.
- For the ETS overlay: use the actual published UK ETS auction clearing price series (available from GOV.UK) rather than a spot price estimate. Display it as a range or confidence band, not a single line, to reflect volatility.
- For the DEFRA social cost of carbon: use the official published trajectory values (GOV.UK carbon valuation collection) and link directly. Note it is a policy value, not a market price, and that methodological disputes exist.
- Separate the factual claim ("CfD payments per tonne of CO₂e avoided, using LCCC's own figures") from the editorial comment ("this is more expensive than the government's own carbon valuation"). Do not conflate them in the chart title.

**Warning signs:**
- The methodology page does not exist or does not explain the counterfactual assumption.
- The chart title contains a causal or evaluative claim that is not separately supported.
- The ETS/DEFRA overlay values are hardcoded rather than sourced from a published series with a citation.

**Phase to address:** Phase 1 (chart 3d specifically). This chart should not ship without a methodology page.

---

### Pitfall 13: Framing That Reads as Polemical Rather Than Pointed

**What goes wrong:**
The editorial thesis is "pointed but sourced." If captions use evaluative language ("waste," "millstone," "scandal") without immediately sourcing the claim, journalists will not quote the site and analysts will dismiss it. The target audience — general public — is also lost if they feel they are being lectured rather than informed.

**Why it happens:**
The editorial voice is set in the project description ("expose the scale and nature of waste"). That word "waste" appears in `project-description.md`. If it migrates unchanged into chart captions, the site positions itself as advocacy rather than analysis.

**How to avoid:**
- Distinguish three layers: (1) the data (sourced, neutral); (2) the implied inference (labelled as such: "This suggests…"); (3) editorial context (kept in prose paragraphs, not chart captions).
- Test each chart caption against the standard: "Is this claim falsifiable from the data shown?" If not, it is editorial comment, not a chart caption.
- Use "consumers paid £X more per MWh than the wholesale price" rather than "£X was wasted per MWh."
- Have one non-believer read each caption before publishing. A friendly sceptic catching a loaded word is cheaper than a hostile tweet going viral.

**Warning signs:**
- A caption contains a verb like "waste," "hidden," "scandal," "broken," or "failure" that is not directly supported by a number shown in the chart.
- The methodology page does not exist when a contested chart ships.

**Phase to address:** Every phase that ships a chart. Establish a caption review checklist.

---

### Pitfall 14: Missing or Thin Methodology Page

**What goes wrong:**
An energy analyst lands on the site, sees an interesting £/tCO₂ figure, wants to reproduce it, finds no methodology page, and either (a) cannot cite the site or (b) writes a dismissive thread about "unclear methodology." Academic and policy citations require reproducibility. A missing methodology page is the single most common reason data journalism sites are not cited by analysts.

**How to avoid:**
- Publish a methodology page before the first chart ships. At minimum: data source with URL and version, any transformations applied, unit conventions, what `Avoided_GHG_Cost_GBP` means and where it comes from, the ETS/DEFRA values used and their provenance.
- Include a link to the raw data download on every chart page.
- Version the methodology: if the calculation changes, the old version should remain accessible or the change should be documented with a date.
- Link to the LCCC methodology document for `Avoided_GHG_Cost_GBP` rather than paraphrasing it.

**Warning signs:**
- There is no `/methodology` or `/about-the-data` page in the site structure.
- The chart footnote says "Source: LCCC" but does not link to the specific dataset URL.
- There is no explanation of how `Avoided_GHG_Cost_GBP` is calculated in the raw data.

**Phase to address:** Phase 1. The methodology page must be live before any chart is indexed.

---

### Pitfall 15: No Data Versioning — Chart Changes Without Explanation

**What goes wrong:**
A reader bookmarks the scissors chart (3c) and returns a month later to find the values have changed — LCCC retrospectively corrected historical data, and the pipeline picked up the correction silently. The reader assumes the site is manipulating numbers. This is a near-certain occurrence: LCCC has previously patched pipeline issues that affected published data.

**How to avoid:**
- Archive the raw CSV with a datestamp in a `data/raw/YYYY-MM-DD/` directory, committed to git (or git LFS for large files). This creates an auditable history of what the upstream source said on each date.
- When a historical revision is detected (an already-processed date's aggregate changes by more than a noise threshold), log it visibly: "LCCC revised data for [month]: [old value] → [new value]. Updated [date]."
- Display a "data as of [date]" stamp on each chart that links to the methodology page's revision log.

**Warning signs:**
- A re-run of the pipeline on historical data produces different output than the previously committed chart data.
- No raw archive of the CSV exists.
- There is no changelog on the site.

**Phase to address:** Phase 1 (pipeline) — archive strategy must be built in from the first ingest.

---

### Pitfall 16: Disputed Overlay Values Without Provenance (ETS, Social Cost of Carbon)

**What goes wrong:**
Chart 3d overlays the UK ETS price and DEFRA social cost of carbon against the CfD £/tCO₂ figure. The ETS price is volatile (£35–80/t range cited in scope). The DEFRA value (~£280/t) is from the Green Book carbon valuation and is methodologically contested (it uses a MAC approach calibrated to UK net-zero targets, not a damage-function SCC). If a critic successfully challenges the overlay value, the chart's key comparison is invalidated.

**How to avoid:**
- Source the ETS price from the official UK ETS authority auction results (GOV.UK), not a news article. Use the calendar-year average clearing price with error bars representing the range.
- For the DEFRA value: use the official "central estimate" from the GOV.UK carbon valuation publication, cite the specific document URL and year of publication, and note on the methodology page that this is a policy valuation used for HM Treasury Green Book appraisal, with a reference to the methodological debate.
- Do not use the "social cost of carbon" framing unless you are using the DEFRA figure specifically. The US EPA SCC (~$185/t in 2023) is a different methodology and jurisdiction.
- Display the overlays as dashed reference lines with explicit labels (e.g. "UK ETS 2024 avg: £47/t") and a hover/tooltip that links to the source.

**Warning signs:**
- The overlay values are hardcoded in the plotting script rather than loaded from a sourced data file.
- The chart legend says "social cost of carbon" without specifying which methodology or year.
- The ETS overlay is a single fixed value rather than a time series.

**Phase to address:** Phase 1 (chart 3d). This is the highest-stakes chart and its overlays must be sourced before launch.

---

### Pitfall 17: Cannibalisation Charts That Imply Causation

**What goes wrong:**
Charts 4a and 4b show the negative correlation between wind output and wholesale price — the classic cannibalisation story. If the caption says "high wind causes lower prices" without qualification, a technically literate critic correctly notes that demand variation, gas prices, and interconnector flows are confounders, and that recent causal ML research has complicated the simple narrative. The chart then becomes an example of journalistic overreach rather than rigorous analysis.

**Why it happens:**
The correlation is real and strong. It is tempting to state the causal direction directly. The causal inference literature on this topic is genuinely contested: some papers find robust causal effects; others find the correlation is confounded by demand timing.

**How to avoid:**
- Caption the chart as: "When wind output is high, wholesale prices tend to be lower. This correlation is consistent with the cannibalisation hypothesis. Causation is contested in the academic literature — [link to note]."
- Link to at least one sceptical source (e.g. Energy Monitor's "Why reports of renewables price cannibalisation may be greatly exaggerated") alongside the supporting sources.
- Defer chart 4a/4b to a milestone that can include proper caveats — the scope already defers these to Phase 3, which is the right call.

**Warning signs:**
- The caption uses the words "causes" or "drives" rather than "correlates with" or "is associated with."
- There is no acknowledgement of confounders.

**Phase to address:** Phase 3 (Elexon joins). Build the causal caveat into the chart specification from the start.

---

### Pitfall 18: No Raw Data Download — Readers Cannot Verify

**What goes wrong:**
Public-education data journalism that does not offer a data download is vulnerable to the accusation "I can't check your numbers." Analysts will not cite a site that does not provide access to the underlying data. This is now a baseline expectation of the genre.

**How to avoid:**
- Provide a clearly labelled link to the LCCC source dataset on every chart page.
- Provide the processed/aggregated dataset used for each chart as a downloadable CSV (e.g. the yearly aggregates used for the scissors chart). This is low-cost (a few KB) and high-credibility.
- The public API is explicitly deferred in PROJECT.md — but a static CSV download is not an API and requires no server.

**Warning signs:**
- No "Download data" or "Source" link is visible on any chart page.
- A reader cannot get from a chart to the underlying data without leaving the site.

**Phase to address:** Phase 1. Every chart page should ship with a data source link and a processed-data download.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode ETS/DEFRA overlay values as constants in plotting code | Fast to implement | Values become stale; provenance is lost; changing them is invisible | Never — source them from a data file from day one |
| `pd.read_csv()` without schema validation | Pipeline "just works" | Silent corruption on any schema change | Never — add column assertions at ingest |
| Inline all chart data in HTML as JSON | Simple build | Page weight blows up; 5–10 MB pages; slow mobile load | Only acceptable for charts with <500 rows of data |
| Skip methodology page for v1 launch | Ship faster | Analysts won't cite the site; credibility window closes quickly | Never — a stub methodology page takes 2 hours |
| GitHub Actions cron without a dead-man's switch | Simple pipeline | Silent stale data after 60 days of no commits | Never — the entire value proposition is "daily updates" |
| `append` to database/CSV on ingest (no upsert) | Trivial code | Duplicate rows on re-run inflate all aggregates | Never for a pipeline that may be re-run |
| Single `main.py` for ingest + transform + plot | Fast prototyping | Impossible to test transforms independently; no incremental builds | Only acceptable in prototype; rewrite before Phase 1 |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LCCC data portal | Assume the direct CSV download URL is stable; hardcode it | Check the CKAN API endpoint (`/api/3/action/resource_show?id=...`) to resolve the current download URL programmatically; cache the resolved URL with a TTL |
| LCCC data portal | Assume a 200 response means valid data | Validate schema, row count (>0), and aggregate plausibility after every fetch |
| GitHub Actions cron | Assume daily schedule runs reliably on inactive repos | Add a keepalive commit or use a dead-man's switch service |
| Cloudflare Pages free tier | Assume unlimited build time | Builds time out at 20 minutes; incremental processing is mandatory as data grows |
| Netlify free tier | Assume unlimited build minutes | 300 min/month; a 5-minute daily build consumes 150 min/month — leaves margin, but a slow pipeline will exhaust it |
| Elexon / NESO APIs (Phase 3) | Assume stable endpoint and schema | Both APIs have changed endpoints and data formats multiple times; pin to versioned API endpoints and validate schema at every ingest |
| UK ETS price data | Use a news article or Wikipedia figure | Use GOV.UK official auction clearing price results; store as a time series, not a scalar |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-processing full historical CSV on every build | Build takes 5+ minutes; hits free-tier limits | Incremental: cache processed Parquet, process only new rows | Once dataset exceeds ~50k rows (~2 years at current volume) |
| Embedding full per-unit daily data in chart JSON | Page weight >5 MB; slow mobile; Lighthouse performance <50 | Pre-aggregate to the granularity the chart actually needs | Heatmap chart with per-unit data: immediate; daily totals: fine |
| Plotly `fig.to_html(include_plotlyjs=True)` | Each chart page embeds a 3 MB Plotly bundle | Use CDN reference for Plotly.js; serve it once per page session | Immediately on a multi-chart page |
| Loading all charts on a single page | First contentful paint >3 s | Lazy-load chart data (fetch JSON on scroll-into-view) | Once there are 4+ charts on the same page |

---

## "Looks Done But Isn't" Checklist

- [ ] **Ingest pipeline:** Runs without error — but has no schema assertion. Verify column names are checked at runtime.
- [ ] **"Last updated" stamp:** Shows today's date — but CDN is serving yesterday's chart data. Verify with a hard-refresh from an incognito window on a fresh CDN edge.
- [ ] **Subsidy total:** Matches a published LCCC figure — but check it also matches after a re-run (idempotency test).
- [ ] **Chart 3d:** Shows a £/tCO₂ figure — but check the ETS and DEFRA overlays are sourced from published data files, not hardcoded.
- [ ] **Methodology page:** Exists as a placeholder — but check it explains the `Avoided_GHG_Cost_GBP` calculation, not just names the data source.
- [ ] **Mobile:** Renders on desktop — but check on a 375px viewport with touch events (real device or BrowserStack, not devtools).
- [ ] **Accessibility:** Looks fine visually — but run axe DevTools; check all SVG charts have `<title>` elements and all colour encodings have a secondary visual differentiator.
- [ ] **Data download:** "Source: LCCC" link is present — but check it links to the specific dataset page, not just the LCCC homepage.
- [ ] **Cron job:** Workflow is enabled — but check the repository has had a commit in the last 30 days, or a keepalive is wired.
- [ ] **Cannibalisation charts (Phase 3):** Correlation is plotted — but check captions do not use causal language without qualification.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Silent schema corruption served for N days | HIGH | Roll back to last good archived CSV; re-run pipeline from archive; add schema validation; publish a corrections notice |
| GitHub Actions cron silently stopped | LOW | Re-enable workflow; trigger manual run; add keepalive; no user-facing impact if caught within 1-2 days |
| CDN serving stale data | LOW | Trigger cache purge via host CLI; add `Cache-Control: no-cache` to chart JSON files; verify with incognito hard-refresh |
| Duplicate rows from non-idempotent ingest | MEDIUM | Deduplicate database on `(Settlement_Date, CfD_ID)`; re-derive all chart aggregates; test idempotency before re-deploying |
| Credibility challenge to methodology | HIGH | Publish a methodological response immediately; if wrong, publish a correction and update methodology page with version history; if right, link the challenge and explain why the methodology is sound |
| Polemical caption goes viral negatively | HIGH | Edit caption immediately; publish a brief explanation of the change; the git history is an auditable record of the original and the correction |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Silent upstream schema drift | Phase 1 (ingest) | Schema assertion tests pass in CI; build fails on unknown columns |
| GitHub Actions cron stops | Phase 1 (pipeline) | Dead-man's switch fires within 25 hours of a missed build |
| CDN serves stale data | Phase 1 (hosting setup) | Hard-refresh from fresh CDN edge shows same data as origin |
| Non-idempotent pipeline | Phase 1 (data model) | Two sequential runs on same input produce bit-identical output |
| Timezone/date-boundary bugs | Phase 1 (ingest) then Phase 2 | October/March monthly totals match LCCC published figures |
| Unit confusion | Phase 1 (computation) | Known-good fixture: total payments 2017–2025 ≈ £13bn |
| Capacity-factor denominator | Phase 2 (CF calculations) | Commissioning-month CFs are not outliers; fleet average ≈ 40–45 % offshore |
| Double-counting across rounds | Phase 1 (data model) then Phase 2 | Sum of per-round totals == grand total |
| Mobile chart footguns | Phase 1 (chart library setup) | Real-device test at 375px; tooltips accessible by tap |
| Accessibility failures | Phase 1 (design system) | axe DevTools score ≥ 95 on every chart page |
| Build-time blowup / JSON bloat | Phase 1 (pipeline architecture) | Build completes in <3 minutes; no chart JSON >500 KB |
| Chart 3d overreach | Phase 1 (chart 3d) | Methodology page live before chart launches; ETS/DEFRA values sourced from data files |
| Polemical captions | Every chart phase | Caption review checklist applied; no evaluative language unsupported by data shown |
| Missing methodology page | Phase 1 | Methodology page live at `/methodology` before any chart is indexed |
| No data versioning | Phase 1 (pipeline) | Raw CSV archived with datestamp on every ingest run |
| Disputed overlay values | Phase 1 (chart 3d) | ETS series loaded from a versioned GOV.UK source file; DEFRA value has a direct URL citation |
| Cannibalisation causation conflation | Phase 3 (Elexon charts) | Caption uses "correlates with" not "causes"; sceptical source linked |
| No raw data download | Phase 1 | Every chart page has a source link and processed CSV download |

---

## Sources

- LCCC Data Portal: [https://dp.lowcarboncontracts.uk/](https://dp.lowcarboncontracts.uk/) — confirmed JSON resource ID was changed in a past pipeline fix
- LCCC news on portal launch: [https://www.lowcarboncontracts.uk/news/lccc-launches-new-data-portal-to-increase-availability-and-accessibility-of-uk-energy-data/](https://www.lowcarboncontracts.uk/news/lccc-launches-new-data-portal-to-increase-availability-and-accessibility-of-uk-energy-data/)
- GitHub Actions scheduled workflow disabling: [https://github.com/orgs/community/discussions/86087](https://github.com/orgs/community/discussions/86087)
- GitHub Actions keepalive: [https://github.com/marketplace/actions/keepalive-workflow](https://github.com/marketplace/actions/keepalive-workflow)
- Cloudflare Pages limits: [https://developers.cloudflare.com/pages/platform/limits/](https://developers.cloudflare.com/pages/platform/limits/)
- Netlify free tier: [https://www.netlify.com/guides/cloudflare-pages-vs-netlify/](https://www.netlify.com/guides/cloudflare-pages-vs-netlify/)
- UK ETS information: [https://en.wikipedia.org/wiki/UK_Emissions_Trading_Scheme](https://en.wikipedia.org/wiki/UK_Emissions_Trading_Scheme)
- DEFRA carbon valuation: [https://www.gov.uk/government/collections/carbon-valuation--2](https://www.gov.uk/government/collections/carbon-valuation--2)
- Carbon valuation methodology: [https://www.gov.uk/government/publications/valuing-greenhouse-gas-emissions-in-policy-appraisal/valuation-of-greenhouse-gas-emissions-for-policy-appraisal-and-evaluation](https://www.gov.uk/government/publications/valuing-greenhouse-gas-emissions-in-policy-appraisal/valuation-of-greenhouse-gas-emissions-for-policy-appraisal-and-evaluation)
- Cannibalisation effect (California): [https://www.sciencedirect.com/science/article/pii/S0140988319303470](https://www.sciencedirect.com/science/article/pii/S0140988319303470)
- Causal ML and renewables price: [https://arxiv.org/html/2501.10423v1](https://arxiv.org/html/2501.10423v1)
- Cannibalisation may be exaggerated: [https://www.energymonitor.ai/policy/market-design/why-reports-of-renewables-price-cannibalisation-may-be-greatly-exaggerated/](https://www.energymonitor.ai/policy/market-design/why-reports-of-renewables-price-cannibalisation-may-be-greatly-exaggerated/)
- Observable Plot mobile tooltip issue: [https://talk.observablehq.com/t/tooltip-or-title-that-will-work-in-mobile-browsers/5453](https://talk.observablehq.com/t/tooltip-or-title-that-will-work-in-mobile-browsers/5453)
- WCAG accessible charts: [https://www.a11y-collective.com/blog/accessible-charts/](https://www.a11y-collective.com/blog/accessible-charts/)
- Gov.uk text descriptions for data visualisations: [https://accessibility.blog.gov.uk/2023/04/13/text-descriptions-for-data-visualisations/](https://accessibility.blog.gov.uk/2023/04/13/text-descriptions-for-data-visualisations/)
- UK settlement timezone and BST handling: Elexon MHHS documentation; [https://www.energy-uk.org.uk/publications/euk-explains-market-wide-half-hourly-settlement/](https://www.energy-uk.org.uk/publications/euk-explains-market-wide-half-hourly-settlement/)
- Dead man switch for cron monitoring: [https://deadmanping.com/blog/cron-job-silent-failure-detection](https://deadmanping.com/blog/cron-job-silent-failure-detection)

---
*Pitfalls research for: UK CfD renewables subsidies data-journalism static site*
*Researched: 2026-04-14*
