export default {
  title: "CfD Visualiser",
  root: "src",
  pages: [
    { name: "Home", path: "/" },
    { name: "Scissors", path: "/charts/scissors" }
  ],
  head: `
<script>document.documentElement.setAttribute('data-theme','light')</script>
<link rel="stylesheet" href="/assets/pico.min.css">
<link rel="stylesheet" href="/assets/custom.css">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="UK Contracts for Difference: what consumers pay vs the market. Daily-rebuilt from LCCC data.">
<meta property="og:title" content="CfD Visualiser">
<meta property="og:description" content="UK CfD: what consumers pay vs the market.">
<meta property="og:image" content="/assets/og-card.png">
<meta property="og:type" content="website">
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "__CF_WEB_ANALYTICS_TOKEN__"}'></script>
  `.trim(),
  theme: "air",
  footer: "Built daily from the LCCC dataset."
};
