---
title: "SubsidyDashboard — UK renewables subsidy in real time"
toc: false
sidebar: false
---

```js
import * as Plot from "npm:@observablehq/plot";
import * as d3 from "npm:d3";
const meta = FileAttachment("./data/meta.json").json();
const captions = FileAttachment("./content/captions.json").json();
const chart3c = FileAttachment("./data/chart-3c.json").json();
```

```js
display(html`<section class="bg-card border-b border-surface">
  <div class="max-w-7xl mx-auto px-6 pt-10 pb-6 flex items-start justify-between gap-4 flex-wrap">
    <div class="flex-1 min-w-[260px]">
      <h1 class="text-2xl sm:text-3xl font-semibold text-accent mb-2">Live UK Renewables Subsidy</h1>
      <p class="text-sm text-muted max-w-3xl">Real-time picture of what UK consumers are paying for low-carbon electricity under the Contracts for Difference scheme. Daily-rebuilt from the LCCC dataset, every chart traces a subsidy in pounds, tonnes of CO₂, or generation share back to source data you can download.</p>
    </div>
    <div class="flex items-center gap-3 text-sm">
      <span class="text-muted">Share:</span>
      <a class="share-icon" aria-label="Share on LinkedIn" href="https://www.linkedin.com/sharing/share-offsite/?url=https://subsidydashboard.uk/" target="_blank" rel="noopener">in</a>
      <a class="share-icon" aria-label="Share on X" href="https://twitter.com/intent/tweet?url=https://subsidydashboard.uk/&text=UK%20renewables%20subsidy%20live" target="_blank" rel="noopener">𝕏</a>
      <a class="share-icon" aria-label="Share on Bluesky" href="https://bsky.app/intent/compose?text=https://subsidydashboard.uk/" target="_blank" rel="noopener">🦋</a>
      <a class="share-icon" aria-label="Share on Facebook" href="https://www.facebook.com/sharer/sharer.php?u=https://subsidydashboard.uk/" target="_blank" rel="noopener">f</a>
      <a class="share-icon" aria-label="Share on WhatsApp" href="https://wa.me/?text=https://subsidydashboard.uk/" target="_blank" rel="noopener">✉</a>
      <a class="share-icon" aria-label="Email" href="mailto:?subject=SubsidyDashboard&body=https://subsidydashboard.uk/">@</a>
      <button class="share-icon" aria-label="Copy link" onclick="navigator.clipboard?.writeText(location.href)">⧉</button>
    </div>
  </div>
  <div class="max-w-7xl mx-auto px-6 pb-12 text-center">
    <p class="text-xs uppercase tracking-wider text-muted mb-2">Total CfD subsidy paid since 1 Jan ${meta.ytd_label_year}</p>
    <p class="text-shock text-accent mb-1"
       id="shock-numeral"
       data-ytd="${meta.ytd_subsidy_gbp}"
       data-rate="${meta.gbp_per_sec_rate}"
       aria-live="off">£${(meta.ytd_subsidy_gbp / 1e9).toFixed(2)} billion</p>
    <p class="text-xs text-muted">As of ${meta.ytd_as_of} · live count-up from pre-baked £${meta.gbp_per_sec_rate.toFixed(0)}/sec rate</p>
  </div>
</section>`);
```

```js
// Sparkline for the Scissors card — strike vs market price across all rows.
// Aggregate to monthly mean so the spark stays readable at 280px width.
const monthly = d3.rollups(
  chart3c.filter(r => r.round === "Allocation Round 1" || r.round === "All"),
  v => ({ strike: d3.mean(v, d => d.strike), market: d3.mean(v, d => d.market) }),
  d => d.month
).map(([month, agg]) => ({ month: new Date(month + "-01"), ...agg }))
 .sort((a, b) => a.month - b.month);

const sparkScissors = Plot.plot({
  width: 280, height: 110,
  marginLeft: 4, marginRight: 4, marginTop: 4, marginBottom: 14,
  axis: null,
  style: { background: "transparent" },
  marks: [
    Plot.areaY(monthly, { x: "month", y1: "market", y2: "strike", fill: "#58a6ff", fillOpacity: 0.18 }),
    Plot.line(monthly, { x: "month", y: "strike", stroke: "#58a6ff", strokeWidth: 1.5 }),
    Plot.line(monthly, { x: "month", y: "market", stroke: "#f78166", strokeWidth: 1.5 })
  ]
});
```

```js
// Mini stat blocks for the placeholder cards (Phase 02 will replace with real charts)
function statBlock(value, label, color = "var(--color-accent)") {
  return html`<div class="stat-block">
    <div class="stat-value" style="color:${color}">${value}</div>
    <div class="stat-label">${label}</div>
  </div>`;
}
```

```js
display(html`<section class="max-w-7xl mx-auto px-6 py-10">
  <div class="flex items-baseline justify-between mb-6">
    <h2 class="text-lg font-semibold text-primary">Explore the charts</h2>
    <span class="text-xs text-muted">${meta.row_count.toLocaleString()} daily rows · schema ${meta.schema_version}</span>
  </div>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

    <a class="cfd-card" href="./charts/scissors">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-01 · Live</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-3c"].card_title}</h3>
      <div class="card-viz">${sparkScissors}</div>
      <p class="text-xs text-muted mb-3">${captions["chart-3c"].card_hook}</p>
      <span class="text-sm text-accent">Explore →</span>
    </a>

    <a class="cfd-card" href="./charts/co2-avoided">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-02 · Coming Phase 02</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-co2-avoided"].card_title}</h3>
      <div class="card-viz">${statBlock("£200–400", "per tonne CO₂ avoided", "#f0883e")}</div>
      <p class="text-xs text-muted mb-3">${captions["chart-co2-avoided"].card_hook}</p>
      <span class="text-sm text-accent">Explore →</span>
    </a>

    <a class="cfd-card" href="./charts/cumulative-subsidy">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-03 · Coming Phase 02</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-cumulative-subsidy"].card_title}</h3>
      <div class="card-viz">${statBlock("80%", "of subsidy → top 10 projects", "#a371f7")}</div>
      <p class="text-xs text-muted mb-3">${captions["chart-cumulative-subsidy"].card_hook}</p>
      <span class="text-sm text-accent">Explore →</span>
    </a>

    <a class="cfd-card" href="./charts/generation-heatmap">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-04 · Coming Phase 02</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-heatmap"].card_title}</h3>
      <div class="card-viz">${statBlock("Dunkelflaute", "calm-and-dark voids", "#56d364")}</div>
      <p class="text-xs text-muted mb-3">${captions["chart-heatmap"].card_hook}</p>
      <span class="text-sm text-accent">Explore →</span>
    </a>

  </div>
</section>`);
```

```js
display(html`<footer class="bg-card border-t border-surface mt-4 py-6 px-6">
  <div class="max-w-7xl mx-auto text-xs text-muted flex flex-wrap gap-x-4 gap-y-1">
    <span>Built daily from the LCCC dataset.</span>
    <span>Source: <a href="https://dp.lowcarboncontracts.uk" class="text-accent">dp.lowcarboncontracts.uk</a></span>
    <span>Last build: ${meta.last_updated}</span>
  </div>
</footer>`);
```

<script type="module" src="/client/shock-counter.js"></script>
<script type="module" src="/client/glossary-tooltip.js"></script>
