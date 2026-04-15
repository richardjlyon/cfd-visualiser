// Phase 01.1 — Hero shock counter (D-09..D-12).
// Reads start (£) and rate (£/sec) from #shock-numeral data attributes;
// animates upward via requestAnimationFrame. Frozen under prefers-reduced-motion.

const ID = "shock-numeral";

function format(valueGbp) {
  // Display in £ billions to 2dp, e.g. "£3.47 billion"
  const n = (valueGbp / 1e9);
  // en-GB locale gives comma thousands separators if/when the magnitude grows
  const fmt = new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `£${fmt.format(n)} billion`;
}

export function init() {
  const el = document.getElementById(ID);
  if (!el) return;

  const start = parseFloat(el.dataset.ytd);
  const rate  = parseFloat(el.dataset.rate);

  if (!Number.isFinite(start)) return;            // no data — leave server-rendered value
  el.textContent = format(start);                  // baseline render

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion || !Number.isFinite(rate) || rate <= 0) {
    return;                                        // freeze at start
  }

  const t0 = performance.now();
  function tick(now) {
    const elapsedSec = (now - t0) / 1000;
    const value = start + elapsedSec * rate;
    el.textContent = format(value);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// Self-register on production pages. Tests import the module then call init()
// manually after installing their DOM stub, so guarding on document.readyState
// is the contract.
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}
