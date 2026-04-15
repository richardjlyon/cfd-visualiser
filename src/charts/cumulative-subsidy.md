---
title: "Cumulative subsidy: who gets the money?"
toc: false
---

```js
const meta = FileAttachment("../data/meta.json").json();
const captions = FileAttachment("../content/captions.json").json();
```

<p class="text-sm text-muted mb-4">
  <a href="/" class="text-muted hover:text-accent">← All charts</a>
</p>

<h1 class="text-[28px] font-semibold text-primary mb-4">${captions["chart-cumulative-subsidy"].card_title}</h1>

<p class="text-base text-primary leading-relaxed mb-4">${captions["chart-cumulative-subsidy"].caption}</p>

<p class="text-base text-primary leading-relaxed mb-6">
  Total <abbr data-glossary="cfd">CfD</abbr> consumer subsidy stacked by project, plotted across each
  <abbr data-glossary="allocation_round">allocation round</abbr>. The Lorenz curve overlay shows how
  concentrated the subsidy stream is — a small number of projects receive the majority of payments.
</p>

<figure class="chart bg-dashboard rounded-lg overflow-hidden my-6"
        role="img"
        aria-labelledby="chart-cumulative-title"
        aria-describedby="chart-cumulative-desc">
  <div id="chart-cumulative-title" hidden>Cumulative subsidy — placeholder</div>
  <div id="chart-cumulative-desc" hidden>Chart coming in Phase 02</div>
  <div class="p-12 text-center text-muted">
    <p class="text-xl text-primary mb-2">Chart coming in Phase 02</p>
    <p class="text-sm">Cumulative consumer subsidy stacked by technology with a Lorenz concentration scatter.</p>
  </div>
</figure>

<p class="text-sm text-muted italic mt-2">
  Source: <a href="https://dp.lowcarboncontracts.uk" class="text-accent">LCCC ACGE dataset</a>
  · Data pending — chart ships in Phase 02
</p>

<p class="mt-2 text-sm">
  <a class="text-accent hover:underline min-h-[44px] inline-flex items-center"
     href="/assets/charts/chart-cumulative-subsidy-placeholder.png"
     download="cfd-cumulative-subsidy-placeholder-${meta.max_settlement_date}.png">Download image (placeholder)</a>
</p>

<aside class="bg-card border border-surface rounded-lg p-6 my-6">
  <h2 class="text-xl font-semibold text-primary mb-2">What does this mean?</h2>
  <div class="prose text-base text-primary leading-relaxed">
    ${captions["chart-cumulative-subsidy"].boxout}
  </div>
</aside>

<script type="module" src="/client/glossary-tooltip.js"></script>
