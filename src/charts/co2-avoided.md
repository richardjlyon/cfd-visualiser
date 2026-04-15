---
title: "The carbon price: are CfDs worth it per tonne?"
toc: false
---

```js
const meta = FileAttachment("../data/meta.json").json();
const captions = FileAttachment("../content/captions.json").json();
```

<p class="text-sm text-muted mb-4">
  <a href="/" class="text-muted hover:text-accent">← All charts</a>
</p>

<h1 class="text-[28px] font-semibold text-primary mb-4">${captions["chart-co2-avoided"].card_title}</h1>

<p class="text-base text-primary leading-relaxed mb-4">${captions["chart-co2-avoided"].caption}</p>

<p class="text-base text-primary leading-relaxed mb-6">
  For each <abbr data-glossary="cfd">CfD</abbr> generator, dividing total consumer subsidy by tonnes of CO₂
  avoided gives an effective carbon price. The picture differs sharply between
  <abbr data-glossary="intermittent">intermittent</abbr> wind and solar contracts and the small number of
  <abbr data-glossary="dispatchable">dispatchable</abbr> biomass and hydro contracts.
</p>

<figure class="chart bg-dashboard rounded-lg overflow-hidden my-6"
        role="img"
        aria-labelledby="chart-co2-title"
        aria-describedby="chart-co2-desc">
  <div id="chart-co2-title" hidden>£/tCO₂ avoided — placeholder</div>
  <div id="chart-co2-desc" hidden>Chart coming in Phase 02</div>
  <div class="p-12 text-center text-muted">
    <p class="text-xl text-primary mb-2">Chart coming in Phase 02</p>
    <p class="text-sm">Full £/tCO₂ avoided explorer with UK ETS price and DEFRA social cost overlays.</p>
  </div>
</figure>

<p class="text-sm text-muted italic mt-2">
  Source: <a href="https://dp.lowcarboncontracts.uk" class="text-accent">LCCC ACGE dataset</a>
  · Data pending — chart ships in Phase 02
</p>

<p class="mt-2 text-sm">
  <a class="text-accent hover:underline min-h-[44px] inline-flex items-center"
     href="/assets/charts/chart-co2-avoided-placeholder.png"
     download="cfd-co2-avoided-placeholder-${meta.max_settlement_date}.png">Download image (placeholder)</a>
</p>

<aside class="bg-card border border-surface rounded-lg p-6 my-6">
  <h2 class="text-xl font-semibold text-primary mb-2">What does this mean?</h2>
  <div class="prose text-base text-primary leading-relaxed">
    ${captions["chart-co2-avoided"].boxout}
  </div>
</aside>

<script type="module" src="/client/glossary-tooltip.js"></script>
