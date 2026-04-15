---
phase: 1
slug: pipeline-first-chart
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-14
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `01-RESEARCH.md` §Validation Architecture (Nyquist invariants for LCCC pipeline).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (latest) for Python pipeline; no JS test framework needed for v1 (Observable Framework has no unit-test story — chart correctness verified via data contract tests on the JSON artefacts) |
| **Config file** | `pyproject.toml` (pytest section) |
| **Quick run command** | `uv run pytest -x -q` |
| **Full suite command** | `uv run pytest --cov=pipeline` |
| **Estimated runtime** | ~15 seconds (Polars + DuckDB in-memory fixtures) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -x -q` (quick)
- **After every plan wave:** Run `uv run pytest --cov=pipeline` (full)
- **Before `/gsd-verify-work`:** Full suite green + manual chart inspection at `localhost:3000/`
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

*Populated by planner. Each task must map to a pytest test ID or an explicit manual-verification row.*

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 1-01-01 | 01 | 1 | PIPE-01..04 | unit | `uv run pytest tests/test_store.py::test_schema` | ⬜ pending |
| 1-02-01 | 02 | 1 | PIPE-05, OPS-01..03 | unit | `uv run pytest tests/test_fetch.py` | ⬜ pending |
| 1-02-02 | 02 | 1 | PIPE-06, OPS-04 | unit | `uv run pytest tests/test_validate.py` | ⬜ pending |
| 1-03-01 | 03 | 2 | EDIT-01, EDIT-02 | integration | `npx @observablehq/framework build` exits 0 | ⬜ pending |
| 1-04-01 | 04 | 2 | CHART-01, PIPE-07 | data-contract | `uv run pytest tests/test_chart_model.py` | ⬜ pending |
| 1-05-01 | 05 | 3 | OPS-05 | manual | GitHub Actions dry-run succeeds | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — fixtures for tiny deterministic LCCC CSV slice (≤50 rows covering ≥2 technologies, ≥1 clawback row, ≥2 allocation rounds, IMRP+BMRP)
- [ ] `tests/fixtures/lccc_mini.csv` — committed reference dataset
- [ ] `tests/test_invariants.py` — stubs for: row-count monotonicity, CfD_Payments_GBP signed-sum tie-out, CF ≤ 1.0, non-null PK, reference-type consistency per unit
- [ ] `pyproject.toml` — add `pytest`, `pytest-cov`, `pandera[polars]`, `hypothesis` (optional) to dev deps

---

## Nyquist Invariants (from RESEARCH.md)

Every pipeline run must satisfy these contracts. Failure = loud build break, not silent stale-serve.

| Invariant | Check | Rationale |
|-----------|-------|-----------|
| **Schema stability** | All 13 columns present with expected dtypes (Pandera schema) | Upstream format change ⇒ fail build |
| **Row monotonicity** | `row_count(today) >= row_count(yesterday) - tolerance` | Detects truncated/partial downloads |
| **PK uniqueness** | `(Settlement_Date, CfD_ID)` unique after dedupe | Store integrity — verified Plan 01-01 |
| **Signed-sum tie-out** | `sum(CFD_Payments_GBP) == sum(positive) - sum(abs(negative))` within £1 | Catches sign-flip bugs (2022 clawback) |
| **CF bounds** | All capacity factors ∈ [0, 1.0] | Detects MWh/capacity unit errors |
| **Reference-type partition** | Every unit has a single `Reference_Type` over its lifetime | Catches aggregation mistakes |
| **Idempotency** | Running ingest twice produces identical DuckDB hash | Proves upsert correctness |
| **Date coverage** | `max(Settlement_Date)` within 7 days of today | Detects stalled upstream |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Chart visual legibility on mobile | CHART-01 | SVG layout judgment | Open `/` in Chrome devtools mobile mode (iPhone 12); confirm y-axis labels visible, no overflow |
| OG:image renders in social preview | EDIT-04 | Third-party caching | Paste deployed URL into `opengraph.xyz`; confirm PNG loads |
| Cron schedule fires on time | OPS-05 | GitHub Actions cron drift | Check Actions tab 48h after merge; confirm daily run succeeded |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (fixtures + pandera schema)
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
