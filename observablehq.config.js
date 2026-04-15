export default {
  title: "CfD Visualiser",
  root: "src",
  pages: [
    { name: "Home", path: "/" }
  ],
  head: `
<link rel="stylesheet" href="/assets/pico.min.css">
<link rel="stylesheet" href="/assets/custom.css">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="UK Contracts for Difference: what consumers pay vs the market. Daily-rebuilt from LCCC data.">
  `.trim(),
  theme: "air",
  footer: "Built daily from the LCCC dataset."
};
