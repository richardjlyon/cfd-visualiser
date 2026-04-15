// Wave-0 RED tests for src/client/glossary-tooltip.js (plan 06 target).
//
// Uses node's built-in test runner + a hand-rolled minimal DOM stub so we
// avoid a jsdom dependency. The stub deliberately provides NO innerHTML
// setter — implementations that try to render glossary content via
// innerHTML will silently fail, pinning the createElement+textContent
// (XSS-safe) contract plan 06 must honour.
//
// STRIDE-S/T mitigation: the third test asserts that a glossary value
// containing `<script>alert(1)</script>` is rendered as text, not as a
// live <script> element.
//
// Run: node --test tests/glossary-tooltip.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";

function installDomStub({ reduceMotion = false } = {}) {
  const listeners = new Map(); // element -> { [event]: fn[] }

  function el(tag) {
    const e = {
      tagName: String(tag).toUpperCase(),
      children: [],
      attributes: {},
      style: {},
      dataset: {},
      _text: "",
      classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
      setAttribute(k, v) {
        this.attributes[k] = v;
        if (k.startsWith("data-")) {
          const camel = k.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
          this.dataset[camel] = v;
        }
      },
      removeAttribute(k) { delete this.attributes[k]; },
      getAttribute(k) { return this.attributes[k]; },
      appendChild(c) { this.children.push(c); c.parent = this; return c; },
      removeChild(c) { this.children = this.children.filter(x => x !== c); },
      remove() { if (this.parent) this.parent.removeChild(this); },
      querySelectorAll(sel) { return collect(this, sel); },
      querySelector(sel) { return collect(this, sel)[0] || null; },
      addEventListener(ev, fn) {
        const map = listeners.get(this) || {};
        (map[ev] ||= []).push(fn);
        listeners.set(this, map);
      },
      removeEventListener(ev, fn) {
        const map = listeners.get(this) || {};
        map[ev] = (map[ev] || []).filter(f => f !== fn);
        listeners.set(this, map);
      },
      dispatch(ev, payload = {}) {
        const fns = (listeners.get(this) || {})[ev] || [];
        for (const fn of fns) fn({ type: ev, target: this, preventDefault() {}, stopPropagation() {}, ...payload });
      },
      getBoundingClientRect() { return { top: 0, left: 0, width: 10, height: 10, bottom: 10, right: 10 }; },
      set textContent(v) { this._text = String(v); this.children = []; },
      get textContent() { return this._text; },
      // NOTE: no innerHTML setter — implementations that assign to innerHTML
      // will silently fail. This pins the createElement+textContent contract.
    };
    return e;
  }

  function collect(root, sel) {
    // Minimal selector support: "abbr[data-glossary]" and `[role="tooltip"]`.
    const out = [];
    function matches(n) {
      if (!n || !n.tagName) return false;
      if (sel === "abbr[data-glossary]") {
        return n.tagName === "ABBR" && n.attributes["data-glossary"];
      }
      if (sel === '[role="tooltip"]') {
        return n.attributes && n.attributes.role === "tooltip";
      }
      return false;
    }
    function walk(n) {
      if (matches(n)) out.push(n);
      for (const c of n.children || []) walk(c);
    }
    walk(root);
    return out;
  }

  const body = el("body");
  const doc = {
    body,
    documentElement: el("html"),
    readyState: "complete",
    createElement: el,
    querySelectorAll: (sel) => body.querySelectorAll(sel),
    querySelector: (sel) => body.querySelector(sel),
    addEventListener(ev, fn) { body.addEventListener(ev, fn); },
    removeEventListener(ev, fn) { body.removeEventListener(ev, fn); },
    dispatch: (ev, payload) => body.dispatch(ev, payload),
  };
  globalThis.document = doc;
  globalThis.window = {
    matchMedia: (q) => ({ matches: q.includes("reduce") ? reduceMotion : false, addEventListener() {}, removeEventListener() {} }),
    addEventListener() {},
    innerWidth: 1024,
    innerHeight: 768,
  };
  globalThis.matchMedia = globalThis.window.matchMedia;
  globalThis.requestAnimationFrame = (fn) => { fn(0); return 1; };
  globalThis.performance = { now: () => 0 };
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      cfd: { term: "CfD", definition: "Contract for Difference." },
      strike_price: { term: "Strike price", definition: "<script>alert(1)</script>" },
    }),
  });
  return { doc, body, el };
}

test("glossary-tooltip: module imports without throwing", async () => {
  installDomStub();
  // RED until plan 06 ships src/client/glossary-tooltip.js.
  await assert.doesNotReject(async () => {
    await import("../src/client/glossary-tooltip.js?1");
  });
});

test("glossary-tooltip: Enter opens tooltip, Escape closes", async () => {
  const { doc, body, el } = installDomStub();
  const abbr = el("abbr");
  abbr.setAttribute("data-glossary", "cfd");
  body.appendChild(abbr);
  const mod = await import("../src/client/glossary-tooltip.js?2");
  if (typeof mod.init === "function") await mod.init();
  else await new Promise((r) => setTimeout(r, 20));
  abbr.dispatch("keydown", { key: "Enter" });
  const tip = body.children.find(
    (c) => c.attributes && c.attributes.role === "tooltip",
  );
  assert.ok(tip, "tooltip should be in body after Enter");
  // Aggregate text across tooltip children (mirrors real Node.textContent).
  function aggregateText(node) {
    let out = node._text || "";
    for (const child of node.children || []) out += aggregateText(child);
    return out;
  }
  assert.match(aggregateText(tip), /CfD/);
  doc.dispatch("keydown", { key: "Escape" });
  const afterEsc = body.children.find(
    (c) => c.attributes && c.attributes.role === "tooltip",
  );
  assert.equal(afterEsc, undefined, "tooltip should be removed after Escape");
});

test("glossary-tooltip: definition renders as text (no HTML execution)", async () => {
  const { body, el } = installDomStub();
  const abbr = el("abbr");
  abbr.setAttribute("data-glossary", "strike_price");
  body.appendChild(abbr);
  const mod = await import("../src/client/glossary-tooltip.js?3");
  if (typeof mod.init === "function") await mod.init();
  abbr.dispatch("keydown", { key: "Enter" });
  const tip = body.children.find(
    (c) => c.attributes && c.attributes.role === "tooltip",
  );
  assert.ok(tip, "tooltip should exist for XSS guard test");
  // Aggregate textContent across children — this mirrors the real DOM's
  // Node.textContent getter, which concatenates descendant text nodes.
  // Plan 06 uses createElement + textContent on child spans (XSS-safe), so
  // the literal "<script>..." string must appear as TEXT inside a child
  // node, not parse into a live <script> element.
  function aggregateText(node) {
    let out = node._text || "";
    for (const child of node.children || []) out += aggregateText(child);
    return out;
  }
  const aggregated = aggregateText(tip);
  assert.ok(aggregated.length > 0, "tooltip must have rendered text content");
  assert.match(aggregated, /CfD|Strike price/, "term rendered as text");
  assert.ok(
    aggregated.includes("<script>alert(1)</script>"),
    "XSS guard: definition must be rendered as text via textContent — the literal <script>...</script> string must appear in the aggregated text content of the tooltip (never parsed into a live DOM element). This pins the createElement+textContent contract used by plan 06.",
  );
});
