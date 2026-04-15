---
phase: "01-pipeline-first-chart"
plan: "01"
subsystem: "pipeline"
tags: [pipeline, duckdb, polars, pandera, testing, units, schema, store]

dependency_graph:
  requires: []
  provides:
    - "pipeline.units — named unit constants (GBP_M, GBP_BN, MWH_PER_GWH, etc.)"
    - "pipeline.schema — Pandera DataFrameSchema strict=True for LCCC CSV"
    - "pipeline.store — idempotent DuckDB upsert on (Settlement_Date, CfD_ID)"
    - "tests/conftest.py — shared pytest fixtures for all downstream plans"
    - "tests/fixtures/cfd_sample.csv — 1109-row stratified fixture"
  affects: []

tech_stack:
  added:
    - "polars==1.39.3 — CSV ingest and DataFrame operations"
    - "duckdb==1.5.2 — analytical store with DATE primary key"
    - "pandera[polars]==0.31.1 — schema validation with strict=True"
    - "httpx>=0.28.1 — HTTP client (for downstream fetcher plan)"
    - "pyarrow==23.0.1 — Arrow bridge between Polars and DuckDB"
    - "pytest==9.0.3, pytest-cov==7.1.0 — test framework"
  patterns:
    - "Polars read_csv -> Pandera validate -> DuckDB Arrow register -> upsert"
    - "pl.Date dtype (not Datetime) enforced at schema boundary (PIPE-08)"
    - "INSERT ... ON CONFLICT (Settlement_Date, CfD_ID) DO UPDATE SET for idempotency"
    - "Column allowlist _VALUE_COLS prevents SQL injection at trust boundary (T-01-01-02)"

key_files:
  created:
    - path: "pipeline/__init__.py"
      role: "Package init with __version__"
    - path: "pipeline/units.py"
      role: "Named unit constants and conversion helpers (PIPE-07)"
    - path: "pipeline/schema.py"
      role: "Pandera DataFrameSchema strict=True with validate() helper (PIPE-02, PIPE-08)"
    - path: "pipeline/store.py"
      role: "Idempotent DuckDB upsert function (PIPE-03)"
    - path: "tests/conftest.py"
      role: "Shared pytest fixtures: sample_csv_path, fresh_duckdb, mock_lccc_response"
    - path: "tests/fixtures/cfd_sample.csv"
      role: "1109-row stratified fixture covering all 11 technology/round combos"
    - path: "tests/test_units.py"
      role: "7 tests for unit constants and conversion helpers"
    - path: "tests/test_schema.py"
      role: "9 tests for Pandera schema validation"
    - path: "tests/test_store.py"
      role: "5 tests for DuckDB upsert idempotency and conflict behavior"
    - path: "pyproject.toml"
      role: "Project config with dev dependencies and pytest settings"
  modified: []

decisions:
  - "CfD_ID regex broadened to r'^[A-Z0-9]{2,4}-[A-Z0-9]{3}-\\d+$' (plan had r'^[A-Z0-9]{3,4}-[A-Z]{3}-\\d+$') — observed ID AAA-K3C-180 has digit in second segment"
  - "Weighted_IMRP_GBP_Per_MWh is nullable=True — 146 nulls in fixture (BMRP rows don't receive IMRP weighting)"
  - "Fixture reference year changed from 2023 to 2026 — stratified sample biased toward recent dates gives only 1 row in 2023 vs 978 rows in 2026"
  - "RESEARCH Open Q2 RESOLVED: CfD_ID <-> Name_of_CfD_Unit confirmed 1:1 on fixture (test_cfd_id_name_one_to_one passes)"

metrics:
  duration: "~25 minutes"
  completed_date: "2026-04-15"
  tasks_completed: 4
  tasks_total: 4
  files_created: 10
  files_modified: 0
  test_count: 21
---

# Phase 1 Plan 01: Store, Schema, and Units Summary

**One-liner:** Pandera strict schema + Polars/DuckDB idempotent upsert with DATE primary key, backed by a 1109-row stratified fixture covering all enum combinations and 2022 clawback rows.

## What Was Built

Four Python modules form the data-layer foundation for all Phase 1 plans:

- **pipeline/units.py** — Named constants (`GBP_M = 1e6`, `GBP_BN = 1e9`, `MWH_PER_GWH = 1000`) and conversion helpers. Importers grep for these symbols; magic number drift is caught at review time.

- **pipeline/schema.py** — Pandera `DataFrameSchema(strict=True)` covering all 13 LCCC CSV columns. Enum sets (`TECHNOLOGIES`, `ROUNDS`, `REFERENCE_TYPES`) are frozen sets of exact LCCC values. `validate()` helper converts the `YYYY-MM-DD 00:00:00.0000000` timestamp string to `pl.Date` before validating (PIPE-08).

- **pipeline/store.py** — `upsert(df, db_path)` runs `validate()` then registers the Arrow table in DuckDB and executes `INSERT ... ON CONFLICT (Settlement_Date, CfD_ID) DO UPDATE SET ...` with an explicit column allowlist (T-01-01-02 security mitigation). Returns table row count.

- **tests/** — `conftest.py` provides `sample_csv_path`, `fresh_duckdb`, and `mock_lccc_response` fixtures. `tests/fixtures/cfd_sample.csv` is a 1109-row stratified sample (100 rows per technology/round combination, sorted by date descending) with forced inclusion of 2022 clawback rows and BMRP rows.

## Schema Enum Sets

| Enum | Values |
|------|--------|
| `TECHNOLOGIES` | Offshore Wind, Onshore Wind, Solar PV, Biomass Conversion, Energy from Waste, Dedicated Biomass, Advanced Conversion Technology |
| `ROUNDS` | Allocation Round 1, Allocation Round 2, Allocation Round 4, Allocation Round 5, Investment Contract |
| `REFERENCE_TYPES` | IMRP, BMRP |

Note: "Allocation Round 3" is intentionally absent — AR3 was postponed/cancelled.

## PK Choice Verification (RESEARCH Open Q1 / A1)

Primary key `(Settlement_Date, CfD_ID)` confirmed by idempotency test. Running `upsert` twice against the same input produces identical `COUNT(*)`, `SUM(CFD_Generation_MWh)`, and `SUM(CFD_Payments_GBP)`.

## CfD_ID ↔ Name_of_CfD_Unit 1:1 Mapping (RESEARCH Open Q2)

`test_cfd_id_name_one_to_one` confirms the relationship is strictly 1:1 on the committed fixture. Both directions checked: each `CfD_ID` has exactly one `Name_of_CfD_Unit`, and each name maps back to exactly one ID.

## Test Summary

| Module | Tests | Result |
|--------|-------|--------|
| test_units.py | 7 | PASS |
| test_schema.py | 9 | PASS |
| test_store.py | 5 | PASS |
| **Total** | **21** | **PASS** |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CfD_ID regex broadened to cover alphanumeric second segment**
- **Found during:** Task 3
- **Issue:** Plan specified `r"^[A-Z0-9]{3,4}-[A-Z]{3}-\d+$"` (second segment letters only), but observed ID `AAA-K3C-180` has a digit in the second segment
- **Fix:** Changed to `r"^[A-Z0-9]{2,4}-[A-Z0-9]{3}-\d+$"` to match all 67 observed IDs
- **Files modified:** pipeline/schema.py
- **Commit:** 0c99043

**2. [Rule 2 - Missing critical functionality] Weighted_IMRP_GBP_Per_MWh nullable**
- **Found during:** Task 3
- **Issue:** BMRP rows have no IMRP weighting value — 146 nulls in fixture (plan omitted nullable annotation)
- **Fix:** Added `nullable=True` to `Weighted_IMRP_GBP_Per_MWh` column in schema
- **Files modified:** pipeline/schema.py
- **Commit:** 0c99043

**3. [Rule 1 - Bug] Fixture reference year changed from 2023 to 2026**
- **Found during:** Task 2
- **Issue:** Stratified sample sorts by Settlement_Date descending (100 rows per combo), yielding 978 rows in 2026 but only 1 row in 2023. The plan's `EXPECTED_2023_MWH` assertion would be essentially meaningless (1 row, ~7000 MWh).
- **Fix:** Changed reference year to 2026 (`EXPECTED_2026_MWH = 2665955.984`) with ±0.01% tolerance. Comment in test explains the design decision.
- **Files modified:** tests/test_units.py
- **Commit:** ccad2d3

## Known Stubs

None. All modules are fully implemented with no placeholder values.

## Threat Flags

No new threat surface beyond what is documented in the plan's threat model.

## Self-Check: PASSED

All files exist and commits are present in git log.
