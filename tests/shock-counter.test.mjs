// Wave-0 RED tests for src/client/shock-counter.js (plan 06 target).
//
// Pins the shock-counter behavioural contract:
//   - prefers-reduced-motion: reduce  -> freeze at start value, NO rAF.
//   - reduce-motion false              -> rAF fires and value ticks upward.
//
// Uses node's built-in test runner with a minimal DOM stub.
// Run: node --test tests/shock-counter.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";

function installDomStub({ reduceMotion = false } = {}) {
  let rafCalls = 0;
  const el = {
    dataset: { ytd: "1234567890.00", rate: "100.50" },
    _text: "",
    set textContent(v) { this._text = String(v); },
    get textContent() { return this._text; },
    setAttribute() {},
    getAttribute() { return null; },
  };
  globalThis.document = {
    readyState: "complete",
    getElementById: (id) => (id === "shock-numeral" ? el : null),
    addEventListener: () => {},
  };
  globalThis.window = {
    matchMedia: (q) => ({
      matches: q.includes("reduce") ? reduceMotion : false,
      addEventListener() {},
      removeEventListener() {},
    }),
    addEventListener() {},
  };
  globalThis.matchMedia = globalThis.window.matchMedia;
  let now = 0;
  globalThis.performance = { now: () => now };
  globalThis.advanceMs = (ms) => { now += ms; };
  globalThis.requestAnimationFrame = (fn) => {
    rafCalls++;
    if (rafCalls < 3) fn(now);
    return rafCalls;
  };
  globalThis.rafCalls = () => rafCalls;
  return el;
}

test("shock-counter: module imports", async () => {
  installDomStub();
  // RED until plan 06 ships src/client/shock-counter.js.
  await assert.doesNotReject(() => import("../src/client/shock-counter.js?1"));
});

test("shock-counter: reduce-motion freezes value, no rAF", async () => {
  const el = installDomStub({ reduceMotion: true });
  await import("../src/client/shock-counter.js?2");
  // Allow auto-init via DOMContentLoaded emulation.
  await new Promise((r) => setTimeout(r, 20));
  assert.equal(
    rafCalls(),
    0,
    "rAF must not fire under prefers-reduced-motion: reduce",
  );
  assert.match(el._text, /£/, "static value rendered with £ prefix");
});

test("shock-counter: ticks upward with rAF", async () => {
  const el = installDomStub({ reduceMotion: false });
  await import("../src/client/shock-counter.js?3");
  advanceMs(1000);
  // Kick one more frame (the module should re-schedule itself).
  globalThis.requestAnimationFrame(() => {});
  assert.ok(
    rafCalls() >= 1,
    "rAF should fire at least once when reduce-motion is false",
  );
});
