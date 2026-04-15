export default {
  title: "CfD Visualiser",
  root: "src",
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap">
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
