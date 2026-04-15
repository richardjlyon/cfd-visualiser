---
title: Strike vs market — CfD scissors
toc: false
---

# UK CfD: what consumers pay vs the market

```js
const data = FileAttachment("../data/chart-3c.json").json();
const meta = FileAttachment("../data/meta.json").json();
const captions = FileAttachment("../content/captions.json").json();
const chartDataUrl = FileAttachment("../data/chart-3c.json").url();
```

```js
const c = captions["chart-3c"];
```

```js
display(html`<p class="caption">${c.caption}</p>`);
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
  style: { fontSize: "14px" },
  x: { label: "Settlement month", type: "utc", tickFormat: "%Y" },
  y: { label: "£ / MWh", grid: true },
  color: {
    legend: true,
    domain: ["Strike price", "Market reference price"],
    range: ["var(--okabe-blue)", "var(--okabe-orange)"]
  },
  marks: [
    Plot.areaY(filtered, {
      x: d => new Date(d.month + "-01"),
      y1: "market",
      y2: "strike",
      fill: d => d.strike >= d.market
                 ? "var(--okabe-vermillion)"
                 : "var(--okabe-green)",
      fillOpacity: 0.18
    }),
    Plot.lineY(filtered, {
      x: d => new Date(d.month + "-01"),
      y: "strike",
      stroke: "var(--okabe-blue)",
      strokeWidth: 2,
      tip: true,
      title: d => `Strike: £${d.strike.toFixed(2)}/MWh`
    }),
    Plot.lineY(filtered, {
      x: d => new Date(d.month + "-01"),
      y: "market",
      stroke: "var(--okabe-orange)",
      strokeWidth: 2,
      tip: true,
      title: d => `Market: £${d.market.toFixed(2)}/MWh`
    }),
    Plot.ruleY([0])
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
display(html`<p class="source-line">
  Source: <a href="${c.source_url}">${c.source_name}</a>.
  Last updated: ${meta.last_updated}.
</p>`);
```

<aside class="boxout">
  <h3>What does this mean?</h3>

```js
display(html`<p>${c.boxout}</p>`);
```

</aside>

```js
display(html`<p><a class="download" href="${chartDataUrl}" download="chart-3c.json">Download this chart's data (JSON)</a></p>`);
```
