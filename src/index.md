---
title: "CfD Visualiser — what the UK's low-carbon contracts really cost"
toc: false
sidebar: false
---

```js
const meta = FileAttachment("./data/meta.json").json();
const captions = FileAttachment("./content/captions.json").json();
```

```js
display(html`<section class="bg-card border-b border-surface">
  <div class="max-w-7xl mx-auto px-6 py-10">
    <h1 class="text-2xl sm:text-3xl font-semibold text-primary mb-2">UK Contracts for Difference: what consumers really pay</h1>
    <p class="text-sm text-muted max-w-3xl">Daily-rebuilt figures from the Low Carbon Contracts Company dataset. Every chart below traces a subsidy — in pounds, tonnes of CO₂, or generation share — back to source data you can download.</p>
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
display(html`<section class="max-w-7xl mx-auto px-6 py-10">
  <div class="flex items-baseline justify-between mb-6">
    <h2 class="text-lg font-semibold text-primary">Explore the charts</h2>
    <span class="text-xs text-muted">${meta.row_count.toLocaleString()} daily rows · schema ${meta.schema_version}</span>
  </div>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

    <a class="cfd-card" href="./charts/scissors">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-01</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-3c"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-3c"].card_hook}</p>
      <span class="text-sm text-accent">Explore →</span>
    </a>

    <a class="cfd-card" href="./charts/co2-avoided">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-02</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-co2-avoided"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-co2-avoided"].card_hook}</p>
      <span class="text-sm text-accent">Explore →</span>
    </a>

    <a class="cfd-card" href="./charts/cumulative-subsidy">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-03</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-cumulative-subsidy"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-cumulative-subsidy"].card_hook}</p>
      <span class="text-sm text-accent">Explore →</span>
    </a>

    <a class="cfd-card" href="./charts/generation-heatmap">
      <p class="text-xs uppercase tracking-wider text-muted mb-2">CHART-04</p>
      <h3 class="text-base font-semibold text-primary mb-2">${captions["chart-heatmap"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-heatmap"].card_hook}</p>
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
