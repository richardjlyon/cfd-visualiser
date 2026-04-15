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
display(html`<section class="hero">
  <div class="hero-row">
    <div class="hero-text">
      <h1 class="hero-title"><span class="bar"></span>Live UK Renewables Subsidy</h1>
      <p class="hero-lead">Real-time renewable energy subsidy data for Great Britain, rebuilt daily from the Low Carbon Contracts Company dataset. Compare what consumers pay against the wholesale market, follow the £-per-tCO₂ avoided, and see who collects the largest share of the subsidy across multiple charts.</p>
    </div>
    <div class="hero-share">
      <span class="share-label">Share:</span>
      <a class="share-icon linkedin" aria-label="Share on LinkedIn" href="https://www.linkedin.com/sharing/share-offsite/?url=https://subsidydashboard.uk/" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M20.45 20.45h-3.55v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.37V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z"/></svg></a>
      <a class="share-icon x" aria-label="Share on X" href="https://twitter.com/intent/tweet?url=https://subsidydashboard.uk/&text=UK%20renewables%20subsidy%20live" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.16 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
      <a class="share-icon bluesky" aria-label="Share on Bluesky" href="https://bsky.app/intent/compose?text=https://subsidydashboard.uk/" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M5.07 3.4c2.9 2.18 6.02 6.6 7.16 8.97 1.14-2.37 4.26-6.79 7.16-8.97 2.1-1.58 5.49-2.8 5.49 1.07 0 .77-.44 6.51-.7 7.45-.9 3.24-4.2 4.07-7.13 3.57 5.13.87 6.43 3.77 3.62 6.67-5.34 5.5-7.67-1.38-8.27-3.15-.11-.32-.16-.47-.16-.34 0-.13-.05.02-.16.34-.6 1.77-2.93 8.65-8.27 3.15-2.81-2.9-1.5-5.8 3.62-6.67-2.92.5-6.22-.33-7.13-3.57C.06 11.04-.38 5.3-.38 4.53c0-3.87 3.39-2.65 5.45-1.13z" transform="translate(0.38 0)"/></svg></a>
      <a class="share-icon facebook" aria-label="Share on Facebook" href="https://www.facebook.com/sharer/sharer.php?u=https://subsidydashboard.uk/" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M24 12a12 12 0 1 0-13.88 11.85v-8.38H7.08V12h3.04V9.36c0-3 1.79-4.66 4.53-4.66 1.31 0 2.69.23 2.69.23v2.95h-1.51c-1.49 0-1.96.93-1.96 1.88V12h3.33l-.53 3.47h-2.8v8.38A12 12 0 0 0 24 12z"/></svg></a>
      <a class="share-icon whatsapp" aria-label="Share on WhatsApp" href="https://wa.me/?text=https://subsidydashboard.uk/" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M.057 24l1.687-6.163A11.87 11.87 0 0 1 .15 11.87C.153 5.32 5.486 0 12.039 0a11.82 11.82 0 0 1 8.413 3.488 11.82 11.82 0 0 1 3.487 8.414c-.003 6.55-5.336 11.87-11.89 11.87a11.9 11.9 0 0 1-5.683-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884a9.86 9.86 0 0 0 1.51 5.26l.357.566-1 3.652zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.149-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg></a>
      <a class="share-icon email" aria-label="Email" href="mailto:?subject=SubsidyDashboard&body=https://subsidydashboard.uk/"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="2 6 12 13 22 6"/></svg></a>
      <button class="share-icon copy" aria-label="Copy link" onclick="navigator.clipboard?.writeText(location.href)"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button>
    </div>
  </div>
</section>`);
```

```js
// ── Card 1: Scissors mini line chart with legend (real chart-3c data) ──
const monthly = (() => {
  const rows = chart3c.filter(r => r.round === "Allocation Round 1");
  return d3.rollups(rows,
    v => ({ strike: d3.mean(v, d => d.strike), market: d3.mean(v, d => d.market) }),
    d => d.month
  ).map(([month, agg]) => ({ month: new Date(month + "-01"), ...agg }))
   .sort((a, b) => a.month - b.month);
})();

const cardScissors = Plot.plot({
  width: 360, height: 200,
  marginLeft: 36, marginRight: 12, marginTop: 8, marginBottom: 24,
  style: { background: "transparent", color: "#8b949e", fontSize: "10px" },
  x: { type: "time", grid: false, tickFormat: d3.timeFormat("%Y") },
  y: { grid: true, label: "£/MWh", labelArrow: false },
  marks: [
    Plot.areaY(monthly, { x: "month", y1: "market", y2: "strike", fill: "#58a6ff", fillOpacity: 0.12 }),
    Plot.line(monthly, { x: "month", y: "strike", stroke: "#58a6ff", strokeWidth: 2 }),
    Plot.line(monthly, { x: "month", y: "market", stroke: "#f78166", strokeWidth: 2 }),
    Plot.ruleY([0], { stroke: "#30363d" })
  ]
});

// ── Card 2: Cumulative subsidy donut (placeholder split: top 10 vs rest) ──
const donutData = [
  { name: "Top 10 projects", value: 80, color: "#a371f7" },
  { name: "Other projects",  value: 20, color: "#30363d" }
];
const cardDonut = (() => {
  const w = 200, h = 200, r = 78, ir = 50;
  const arc = d3.arc().innerRadius(ir).outerRadius(r);
  const pie = d3.pie().value(d => d.value).sort(null);
  const arcs = pie(donutData);
  const svg = d3.create("svg")
    .attr("viewBox", `${-w/2} ${-h/2} ${w} ${h}`)
    .attr("width", w).attr("height", h)
    .style("display", "block");
  svg.selectAll("path").data(arcs).join("path")
    .attr("d", arc).attr("fill", d => d.data.color)
    .attr("stroke", "#161b22").attr("stroke-width", 1);
  svg.append("text").attr("text-anchor", "middle").attr("dy", "-0.2em")
    .attr("fill", "#a371f7").style("font-size", "20px").style("font-weight", "600")
    .text("80%");
  svg.append("text").attr("text-anchor", "middle").attr("dy", "1em")
    .attr("fill", "#8b949e").style("font-size", "9px")
    .text("to top 10");
  return svg.node();
})();

// ── Card 3: £/tCO₂ horizontal bars (placeholder typical-range bars) ──
const barData = [
  { tech: "Offshore wind", lo: 80,  hi: 180, color: "#58a6ff" },
  { tech: "Onshore wind",  lo: 60,  hi: 130, color: "#56d364" },
  { tech: "Solar PV",      lo: 70,  hi: 160, color: "#f0883e" },
  { tech: "Biomass",       lo: 220, hi: 420, color: "#a371f7" }
];
const cardBars = Plot.plot({
  width: 360, height: 200,
  marginLeft: 96, marginRight: 28, marginTop: 8, marginBottom: 28,
  style: { background: "transparent", color: "#8b949e", fontSize: "11px" },
  x: { domain: [0, 450], grid: true, label: "£ / tCO₂ avoided", labelArrow: false, tickFormat: d => `£${d}` },
  y: { label: null },
  marks: [
    Plot.barX(barData, { x1: "lo", x2: "hi", y: "tech", fill: d => d.color, opacity: 0.85, height: 12 }),
    Plot.text(barData, { x: "hi", y: "tech", text: d => `£${d.lo}–${d.hi}`, dx: 6, fill: "#e6edf3", textAnchor: "start" }),
    Plot.ruleX([0], { stroke: "#30363d" })
  ]
});
```

```js
display(html`<section class="charts-section">
  <h2 class="section-title">Live Generation, Subsidy and Avoided Emissions</h2>

  <div class="chart-grid">

    <article class="chart-card">
      <header class="chart-card-head">
        <h3>Strike vs Market Price — Today</h3>
        <span class="chart-card-meta">${meta.last_updated.slice(0,10)}</span>
      </header>
      <div class="chart-card-legend">
        <span class="sw"><i style="background:#58a6ff"></i>Strike price</span>
        <span class="sw"><i style="background:#f78166"></i>Market reference price</span>
      </div>
      <div class="chart-card-body">${cardScissors}</div>
      <a class="chart-card-cta" href="./charts/scissors">Open Scissors chart →</a>
    </article>

    <article class="chart-card">
      <header class="chart-card-head">
        <h3>Cumulative Subsidy — Top 10 Share</h3>
        <span class="chart-card-meta">placeholder · Phase 02</span>
      </header>
      <div class="chart-card-legend">
        <span class="sw"><i style="background:#a371f7"></i>Top 10 projects</span>
        <span class="sw"><i style="background:#30363d"></i>Other</span>
      </div>
      <div class="chart-card-body">${cardDonut}</div>
      <a class="chart-card-cta" href="./charts/cumulative-subsidy">Open Cumulative chart →</a>
    </article>

    <article class="chart-card">
      <header class="chart-card-head">
        <h3>£/tCO₂ Avoided — Typical Range</h3>
        <span class="chart-card-meta">placeholder · Phase 02</span>
      </header>
      <div class="chart-card-legend">
        <span class="sw"><i style="background:#58a6ff"></i>Offshore</span>
        <span class="sw"><i style="background:#56d364"></i>Onshore</span>
        <span class="sw"><i style="background:#f0883e"></i>Solar</span>
        <span class="sw"><i style="background:#a371f7"></i>Biomass</span>
      </div>
      <div class="chart-card-body">${cardBars}</div>
      <a class="chart-card-cta" href="./charts/co2-avoided">Open £/tCO₂ chart →</a>
    </article>

  </div>

  <div class="ticker">
    <span class="ticker-label">Live ticker · CfD subsidy paid since 1 Jan ${meta.ytd_label_year}</span>
    <span class="ticker-value text-accent"
          id="shock-numeral"
          data-ytd="${meta.ytd_subsidy_gbp}"
          data-rate="${meta.gbp_per_sec_rate}"
          aria-live="off">£${(meta.ytd_subsidy_gbp / 1e9).toFixed(2)}b</span>
    <span class="ticker-meta">As of ${meta.ytd_as_of} · £${meta.gbp_per_sec_rate.toFixed(0)}/sec</span>
    <a class="ticker-link" href="./charts/generation-heatmap">Generation heatmap →</a>
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
