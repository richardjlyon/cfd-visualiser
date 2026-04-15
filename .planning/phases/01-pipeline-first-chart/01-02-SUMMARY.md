---
phase: "01-pipeline-first-chart"
plan: "02"
subsystem: "pipeline"
tags: [pipeline, httpx, fetch, validation, healthchecks, tdd]

dependency_graph:
  requires:
    - "pipeline.schema.validate — Pandera schema from plan 01-01"
    - "pipeline.store.upsert — DuckDB upsert from plan 01-01"
    - "tests/conftest.py — shared fixtures from plan 01-01"
  provides:
    - "pipeline.fetch — httpx download with gzip archive and content guards"
    - "pipeline.validate — CSV reader + Pandera boundary (UTC-naive date-only)"
    - "pipeline.__main__ — CLI entry fetch->validate->upsert->healthcheck with 4 exit codes"
    - "pipeline/README.md — UTC-naive timezone convention documented"
  affects:
    - "Plan 01-05 (CI/deploy): invokes python -m pipeline as the build step"

tech_stack:
  added:
    - "httpx — already a declared dependency; HTTPTransport(retries=3) + timeout=60s"
    - "gzip (stdlib) — used for raw archive writes"
    - "pandera.errors.SchemaError — caught at validate boundary in __main__.py"
  patterns:
    - "Injected httpx.Client pattern: fetch() and run() accept client= for testability"
    - "MockTransport URL routing: single client handles both LCCC and HC URLs in tests"
    - "TDD: RED commit then GREEN commit per task (6 commits total)"
    - "Exit-code contract: 1=fetch, 2=schema-drift, 3=store, 4=healthcheck"
    - "DuckDB not touched if validate raises (schema drift halts before Step 3)"

key_files:
  created:
    - path: "pipeline/fetch.py"
      role: "LCCC CSV downloader with HTML guard, size guard, gzip archive (PIPE-01, PIPE-04)"
    - path: "pipeline/validate.py"
      role: "CSV reader + Pandera schema enforcement, UTC-naive date coercion (PIPE-02, PIPE-08)"
    - path: "pipeline/__main__.py"
      role: "CLI orchestrator: fetch->validate->upsert->healthcheck (PIPE-05)"
    - path: "pipeline/README.md"
      role: "UTC-naive timezone convention, exit codes, env vars, data flow diagram"
    - path: "tests/test_fetch.py"
      role: "5 tests: happy path CSV write, gzip archive, 500 error, HTML rejection, tiny body"
    - path: "tests/test_validate.py"
      role: "6 tests: valid CSV, Date dtype, extra column, unknown tech, missing column, no mutation"
    - path: "tests/test_pipeline_main.py"
      role: "5 tests: end-to-end happy path, fetch failure, schema drift, HC ping, HC skip"
  modified:
    - path: ".gitignore"
      role: "Added data/cfd.duckdb, data/cfd.duckdb.wal, data/latest.csv exclusions"

decisions:
  - "Injected httpx.Client used for HC ping in run() — same client handles LCCC and HC URLs in tests, routing by URL fragment in MockTransport handler"
  - "EXIT_SCHEMA_DRIFT=2 halts before any DuckDB file creation — confirmed by test_schema_drift_exits_2 asserting db_path does not exist"
  - "LCCC_URL pinned to dataset portal UUID path (not a named alias) — stable as long as dataset UUID doesn't change"
  - "validate.py delegates date coercion to schema.validate() which already handles the timestamp->Date slice — thin wrapper pattern"

metrics:
  duration: "~4 minutes"
  completed_date: "2026-04-15"
  tasks_completed: 3
  tasks_total: 3
  files_created: 7
  files_modified: 1
  test_count: 16
---

# Phase 1 Plan 02: Fetch, Validate, Archive Summary

**One-liner:** httpx fetcher with gzip archive and HTML/size content guards + Pandera validate boundary + four-exit-code CLI orchestrator backed by 16 TDD tests.

## What Was Built

Three modules complete the daily-runnable pipeline CLI:

- **pipeline/fetch.py** — Downloads LCCC CSV via httpx (retries=3, timeout=60s). Guards against HTML error pages (first-1024-byte scan) and truncated responses (<1 KB). Writes the raw CSV to `dest_csv` and a gzipped date-stamped snapshot to `raw_dir/YYYY-MM-DD.csv.gz`. Accepts an injected `httpx.Client` for testability.

- **pipeline/validate.py** — Reads the CSV with Polars (`infer_schema_length=10_000`), coerces `Settlement_Date` from LCCC's `YYYY-MM-DD 00:00:00.0000000` format to `pl.Date` (UTC-naive), then delegates to `pipeline.schema.validate`. Raises `pandera.errors.SchemaError` on any drift (extra column, unknown enum, missing required column).

- **pipeline/__main__.py** — `run()` orchestrates the four steps and returns a typed exit code:
  - 1 = fetch failed
  - 2 = schema drift (DuckDB NOT written)
  - 3 = store failed
  - 4 = healthcheck ping failed
  - `PIPELINE_HC_URL` env var gates the optional ping; omit in dev to skip entirely.

- **pipeline/README.md** — Documents the UTC-naive date-only convention, all exit codes, env vars, and the full data flow diagram.

## Exit-Code Contract

| Code | Meaning | DuckDB Written? |
|------|---------|-----------------|
| 0 | OK | Yes |
| 1 | Fetch failed (network, HTML, tiny body) | No |
| 2 | Schema drift (Pandera SchemaError) | No |
| 3 | Store failed (DuckDB write error) | Yes (attempted) |
| 4 | Healthcheck ping failed | Yes |

## MockTransport Pattern Used in Tests

All three test modules use `httpx.MockTransport` with a single URL-routing handler:

```python
def handler(request: httpx.Request) -> httpx.Response:
    if "lowcarboncontracts.uk" in str(request.url):
        return httpx.Response(200, content=lccc_body)
    if hc_url and str(request.url) == hc_url:
        hc_calls.append(str(request.url))
        return httpx.Response(200)
    return httpx.Response(404)
```

This avoids needing `respx` or other mocking libraries — the injected client handles all outbound HTTP in tests.

## Test Summary

| Module | Tests | Result |
|--------|-------|--------|
| test_fetch.py | 5 | PASS |
| test_validate.py | 6 | PASS |
| test_pipeline_main.py | 5 | PASS |
| **Plan total** | **16** | **PASS** |
| **Full suite** | **47** | **PASS** |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] HC ping uses injected client instead of bare httpx.get**
- **Found during:** Task 3
- **Issue:** The plan's `__main__.py` template called `httpx.get(hc_url)` directly for the healthcheck ping. This means the injected `client` mock doesn't intercept HC requests — `test_healthcheck_ping_issued` would fail because the HC call goes to a real URL.
- **Fix:** In `run()`, if `client is not None`, use `client.get(hc_url)` instead of `httpx.get(hc_url)`. Production behaviour (no injected client) falls back to `httpx.get()`.
- **Files modified:** pipeline/__main__.py
- **Commit:** 54396b3

## Known Stubs

None. All modules are fully implemented with no placeholder values or TODO comments.

## Threat Flags

No new threat surface beyond the plan's threat model. All T-01-02-* mitigations are implemented:
- T-01-02-01: HTML guard + size guard + raise_for_status in fetch.py
- T-01-02-02: timeout=60s, retries=3, MIN_BYTES guard in fetch.py
- T-01-02-03: HC URL read from env var only, never logged in full
- T-01-02-04: Pandera strict=True in schema.py (pre-existing); validate.py is the ingest boundary
- T-01-02-05: URL pinned to LCCC dataset portal UUID; TLS via httpx default

## TDD Gate Compliance

- Task 1 RED gate: commit `0db9bf8` — `test(01-02): add failing tests for fetch.py (RED phase)`
- Task 1 GREEN gate: commit `7074340` — `feat(01-02): implement pipeline/fetch.py...`
- Task 2 RED gate: commit `fd3f001` — `test(01-02): add failing tests for validate.py (RED phase)`
- Task 2 GREEN gate: commit `d2d88ce` — `feat(01-02): implement pipeline/validate.py...`
- Task 3 RED gate: commit `41e6bfc` — `test(01-02): add failing tests for pipeline/__main__.py (RED phase)`
- Task 3 GREEN gate: commit `54396b3` — `feat(01-02): implement pipeline/__main__.py CLI and README (PIPE-05)`

## Self-Check: PASSED

Files verified present:
- pipeline/fetch.py: FOUND
- pipeline/validate.py: FOUND
- pipeline/__main__.py: FOUND
- pipeline/README.md: FOUND
- tests/test_fetch.py: FOUND
- tests/test_validate.py: FOUND
- tests/test_pipeline_main.py: FOUND

Commits verified in git log:
- 0db9bf8: FOUND (test RED fetch)
- 7074340: FOUND (feat fetch)
- fd3f001: FOUND (test RED validate)
- d2d88ce: FOUND (feat validate)
- 41e6bfc: FOUND (test RED main)
- 54396b3: FOUND (feat main)
