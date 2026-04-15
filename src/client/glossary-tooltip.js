// Phase 01.1 — Glossary tooltip (D-17..D-20). Vanilla JS, no framework deps.
// Loaded once per page via:
//   <script type="module" src="/client/glossary-tooltip.js"></script>

const HOVER_DELAY_MS   = 150;
const DISMISS_DELAY_MS = 100;
const GLOSSARY_URL     = "/content/glossary.json";

let glossary = null;
let activeTooltip = null;
let hoverTimer = null;
let dismissTimer = null;

function reduceMotion() {
  return typeof window !== "undefined"
    && window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

async function loadGlossary() {
  if (glossary) return glossary;
  const res = await fetch(GLOSSARY_URL);
  if (!res || !res.ok) { glossary = {}; return glossary; }
  glossary = await res.json();
  return glossary;
}

function buildTooltip(slug, entry) {
  const tip = document.createElement("div");
  tip.id = `tooltip-${slug}`;
  tip.setAttribute("role", "tooltip");
  tip.className = [
    "fixed bg-card border border-surface rounded p-2 px-3 shadow-lg",
    "max-w-[280px] text-sm z-[100]",
    reduceMotion() ? "" : "transition-opacity duration-[120ms] opacity-0",
  ].filter(Boolean).join(" ");

  // Term: bolded; definition: plain text. Both via textContent on child nodes
  // — NEVER innerHTML for the definition (XSS guard, T-01.1-01).
  const termEl = document.createElement("strong");
  termEl.className = "text-primary font-semibold block";
  termEl.textContent = entry.term || "";

  const defEl = document.createElement("span");
  defEl.className = "text-muted block";
  defEl.textContent = entry.definition || "";

  tip.appendChild(termEl);
  tip.appendChild(defEl);

  // Desktop-only dismiss hint
  if (typeof window !== "undefined"
      && window.matchMedia
      && window.matchMedia("(hover: hover)").matches) {
    const hint = document.createElement("span");
    hint.className = "text-muted text-sm block mt-1";
    hint.textContent = "(press Esc to close)";
    tip.appendChild(hint);
  }

  document.body.appendChild(tip);
  return tip;
}

function position(tip, anchor) {
  const r = anchor.getBoundingClientRect();
  const tr = tip.getBoundingClientRect();
  let top = r.top - tr.height - 8;
  if (top < 8) top = r.bottom + 8;     // flip below if above viewport
  let left = r.left + (r.width - tr.width) / 2;
  const maxLeft = (typeof innerWidth !== "undefined" ? innerWidth : 1024) - tr.width - 8;
  left = Math.max(8, Math.min(left, maxLeft));
  tip.style.top  = `${top}px`;
  tip.style.left = `${left}px`;
}

function show(anchor) {
  const slug = anchor.dataset ? anchor.dataset.glossary : anchor.getAttribute("data-glossary");
  if (!glossary || !slug) return;
  const entry = glossary[slug];
  if (!entry) return;
  hide();
  const tip = buildTooltip(slug, entry);
  position(tip, anchor);
  anchor.setAttribute("aria-describedby", tip.id);
  activeTooltip = { tip, anchor };
  if (!reduceMotion()) requestAnimationFrame(() => { tip.style.opacity = "1"; });
}

function hide() {
  if (!activeTooltip) return;
  const { tip, anchor } = activeTooltip;
  anchor.removeAttribute("aria-describedby");
  const parent = tip.parentNode || tip.parent;
  if (parent && parent.removeChild) parent.removeChild(tip);
  else if (typeof tip.remove === "function") tip.remove();
  activeTooltip = null;
}

export async function init() {
  await loadGlossary();
  const anchors = document.querySelectorAll("abbr[data-glossary]");
  for (const a of anchors) {
    if (typeof a.tabIndex === "number") a.tabIndex = 0;
    a.addEventListener("mouseenter", () => {
      clearTimeout(dismissTimer);
      hoverTimer = setTimeout(() => show(a), HOVER_DELAY_MS);
    });
    a.addEventListener("mouseleave", () => {
      clearTimeout(hoverTimer);
      dismissTimer = setTimeout(hide, DISMISS_DELAY_MS);
    });
    a.addEventListener("touchstart", (e) => {
      if (e && e.preventDefault) e.preventDefault();
      if (activeTooltip && activeTooltip.anchor === a) hide();
      else show(a);
    }, { passive: false });
    a.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        if (e.preventDefault) e.preventDefault();
        show(a);
      }
    });
  }
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
  document.addEventListener("touchstart", (e) => {
    if (!activeTooltip) return;
    const t = e.target;
    if (t !== activeTooltip.anchor && (!activeTooltip.tip.contains || !activeTooltip.tip.contains(t))) hide();
  });
  if (typeof window !== "undefined" && window.addEventListener) {
    window.addEventListener("scroll", hide, { passive: true });
  }
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    // Fire-and-forget; tests await init() explicitly when they need synchrony.
    init();
  }
}
