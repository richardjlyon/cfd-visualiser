export default {
  title: "SubsidyDashboard",
  root: "src",
  theme: "near-midnight",
  sidebar: false,
  toc: false,
  header: `<header class="topnav"><div class="topnav-inner">
  <a href="/" class="brand"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" fill="currentColor" stroke="none"/></svg> SubsidyDashboard</a>
  <nav>
    <a href="/" class="active"><span class="dot"></span> Live</a>
    <a href="/charts/scissors"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 17 9 11 13 15 21 7"/><polyline points="14 7 21 7 21 14"/></svg> Scissors</a>
    <a href="/charts/co2-avoided"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2C7 7 5 11 5 14a7 7 0 0 0 14 0c0-3-2-7-7-12z"/></svg> £/tCO₂</a>
    <a href="/charts/cumulative-subsidy"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 3 3 21 21 21"/><polyline points="6 17 11 11 15 14 20 8"/></svg> Cumulative</a>
    <a href="/charts/generation-heatmap"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg> Heatmap</a>
  </nav>
  <div class="topnav-right">
    <a href="https://github.com/" class="more">More <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 10l5 5 5-5z"/></svg></a>
    <button class="theme-toggle" aria-label="Theme toggle"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg></button>
  </div>
</div>
</header>`,
  pager: false,
  pages: [
    { name: "Home",                  path: "/" },
    { name: "Scissors",              path: "/charts/scissors" },
    { name: "£/tCO₂ avoided",        path: "/charts/co2-avoided" },
    { name: "Cumulative subsidy",    path: "/charts/cumulative-subsidy" },
    { name: "Generation heatmap",    path: "/charts/generation-heatmap" }
  ],
  head: `
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@500;600;700&display=swap">
<link rel="stylesheet" href="/assets/tailwind.css">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="UK Contracts for Difference: what consumers pay vs the market. Daily-rebuilt from LCCC data.">
<meta property="og:title" content="CfD Visualiser">
<meta property="og:description" content="UK CfD: what consumers pay vs the market.">
<meta property="og:image" content="/assets/og-card.png">
<meta property="og:type" content="website">
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "__CF_WEB_ANALYTICS_TOKEN__"}'></script>
  `.trim(),
  // Footer rendered inside src/index.md to use Tailwind utility classes.
  // Framework's plain-string footer cannot accept HTML markup.
  footer: ""
};
