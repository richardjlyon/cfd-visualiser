---
title: "CfD Visualiser — what the UK's low-carbon contracts really cost"
toc: false
---

```js
const meta = FileAttachment("./data/meta.json").json();
const captions = FileAttachment("./content/captions.json").json();
```

<header class="bg-card border-b border-surface">
  <div class="max-w-7xl mx-auto px-4 py-4">
    <a href="/" class="text-xl font-semibold text-primary no-underline">CfD Visualiser</a>
  </div>
</header>

```js
display(html`<section class="bg-card py-12 sm:py-16 px-4 text-center border-b border-surface">
  <p class="text-base text-muted mb-2">Total CfD subsidy paid since 1 Jan ${meta.ytd_label_year}</p>
  <p class="text-shock text-accent mb-2"
     id="shock-numeral"
     data-ytd="${meta.ytd_subsidy_gbp}"
     data-rate="${meta.gbp_per_sec_rate}"
     aria-live="off">£${(meta.ytd_subsidy_gbp / 1e9).toFixed(2)} billion</p>
  <p class="text-sm text-muted">As of ${meta.ytd_as_of}</p>
</section>`);
```

```js
display(html`<section class="max-w-7xl mx-auto px-4 py-12">
  <h2 class="text-xl font-semibold text-primary mb-6">Explore the charts</h2>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">

    <a class="card bg-card border border-surface rounded-lg p-6 min-h-[44px] no-underline block"
       href="./charts/scissors">
      <h3 class="text-xl font-semibold text-primary mb-2">${captions["chart-3c"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-3c"].card_hook}</p>
      <span class="text-sm text-muted">Explore →</span>
    </a>

    <a class="card bg-card border border-surface rounded-lg p-6 min-h-[44px] no-underline block"
       href="./charts/co2-avoided">
      <h3 class="text-xl font-semibold text-primary mb-2">${captions["chart-co2-avoided"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-co2-avoided"].card_hook}</p>
      <span class="text-sm text-muted">Explore →</span>
    </a>

    <a class="card bg-card border border-surface rounded-lg p-6 min-h-[44px] no-underline block"
       href="./charts/cumulative-subsidy">
      <h3 class="text-xl font-semibold text-primary mb-2">${captions["chart-cumulative-subsidy"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-cumulative-subsidy"].card_hook}</p>
      <span class="text-sm text-muted">Explore →</span>
    </a>

    <a class="card bg-card border border-surface rounded-lg p-6 min-h-[44px] no-underline block"
       href="./charts/generation-heatmap">
      <h3 class="text-xl font-semibold text-primary mb-2">${captions["chart-heatmap"].card_title}</h3>
      <p class="text-sm text-muted mb-4">${captions["chart-heatmap"].card_hook}</p>
      <span class="text-sm text-muted">Explore →</span>
    </a>

  </div>
</section>`);
```

```js
display(html`<footer class="bg-card border-t border-surface mt-12 py-8 px-4">
  <div class="max-w-7xl mx-auto text-sm text-muted">
    Built daily from the LCCC dataset.
    · Source: <a href="https://dp.lowcarboncontracts.uk" class="text-accent">dp.lowcarboncontracts.uk</a>
    · Last build: ${meta.last_updated}
  </div>
</footer>`);
```

<script type="module" src="/client/shock-counter.js"></script>
<script type="module" src="/client/glossary-tooltip.js"></script>
