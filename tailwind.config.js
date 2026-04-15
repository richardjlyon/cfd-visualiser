/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./src/**/*.{md,html,js,mjs}",
    "./observablehq.config.js"
  ],
  theme: {
    extend: {
      colors: {
        dashboard: "#0d1117",
        card:      "#161b22",
        surface:   "#30363d",
        accent:    "#58a6ff",
        primary:   "#e6edf3",
        muted:     "#8b949e",
        grid:      "#21262d",
        "on-accent": "#0d1117"
      },
      fontFamily: {
        display: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"]
      }
    }
  },
  plugins: []
};
