---
title: "The scissors: what you pay vs the market"
toc: false
---

```js
const data = FileAttachment("../data/chart-3c.json").json();
const meta = FileAttachment("../data/meta.json").json();
const captions = FileAttachment("../content/captions.json").json();
const chartDataUrl = FileAttachment("../data/chart-3c.json").url();
```

```js
const c = captions["chart-3c"];
```

<nav class="max-w-3xl mx-auto px-4 pt-6">
  <a href="/" class="text-sm text-muted hover:text-accent">← All charts</a>
</nav>

<main class="max-w-3xl mx-auto px-4">

<h1 class="text-[28px] font-semibold text-primary mt-4 mb-4">The scissors: what you pay vs the market</h1>

<p class="text-base text-primary leading-relaxed mb-6">
  Under the UK's <abbr data-glossary="cfd">CfD</abbr> scheme, generators are paid the difference between an agreed
  <abbr data-glossary="strike_price">strike price</abbr> and the wholesale market
  <abbr data-glossary="reference_price">reference price</abbr> (specifically the
  <abbr data-glossary="imrp">IMRP</abbr> for intermittent generation).
  This chart traces those two prices over time across all
  <abbr data-glossary="allocation_round">allocation rounds</abbr>.
</p>

```js
display(html`<p class="text-base text-primary">${c.caption}</p>`);
```

```js
const roundLabels = ["All", "Investment Contract", "Allocation Round 1",
                     "Allocation Round 2", "Allocation Round 4", "Allocation Round 5"];
const selectedRound = view(Inputs.radio(roundLabels, {
  label: "Show allocation rounds:",
  value: "All"
}));
```

```js
function rollupAllRounds(rows) {
  const byMonth = d3.rollups(
    rows,
    v => ({
      strike: d3.sum(v, d => d.strike * d.generation_mwh) /
              d3.sum(v, d => d.generation_mwh),
      market: d3.sum(v, d => d.market * d.generation_mwh) /
              d3.sum(v, d => d.generation_mwh),
      payments_gbp: d3.sum(v, d => d.payments_gbp),
      generation_mwh: d3.sum(v, d => d.generation_mwh),
    }),
    d => d.month
  );
  return byMonth.map(([month, agg]) => ({ month, round: "All", ...agg }));
}

const filtered = selectedRound === "All"
  ? rollupAllRounds(data)
  : data.filter(d => d.round === selectedRound);
```

<figure class="chart" role="img"
        aria-labelledby="chart-3c-title"
        aria-describedby="chart-3c-caption">
  <div id="chart-3c-title" hidden>
    Strike price vs market reference price over time — the scissors chart.
  </div>

```js
display(Plot.plot({
  marginLeft: 60,
  marginBottom: 40,
  style: { color: "#e6edf3", background: "#0d1117", fontSize: "14px" },
  x: { label: "Settlement month", type: "utc", tickFormat: "%Y" },
  y: { label: "£ / MWh", grid: true },
  color: {
    legend: true,
    domain: ["Strike price", "Market reference price"],
    range: ["#58a6ff", "#e6a817"]
  },
  marks: [
    Plot.areaY(filtered, {
      x: d => new Date(d.month + "-01"),
      y1: "market",
      y2: "strike",
      fill: d => d.strike >= d.market ? "#f44336" : "#4caf50",
      fillOpacity: 0.20
    }),
    Plot.lineY(filtered, {
      x: d => new Date(d.month + "-01"),
      y: "strike",
      stroke: "#58a6ff",
      strokeWidth: 2,
      tip: true,
      title: d => `Strike: £${d.strike.toFixed(2)}/MWh`
    }),
    Plot.lineY(filtered, {
      x: d => new Date(d.month + "-01"),
      y: "market",
      stroke: "#e6a817",
      strokeWidth: 2,
      tip: true,
      title: d => `Market: £${d.market.toFixed(2)}/MWh`
    }),
    Plot.ruleY([0], { stroke: "#21262d" })
  ],
  width: 720,
  height: 480
}));
```

```js
display(html`<figcaption id="chart-3c-caption">${c.caption}</figcaption>`);
```

</figure>

```js
display(html`<p class="text-sm text-muted italic mt-2">
  Source: <a class="text-accent" href="${c.source_url}">${c.source_name}</a>.
  Last updated: ${meta.last_updated}.
</p>`);
```

```js
display(html`<p class="mt-2 text-sm">
  <a class="text-accent hover:underline min-h-[44px] inline-flex items-center"
     href="${chartDataUrl}" download="chart-3c.json">Download this chart's data (JSON)</a>
  ·
  <a class="text-accent hover:underline min-h-[44px] inline-flex items-center"
     href="/assets/charts/chart-3c.png" download="cfd-scissors-${meta.max_settlement_date}.png">Download image</a>
</p>`);
```

```js
display(html`<aside class="bg-card border border-surface rounded-lg p-6 my-6">
  <h2 class="text-xl font-semibold text-primary">What does this mean?</h2>
  <div class="prose text-base text-primary leading-relaxed">${c.boxout}</div>
</aside>`);
```

</main>

<script type="module" src="/client/glossary-tooltip.js"></script>
