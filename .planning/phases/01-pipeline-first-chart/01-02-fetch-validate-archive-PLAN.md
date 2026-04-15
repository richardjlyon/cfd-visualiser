---
phase: 01-pipeline-first-chart
plan: 02
type: execute
wave: 2
depends_on: ["01-01"]
files_modified:
  - pipeline/fetch.py
  - pipeline/validate.py
  - pipeline/__main__.py
  - pipeline/README.md
  - tests/test_fetch.py
  - tests/test_validate.py
  - tests/test_pipeline_main.py
  - .gitignore
autonomous: true
requirements: [PIPE-01, PIPE-04, PIPE-05, PIPE-08]
tags: [pipeline, httpx, fetch, validation, healthchecks]

must_haves:
  truths:
    - "Running `python -m pipeline` end-to-end on a mock LCCC response downloads, archives, validates, and upserts in that exact order — and exits non-zero if any step fails"
    - "The daily CSV is archived as a gzipped snapshot at data/raw/YYYY-MM-DD.csv.gz"
    - "A schema drift (column rename, added column, unknown enum) causes the pipeline to exit non-zero and NOT write to data/cfd.duckdb"
    - "On successful completion the pipeline pings a Healthchecks URL if PIPELINE_HC_URL env var is set, and silently skips the ping if unset"
    - "Settlement_Date is parsed as date-only at the fetch/validate boundary; no datetime objects propagate downstream"
    - "The timezone convention is documented in pipeline/README.md as UTC-naive date-only"
  artifacts:
    - path: "pipeline/fetch.py"
      provides: "fetch(dest_csv, raw_dir) -> Path using httpx with retries + gzip archive"
      contains: "httpx.Client"
    - path: "pipeline/validate.py"
      provides: "read_and_validate(csv_path) -> polars.DataFrame; exits non-zero on drift"
      contains: "from pipeline.schema import validate"
    - path: "pipeline/__main__.py"
      provides: "CLI entry: fetch -> validate -> store -> healthcheck ping"
      contains: "if __name__ == "
    - path: "pipeline/README.md"
      provides: "Documented timezone convention + CLI usage"
      contains: "UTC-naive"
    - path: "tests/test_fetch.py"
      provides: "Mocked-httpx fetch test + archive test"
    - path: "tests/test_validate.py"
      provides: "Drift detection tests (exit code 1 on bad CSV)"
    - path: "tests/test_pipeline_main.py"
      provides: "End-to-end dry-run test using respx/httpx mock"
  key_links:
    - from: "pipeline/__main__.py"
      to: "pipeline.fetch"
      via: "import and call"
      pattern: "from pipeline.fetch import"
    - from: "pipeline/__main__.py"
      to: "pipeline.validate"
      via: "import and call"
      pattern: "from pipeline.validate import"
    - from: "pipeline/__main__.py"
      to: "pipeline.store.upsert"
      via: "import and call"
      pattern: "from pipeline.store import"
    - from: "pipeline/fetch.py"
      to: "data/raw/"
      via: "gzip.open write"
      pattern: "gzip\\.open"
---

<objective>
Fetch the LCCC CSV daily, archive it gzipped, validate it against the Pandera schema, upsert into DuckDB, and ping a dead-man's switch — all via `python -m pipeline`. Wire the four steps so a schema drift halts the pipeline non-zero and the previous `data/cfd.duckdb` is left untouched.

Purpose: Plan 01-01 produced contracts; this plan produces the daily-runnable pipeline. Every downstream plan (chart builder, site, cron) invokes `python -m pipeline` — this is the load-bearing CLI seam.

Output: `pipeline/{fetch,validate,__main__}.py`, `pipeline/README.md`, three test modules, `.gitignore` updated.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/phases/01-pipeline-first-chart/01-RESEARCH.md
@.planning/phases/01-pipeline-first-chart/01-VALIDATION.md
@.planning/phases/01-pipeline-first-chart/01-01-SUMMARY.md
@pipeline/schema.py
@pipeline/store.py
@pipeline/units.py

<interfaces>
<!-- Reused from Plan 01-01 -->

```python
# pipeline/schema.py
from pipeline.schema import validate  # polars.DataFrame -> polars.DataFrame (raises pandera.errors.SchemaError)

# pipeline/store.py
from pipeline.store import upsert  # (df, db_path) -> int row count
```

<!-- New contracts this plan creates -->

```python
# pipeline/fetch.py
LCCC_URL: str  # pinned official CSV URL
def fetch(dest_csv: Path, raw_dir: Path, *, client: httpx.Client | None = None) -> Path: ...
# - Downloads LCCC_URL to dest_csv
# - Writes gzipped copy to raw_dir / f"{today_iso}.csv.gz"
# - Raises httpx.HTTPError on non-2xx or timeout after retries
# - client parameter enables injection for tests

# pipeline/validate.py
def read_and_validate(csv_path: Path) -> "polars.DataFrame": ...
# - Reads CSV with Polars, coerces Settlement_Date to Date
# - Calls pipeline.schema.validate
# - Raises pandera.errors.SchemaError on drift
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: pipeline/fetch.py with httpx + gzip archive and test_fetch.py (PIPE-01, PIPE-04)</name>
  <files>pipeline/fetch.py, tests/test_fetch.py, .gitignore</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (fetch.py example lines 500-525; Pitfall 7 raw archive growth)
    - pipeline/__init__.py
    - tests/conftest.py (mock_lccc_response fixture already exists)
  </read_first>
  <behavior>
    - `fetch(dest, raw_dir, client=mock_client)` writes `dest` with the mock response bytes
    - After fetch, `raw_dir / f"{today}.csv.gz"` exists and, when gunzipped, equals the bytes written to `dest`
    - fetch raises `httpx.HTTPError` when the mock returns status 500 (after retries)
    - fetch raises `ValueError` if the response content-type is obviously wrong (HTML instead of CSV) — detected via presence of `<html` in first 1024 bytes
    - fetch raises `ValueError` if response body is smaller than 1 KB (catches truncated/empty downloads)
    - Default LCCC_URL constant equals the URL from CLAUDE.md / RESEARCH.md
  </behavior>
  <action>
    1. Create `pipeline/fetch.py`:
       ```python
       """Daily LCCC CSV fetch with gzip archive (PIPE-01, PIPE-04)."""
       from __future__ import annotations
       import datetime as dt
       import gzip
       from pathlib import Path
       import httpx

       LCCC_URL: str = (
           "https://dp.lowcarboncontracts.uk/dataset/"
           "8e8ca0d5-c774-4dc8-a079-347f1c180c0f/resource/"
           "5279a55d-4996-4b1e-ba07-f411d8fd31f0/download/"
           "actual_cfd_generation_and_avoided_ghg_emissions.csv"
       )

       MIN_BYTES = 1024  # < 1 KB is definitely a truncated/empty response

       def fetch(
           dest_csv: Path,
           raw_dir: Path,
           *,
           client: httpx.Client | None = None,
           url: str = LCCC_URL,
           today: dt.date | None = None,
       ) -> Path:
           owns_client = client is None
           if client is None:
               transport = httpx.HTTPTransport(retries=3)
               client = httpx.Client(
                   transport=transport, timeout=60.0, follow_redirects=True
               )
           try:
               r = client.get(url)
               r.raise_for_status()
               body = r.content
           finally:
               if owns_client:
                   client.close()

           if len(body) < MIN_BYTES:
               raise ValueError(
                   f"LCCC response too small ({len(body)} bytes); "
                   f"expected >= {MIN_BYTES}"
               )
           head = body[:1024].lower()
           if b"<html" in head or b"<!doctype html" in head:
               raise ValueError(
                   "LCCC response looks like HTML (not CSV) — upstream error page?"
               )

           dest_csv.parent.mkdir(parents=True, exist_ok=True)
           dest_csv.write_bytes(body)

           raw_dir.mkdir(parents=True, exist_ok=True)
           stamp = (today or dt.date.today()).isoformat()
           archive = raw_dir / f"{stamp}.csv.gz"
           with gzip.open(archive, "wb") as dst:
               dst.write(body)
           return dest_csv
       ```
    2. Create `tests/test_fetch.py`:
       - Use `httpx.MockTransport` to build a test `httpx.Client` that returns the `mock_lccc_response` fixture bytes with status 200.
       - `test_fetch_writes_csv`: call `fetch(dest, raw_dir, client=mock)`; assert `dest.read_bytes() == mock_lccc_response`.
       - `test_fetch_writes_gzip_archive`: assert `raw_dir/f"{today}.csv.gz"` exists; gunzip and assert content equals original bytes.
       - `test_fetch_raises_on_500`: MockTransport returns 500; expect `httpx.HTTPError`.
       - `test_fetch_raises_on_html_response`: MockTransport returns 200 with `<html>` body; expect `ValueError` matching `HTML`.
       - `test_fetch_raises_on_tiny_body`: MockTransport returns 200 with 100-byte body; expect `ValueError` matching `too small`.
       - Pass `today=dt.date(2024, 1, 15)` for deterministic archive filename.
    3. Append to `.gitignore`:
       ```
       # Daily pipeline artefacts
       data/cfd.duckdb
       data/cfd.duckdb.wal
       # Intermediate uncompressed fetches (archives stay under data/raw/*.csv.gz)
       data/latest.csv
       ```
  </action>
  <verify>
    <automated>uv run pytest tests/test_fetch.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_fetch.py -x -q` exits 0
    - `grep -q "LCCC_URL" pipeline/fetch.py` succeeds
    - `grep -q "gzip.open" pipeline/fetch.py` succeeds
    - `grep -q "<html" pipeline/fetch.py` succeeds
    - Test file defines at least 5 test functions
    - `grep -q "data/cfd.duckdb" .gitignore` succeeds
  </acceptance_criteria>
  <done>
    Fetcher downloads, archives, and surfaces upstream errors loudly (PIPE-01 + PIPE-04).
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: pipeline/validate.py + test_validate.py (PIPE-02 loud-fail boundary, PIPE-08 date-only)</name>
  <files>pipeline/validate.py, tests/test_validate.py</files>
  <read_first>
    - pipeline/schema.py
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (Pitfall 1 silent schema drift; Pitfall 6 timezone)
    - tests/fixtures/cfd_sample.csv
  </read_first>
  <behavior>
    - `read_and_validate(valid_csv_path)` returns a `polars.DataFrame` with 13 columns
    - After validation, the returned `Settlement_Date` column has dtype `polars.Date` (not Datetime, not Utf8) — PIPE-08
    - Given a CSV with an extra column "Foo", `read_and_validate` raises `pandera.errors.SchemaError`
    - Given a CSV with `Technology="UnknownTech"` in one row, raises `pandera.errors.SchemaError`
    - Given a CSV missing the `CfD_ID` column, raises a schema error before any row-level check
    - `read_and_validate` does NOT mutate the input file
  </behavior>
  <action>
    1. Create `pipeline/validate.py`:
       ```python
       """Read LCCC CSV and apply Pandera schema (PIPE-02, PIPE-08).

       Timezone convention: Settlement_Date is treated as UTC-naive date-only.
       The raw CSV uses `YYYY-MM-DD 00:00:00.0000000` timestamp literals; we
       slice to the first 10 characters and parse as polars.Date. No time
       component survives this function.
       """
       from __future__ import annotations
       from pathlib import Path
       import polars as pl
       from pipeline.schema import validate as _schema_validate

       def read_and_validate(csv_path: Path) -> pl.DataFrame:
           df = pl.read_csv(csv_path, infer_schema_length=10_000)
           if df["Settlement_Date"].dtype == pl.Utf8:
               df = df.with_columns(
                   pl.col("Settlement_Date")
                     .str.slice(0, 10)
                     .str.to_date("%Y-%m-%d")
               )
           return _schema_validate(df)
       ```
    2. Create `tests/test_validate.py`:
       - `test_valid_csv_returns_dataframe(sample_csv_path)`: assert returned object is `pl.DataFrame`, column count == 13.
       - `test_settlement_date_is_polars_date(sample_csv_path)`: assert `df["Settlement_Date"].dtype == pl.Date`.
       - `test_extra_column_fails(tmp_path, sample_csv_path)`: copy fixture, append an extra `,99` column header and row, expect `pandera.errors.SchemaError`.
       - `test_unknown_technology_fails(tmp_path, sample_csv_path)`: read fixture with Polars, mutate one row's Technology to "UnknownTech", write CSV to tmp_path, expect `SchemaError`.
       - `test_missing_column_fails(tmp_path, sample_csv_path)`: produce CSV without `CfD_ID` column, expect schema error.
       - `test_file_not_mutated(sample_csv_path)`: hash fixture before and after — assert unchanged.
  </action>
  <verify>
    <automated>uv run pytest tests/test_validate.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_validate.py -x -q` exits 0
    - `grep -q "from pipeline.schema import" pipeline/validate.py` succeeds
    - `grep -q "pl.Date" pipeline/validate.py` succeeds
    - `grep -q "str.slice(0, 10)" pipeline/validate.py` succeeds (date-only enforcement)
    - Test file defines at least 6 test functions covering behavior bullets
  </acceptance_criteria>
  <done>
    Validator is the single ingest-boundary contract for schema + date-only; all drift types raise.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: pipeline/__main__.py CLI + Healthchecks ping + timezone README + end-to-end test (PIPE-05)</name>
  <files>pipeline/__main__.py, pipeline/README.md, tests/test_pipeline_main.py</files>
  <read_first>
    - pipeline/fetch.py
    - pipeline/validate.py
    - pipeline/store.py
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (GitHub Actions workflow skeleton lines 527-565; Healthchecks section)
  </read_first>
  <behavior>
    - `python -m pipeline` with a mocked httpx client runs fetch -> validate -> upsert in order
    - When `PIPELINE_HC_URL` env var is set to a mock URL, the CLI issues a GET to that URL after successful upsert
    - When `PIPELINE_HC_URL` is unset, the CLI completes successfully without any HC call
    - When fetch raises, the CLI exits with code 1 and the DuckDB file is NOT created (or is unchanged)
    - When validate raises a SchemaError, the CLI exits with code 2 and DuckDB file is unchanged
    - Standard data paths default to `data/latest.csv`, `data/raw/`, `data/cfd.duckdb` relative to cwd (overridable via env)
  </behavior>
  <action>
    1. Create `pipeline/__main__.py`:
       ```python
       """CLI entry: fetch -> validate -> store -> healthcheck (PIPE-01..05)."""
       from __future__ import annotations
       import os
       import sys
       from pathlib import Path
       import httpx
       import pandera.errors
       from pipeline.fetch import fetch
       from pipeline.validate import read_and_validate
       from pipeline.store import upsert

       EXIT_FETCH_FAILED = 1
       EXIT_SCHEMA_DRIFT = 2
       EXIT_STORE_FAILED = 3
       EXIT_HEALTHCHECK_FAILED = 4

       def run(
           *,
           latest_csv: Path = Path("data/latest.csv"),
           raw_dir: Path = Path("data/raw"),
           db_path: Path = Path("data/cfd.duckdb"),
           client: httpx.Client | None = None,
           hc_url: str | None = None,
       ) -> int:
           hc_url = hc_url if hc_url is not None else os.environ.get("PIPELINE_HC_URL")
           try:
               fetch(latest_csv, raw_dir, client=client)
           except Exception as e:
               print(f"ERROR: fetch failed: {e}", file=sys.stderr)
               return EXIT_FETCH_FAILED
           try:
               df = read_and_validate(latest_csv)
           except pandera.errors.SchemaError as e:
               print(f"ERROR: schema drift detected: {e}", file=sys.stderr)
               return EXIT_SCHEMA_DRIFT
           try:
               rows = upsert(df, db_path)
               print(f"ok: {rows} rows in raw_generation")
           except Exception as e:
               print(f"ERROR: store failed: {e}", file=sys.stderr)
               return EXIT_STORE_FAILED
           if hc_url:
               try:
                   httpx.get(hc_url, timeout=10.0).raise_for_status()
                   print(f"ok: healthcheck pinged {hc_url}")
               except Exception as e:
                   print(f"WARN: healthcheck ping failed: {e}", file=sys.stderr)
                   return EXIT_HEALTHCHECK_FAILED
           return 0

       if __name__ == "__main__":
           sys.exit(run())
       ```
    2. Create `pipeline/README.md`:
       ```markdown
       # Pipeline

       Daily ingest: fetch -> validate -> upsert -> healthcheck.

       ## Usage

       ```
       uv run python -m pipeline
       ```

       Exit codes:
       - 0 OK
       - 1 fetch failed (network, HTML response, truncated body)
       - 2 schema drift (Pandera SchemaError — does NOT write to DuckDB)
       - 3 store failed (DuckDB write error)
       - 4 healthcheck ping failed (store completed successfully)

       ## Timezone convention (PIPE-08)

       `Settlement_Date` is treated as **UTC-naive date-only** throughout the
       pipeline. The raw CSV uses timestamp literals ending in
       `00:00:00.0000000`; we slice off the time component at the validate
       boundary and store as DuckDB `DATE`. No `datetime` or tz-aware objects
       propagate downstream. Any future external price series (ETS, DEFRA SCC)
       must be normalised to the same date-only convention before join.

       ## Environment variables

       - `PIPELINE_HC_URL` (optional): Healthchecks.io ping URL; omitted in dev.
       ```
    3. Create `tests/test_pipeline_main.py`:
       - `test_end_to_end_happy_path(tmp_path, mock_lccc_response)`: build MockTransport returning fixture bytes; call `run(latest_csv=tmp_path/"latest.csv", raw_dir=tmp_path/"raw", db_path=tmp_path/"cfd.duckdb", client=mock_client)`; assert return 0 and DuckDB file exists with >= 800 rows.
       - `test_fetch_failure_exits_1(tmp_path)`: MockTransport returns 500; assert run returns 1; assert DuckDB file was NOT created.
       - `test_schema_drift_exits_2(tmp_path)`: MockTransport returns a CSV with an extra column; assert run returns 2; assert DuckDB NOT created.
       - `test_healthcheck_ping_issued(tmp_path, mock_lccc_response)`: MockTransport serves both LCCC and HC URL; pass `hc_url="http://hc.test/abc"`; assert HC URL was called exactly once. Use a transport router or two mocks composed.
       - `test_healthcheck_skipped_when_unset(tmp_path, mock_lccc_response, monkeypatch)`: monkeypatch.delenv("PIPELINE_HC_URL", raising=False); assert run returns 0 without any HC call.
  </action>
  <verify>
    <automated>uv run pytest tests/ -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_pipeline_main.py -x -q` exits 0
    - Full phase suite still green: `uv run pytest tests/ -x -q` exits 0
    - `grep -q "EXIT_SCHEMA_DRIFT = 2" pipeline/__main__.py` succeeds
    - `grep -q "PIPELINE_HC_URL" pipeline/__main__.py` succeeds
    - `grep -q "UTC-naive date-only" pipeline/README.md` succeeds
    - `grep -q "Exit codes" pipeline/README.md` succeeds
    - `uv run python -m pipeline --help 2>&1 || true` does not crash the process (no-arg exit is acceptable; just verifies importable)
  </acceptance_criteria>
  <done>
    `python -m pipeline` is the single CLI seam; all four loud-failure modes covered by tests.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| internet -> pipeline.fetch | Untrusted LCCC response body — must be content-type and size guarded |
| pipeline -> filesystem | Writes to data/ and data/raw/ — controlled paths, no user input in filename |
| pipeline -> Healthchecks.io | HC URL is a secret from env; outbound only |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-02-01 | Tampering | pipeline/fetch.py | mitigate | HTML-body guard + min-size guard + httpx `raise_for_status` + Pandera boundary downstream |
| T-01-02-02 | Denial of Service | pipeline/fetch.py | mitigate | httpx timeout=60s, retries=3 bounded; MIN_BYTES guard catches empty replies |
| T-01-02-03 | Information Disclosure | PIPELINE_HC_URL | mitigate | Env var only (never logged in full on failure); not committed to repo |
| T-01-02-04 | Tampering | pipeline/validate.py | mitigate | Pandera strict=True; schema drift exits non-zero before any write |
| T-01-02-05 | Spoofing | LCCC URL | accept | URL pinned to dataset portal; TLS via httpx default; no auth required for public dataset |
</threat_model>

<verification>
- `uv run pytest tests/ -x -q` exits 0
- `uv run python -c "from pipeline import fetch, validate, store; from pipeline.__main__ import run; print('ok')"` prints `ok`
- `grep -q "UTC-naive" pipeline/README.md` succeeds
- Schema drift test proves DuckDB is not touched on failure
</verification>

<success_criteria>
- `python -m pipeline` runs end-to-end with a mocked transport
- Fetch raises on HTML, tiny body, and 5xx; archive always gzipped
- Schema drift exits code 2 without writing to DuckDB
- Healthchecks ping fires only when `PIPELINE_HC_URL` is set
- Timezone convention documented in pipeline/README.md
</success_criteria>

<output>
After completion, create `.planning/phases/01-pipeline-first-chart/01-02-SUMMARY.md` documenting: CLI exit-code contract, mock-transport pattern used in tests, any changes to LCCC URL discovered during implementation.
</output>
