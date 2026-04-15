---
title: "Intermittency: when the wind stops blowing"
toc: false
---

```js
const meta = FileAttachment("../data/meta.json").json();
const captions = FileAttachment("../content/captions.json").json();
```

<p class="text-sm text-muted mb-4">
  <a href="/" class="text-muted hover:text-accent">← All charts</a>
</p>

<h1 class="text-[28px] font-semibold text-primary mb-4">${captions["chart-heatmap"].card_title}</h1>

<p class="text-base text-primary leading-relaxed mb-4">${captions["chart-heatmap"].caption}</p>

<p class="text-base text-primary leading-relaxed mb-6">
  A daily generation heatmap (year × day-of-year) for wind and solar reveals when
  <abbr data-glossary="intermittent">intermittent</abbr> output collapses — the so-called Dunkelflaute periods.
  The contrast with <abbr data-glossary="dispatchable">dispatchable</abbr> technologies shows why the grid still
  depends on backup capacity.
</p>

<figure class="chart bg-dashboard rounded-lg overflow-hidden my-6"
        role="img"
        aria-labelledby="chart-heatmap-title"
        aria-describedby="chart-heatmap-desc">
  <div id="chart-heatmap-title" hidden>Daily generation heatmap — placeholder</div>
  <div id="chart-heatmap-desc" hidden>Chart coming in Phase 02</div>
  <div class="p-12 text-center text-muted">
    <p class="text-xl text-primary mb-2">Chart coming in Phase 02</p>
    <p class="text-sm">Daily generation heatmap (year × day-of-year) for wind and solar with mobile-simplified weekly fallback.</p>
  </div>
</figure>

<p class="text-sm text-muted italic mt-2">
  Source: <a href="https://dp.lowcarboncontracts.uk" class="text-accent">LCCC ACGE dataset</a>
  · Data pending — chart ships in Phase 02
</p>

<p class="mt-2 text-sm">
  <a class="text-accent hover:underline min-h-[44px] inline-flex items-center"
     href="/assets/charts/chart-heatmap-placeholder.png"
     download="cfd-generation-heatmap-placeholder-${meta.max_settlement_date}.png">Download image (placeholder)</a>
</p>

<aside class="bg-card border border-surface rounded-lg p-6 my-6">
  <h2 class="text-xl font-semibold text-primary mb-2">What does this mean?</h2>
  <div class="prose text-base text-primary leading-relaxed">
    ${captions["chart-heatmap"].boxout}
  </div>
</aside>

<script type="module" src="/client/glossary-tooltip.js"></script>
