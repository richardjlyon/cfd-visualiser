---
phase: 01-pipeline-first-chart
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pyproject.toml
  - pipeline/__init__.py
  - pipeline/units.py
  - pipeline/schema.py
  - pipeline/store.py
  - tests/conftest.py
  - tests/fixtures/cfd_sample.csv
  - tests/test_units.py
  - tests/test_schema.py
  - tests/test_store.py
autonomous: true
requirements: [PIPE-02, PIPE-03, PIPE-07, PIPE-08]
tags: [pipeline, duckdb, polars, pandera, testing]

must_haves:
  truths:
    - "A Pandera schema rejects a CSV with a missing, renamed, or unknown-enum column and passes on the committed reference CSV"
    - "Running the Polars -> DuckDB upsert twice against the same input produces identical aggregate sums for every year"
    - "Unit constants (GBP_M, GBP_BN, MWH, GWH, TCO2E) round-trip correctly and a fixture asserts a known 2023 total generation value"
    - "Settlement_Date is stored as DuckDB DATE (not TIMESTAMP) and a test proves no time component survives ingest"
  artifacts:
    - path: "pipeline/units.py"
      provides: "Named unit constants (GBP, GBP_M, GBP_BN, MWH, GWH, TCO2E) with conversion helpers"
      contains: "GBP_PER_MWH"
    - path: "pipeline/schema.py"
      provides: "Pandera DataFrameSchema for LCCC CSV with strict=True"
      contains: "strict=True"
    - path: "pipeline/store.py"
      provides: "upsert(df, db_path) using INSERT ... ON CONFLICT on (Settlement_Date, CfD_ID)"
      contains: "ON CONFLICT"
    - path: "tests/conftest.py"
      provides: "Shared pytest fixtures: sample CSV path, fresh DuckDB tmpdir, mock httpx"
    - path: "tests/fixtures/cfd_sample.csv"
      provides: "Stratified 1000-row subset of LCCC data (all Allocation_round x Technology combos)"
    - path: "tests/test_units.py"
      provides: "Unit-constant correctness tests"
    - path: "tests/test_schema.py"
      provides: "Pandera schema tests: valid accept, column drift fail, unknown enum fail, date-only parse"
    - path: "tests/test_store.py"
      provides: "Idempotency test (run-twice-identical), update-on-conflict test"
  key_links:
    - from: "pipeline/store.py"
      to: "pipeline/schema.py"
      via: "validates df before upsert"
      pattern: "from pipeline\\.schema import"
    - from: "tests/test_schema.py"
      to: "tests/fixtures/cfd_sample.csv"
      via: "Polars read_csv on fixture"
      pattern: "cfd_sample\\.csv"
---

<objective>
Lay the data-layer foundation: named units (PIPE-07), Pandera schema with strict=True (PIPE-02), idempotent DuckDB upsert on (Settlement_Date, CfD_ID) (PIPE-03), date-only timezone convention (PIPE-08), and the pytest harness (conftest + 1000-row fixture) every downstream plan will reuse.

Purpose: Every other plan in Phase 1 depends on a trustworthy store and schema. This plan produces the bedrock contracts and the fixtures that make Wave 0 real.

Output: `pipeline/{units,schema,store}.py`, `tests/conftest.py`, `tests/fixtures/cfd_sample.csv`, three test files, pyproject dev deps added.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/01-pipeline-first-chart/01-RESEARCH.md
@.planning/phases/01-pipeline-first-chart/01-VALIDATION.md
@data/actual_cfd_generation_and_avoided_ghg_emissions.csv
@pyproject.toml

<interfaces>
<!-- Contracts this plan establishes for downstream plans -->

```python
# pipeline/units.py
GBP: str = "GBP"
GBP_M: float = 1_000_000.0       # £ per £m
GBP_BN: float = 1_000_000_000.0  # £ per £bn
MWH: str = "MWh"
GWH: float = 1_000.0              # MWh per GWh
TCO2E: str = "tCO2e"
GBP_PER_MWH: str = "GBP/MWh"

def gbp_to_millions(value_gbp: float) -> float: ...
def gbp_to_billions(value_gbp: float) -> float: ...
def mwh_to_gwh(value_mwh: float) -> float: ...

# pipeline/schema.py
import pandera.polars as pa
schema: pa.DataFrameSchema  # strict=True, 13 columns, enum checks on Technology/Allocation_round/Reference_Type

# pipeline/store.py
def upsert(df: "polars.DataFrame", db_path: str) -> int: ...
# returns number of rows inserted-or-updated; creates raw_generation table if missing;
# PK = (Settlement_Date, CfD_ID); Settlement_Date column type is DATE (not TIMESTAMP).
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add dev deps and create fixture + conftest (Wave 0 scaffolding)</name>
  <files>pyproject.toml, tests/__init__.py, tests/conftest.py, tests/fixtures/cfd_sample.csv</files>
  <read_first>
    - pyproject.toml (existing contents — do not clobber)
    - data/actual_cfd_generation_and_avoided_ghg_emissions.csv (first 5 rows for column order)
    - .planning/phases/01-pipeline-first-chart/01-VALIDATION.md (Wave 0 Requirements section)
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (lines 600-715, Nyquist + Wave 0 Gaps)
  </read_first>
  <behavior>
    - `uv run pytest --collect-only` discovers tests/ directory with zero errors
    - conftest provides fixture `sample_csv_path` returning Path to cfd_sample.csv
    - conftest provides fixture `fresh_duckdb` yielding a tmp DuckDB path, cleans up after test
    - conftest provides fixture `mock_lccc_response` returning bytes of the sample CSV (for httpx mocking later)
    - `tests/fixtures/cfd_sample.csv` has >= 800 rows, <= 1200 rows, covers every Allocation_round value (Investment Contract, AR1, AR2, AR4, AR5), every Technology value, includes at least one 2022 row with negative CFD_Payments_GBP, includes both IMRP and BMRP
  </behavior>
  <action>
    1. Edit pyproject.toml: add `[dependency-groups]` section (or extend existing) with dev group containing `pytest>=9.0`, `pytest-cov>=5.0`, `polars>=1.39.3`, `duckdb>=1.5.2`, `pandera[polars]>=0.31.0`, `httpx>=0.28.1`, `pyarrow`. Run `uv sync` to update uv.lock.
    2. Add `[tool.pytest.ini_options]` section:
       ```toml
       [tool.pytest.ini_options]
       testpaths = ["tests"]
       addopts = "-x -q --strict-markers"
       markers = ["live: hits live LCCC URL; skip offline"]
       ```
    3. Create `tests/__init__.py` (empty).
    4. Generate `tests/fixtures/cfd_sample.csv` via a one-shot Python script (run inline, do not commit the script):
       - Read the full CSV with Polars.
       - Stratified sample: for each (Allocation_round, Technology) cell take up to 30 rows (ordered by Settlement_Date descending to bias recent).
       - Force-include 5 rows where year(Settlement_Date)==2022 AND CFD_Payments_GBP < 0.
       - Force-include 5 rows where Reference_Type=='BMRP'.
       - Write CSV in identical column order and same date format (`YYYY-MM-DD 00:00:00.0000000`) as source.
       - Expected final row count: ~900-1100.
    5. Create `tests/conftest.py`:
       ```python
       from pathlib import Path
       import pytest

       FIXTURES = Path(__file__).parent / "fixtures"

       @pytest.fixture
       def sample_csv_path() -> Path:
           return FIXTURES / "cfd_sample.csv"

       @pytest.fixture
       def fresh_duckdb(tmp_path: Path) -> Path:
           return tmp_path / "test.duckdb"

       @pytest.fixture
       def mock_lccc_response(sample_csv_path: Path) -> bytes:
           return sample_csv_path.read_bytes()
       ```
  </action>
  <verify>
    <automated>uv sync &amp;&amp; uv run pytest --collect-only tests/ 2&gt;&amp;1 | tail -5</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest --collect-only tests/` exits 0
    - `test -f tests/fixtures/cfd_sample.csv` succeeds
    - `wc -l tests/fixtures/cfd_sample.csv` reports between 800 and 1200
    - `grep -c "AR5" tests/fixtures/cfd_sample.csv` >= 1
    - `grep -c "BMRP" tests/fixtures/cfd_sample.csv` >= 5
    - `uv run python -c "import polars as pl; df=pl.read_csv('tests/fixtures/cfd_sample.csv'); assert df['CFD_Payments_GBP'].min() < 0"` exits 0
    - `grep -q 'pytest' pyproject.toml` succeeds
  </acceptance_criteria>
  <done>
    Dev deps installed; fixture CSV committed; conftest importable; pytest collects without errors.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: pipeline/units.py with constants + test_units.py covering PIPE-07</name>
  <files>pipeline/__init__.py, pipeline/units.py, tests/test_units.py</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (Pitfall 5 section, lines ~440-450)
    - tests/fixtures/cfd_sample.csv (spot-check actual values)
  </read_first>
  <behavior>
    - `gbp_to_millions(1_000_000) == 1.0` exact
    - `gbp_to_billions(1_500_000_000) == 1.5` exact
    - `mwh_to_gwh(2500) == 2.5` exact
    - Round-trip: `gbp_to_billions(gbp_to_millions_inverse(X)) == X` for X in {0, 1, 123.456, 1e9}
    - Fixture assertion: sum of CFD_Generation_MWh for year 2023 in cfd_sample.csv equals a stable reference constant within ±0.01%
  </behavior>
  <action>
    1. Create `pipeline/__init__.py` containing only: `__version__ = "0.1.0"`
    2. Create `pipeline/units.py`:
       ```python
       """Named unit constants for monetary and energy quantities (PIPE-07).

       Importers must use these symbols rather than string/float literals so unit
       drift is caught by grep and by the fixture tests in tests/test_units.py.
       """
       from __future__ import annotations

       # String labels (for column metadata, axis labels)
       GBP: str = "GBP"
       GBP_PER_MWH: str = "GBP/MWh"
       MWH: str = "MWh"
       GWH: str = "GWh"
       TCO2E: str = "tCO2e"

       # Scale factors (divide raw £/MWh figures by these to render larger units)
       GBP_M: float = 1_000_000.0
       GBP_BN: float = 1_000_000_000.0
       MWH_PER_GWH: float = 1_000.0

       def gbp_to_millions(value_gbp: float) -> float:
           return value_gbp / GBP_M

       def gbp_to_billions(value_gbp: float) -> float:
           return value_gbp / GBP_BN

       def mwh_to_gwh(value_mwh: float) -> float:
           return value_mwh / MWH_PER_GWH
       ```
    3. Create `tests/test_units.py` with tests covering the behavior list. For the 2023-total fixture assertion: compute the true value once via `uv run python -c "import polars as pl; df = pl.read_csv('tests/fixtures/cfd_sample.csv').with_columns(pl.col('Settlement_Date').str.slice(0,10).str.to_date()); print(df.filter(pl.col('Settlement_Date').dt.year() == 2023)['CFD_Generation_MWh'].sum())"` and hardcode as `EXPECTED_2023_MWH` with a ±0.01% tolerance. Convert to GWh via `mwh_to_gwh` and assert the GWh value equals `EXPECTED_2023_MWH / 1000` exactly.
  </action>
  <verify>
    <automated>uv run pytest tests/test_units.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_units.py -x -q` exits 0
    - `grep -q "GBP_M" pipeline/units.py` succeeds
    - `grep -q "MWH_PER_GWH" pipeline/units.py` succeeds
    - Test file includes at least 4 test functions: `test_gbp_to_millions`, `test_gbp_to_billions`, `test_mwh_to_gwh`, `test_2023_total_generation_gwh_matches_reference`
  </acceptance_criteria>
  <done>
    Unit constants defined and enforced by tests; fixture round-trip passes.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: pipeline/schema.py Pandera schema + test_schema.py covering PIPE-02 and PIPE-08</name>
  <files>pipeline/schema.py, tests/test_schema.py</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (Pattern 2 Pandera example lines 313-345; LCCC Data Schema table lines 125-150)
    - pipeline/units.py (just created)
    - tests/fixtures/cfd_sample.csv
  </read_first>
  <behavior>
    - `validate(sample_df)` returns the DataFrame unchanged when every row is conformant
    - Adding an extra unknown column "Foo" to the DataFrame raises `pandera.errors.SchemaError` (strict=True)
    - Renaming `Technology` to `technology` raises `SchemaError`
    - A row with `Technology="Wind"` (not in enum set) raises `SchemaError`
    - A row with `Reference_Type="XYZ"` raises `SchemaError`
    - After schema validation, `Settlement_Date` column dtype is `polars.Date` (not `Datetime`) — PIPE-08
    - A row with negative `CFD_Generation_MWh` raises `SchemaError`
    - `CFD_Payments_GBP` accepts negative values (clawback) without raising
    - `CfD_ID` ↔ `Name_of_CfD_Unit` is 1:1 on the committed fixture (resolves RESEARCH Open Q2): for every distinct `CfD_ID` there is exactly one `Name_of_CfD_Unit`, and vice versa
  </behavior>
  <action>
    1. Create `pipeline/schema.py`:
       - Define `TECHNOLOGIES`, `ROUNDS`, `REFERENCE_TYPES` as frozen sets using the exact enum values documented in RESEARCH.md (copy verbatim — do not paraphrase).
       - Build `schema: pa.DataFrameSchema` with `strict=True` covering all 13 columns from the LCCC schema table.
       - `Settlement_Date` column: `pa.Column(pl.Date, ...)` — use polars Date dtype (PIPE-08).
       - `CfD_ID`: str with regex `r"^[A-Z0-9]{3,4}-[A-Z]{3}-\d+$"` (verified to match observed IDs like `CAA-EAS-166`, `AR2-HRN-306`, `AAA-COM-191`).
       - `Technology`, `Allocation_round`, `Reference_Type`: `Check.isin(...)`.
       - `CFD_Generation_MWh`: `Check.ge(0)`.
       - `CFD_Payments_GBP`: no non-negativity check (signed).
       - `Strike_Price_GBP_Per_MWh`: `Check.gt(0)`.
       - `Market_Reference_Price_GBP_Per_MWh`, `Weighted_IMRP_GBP_Per_MWh`, `Avoided_GHG_tonnes_CO2e`, `Avoided_GHG_Cost_GBP`: float, no range check.
       - Export a `validate(df: pl.DataFrame) -> pl.DataFrame` helper that wraps `schema.validate(df, lazy=False)` and converts `Settlement_Date` string->Date if needed (use `pl.col("Settlement_Date").str.slice(0, 10).str.to_date("%Y-%m-%d")` if dtype is string).
    2. Create `tests/test_schema.py` with one test per behavior bullet. Use the `sample_csv_path` fixture to load a clean DataFrame, then mutate it for negative cases. Test function names must include: `test_valid_accepts`, `test_extra_column_fails`, `test_column_rename_fails`, `test_unknown_technology_fails`, `test_unknown_reference_type_fails`, `test_date_only_no_time`, `test_negative_generation_fails`, `test_negative_payments_accepted`, `test_cfd_id_name_one_to_one` (asserts the 1:1 mapping on the committed fixture — resolves RESEARCH Open Q2).
  </action>
  <verify>
    <automated>uv run pytest tests/test_schema.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_schema.py -x -q` exits 0
    - `grep -q "strict=True" pipeline/schema.py` succeeds
    - `grep -q "pl.Date" pipeline/schema.py` OR `grep -q "pandera.*Date" pipeline/schema.py` succeeds
    - Test file defines at least 9 test functions named as listed above (including `test_cfd_id_name_one_to_one`)
    - `grep -c "isin" pipeline/schema.py` >= 3 (Technology, Allocation_round, Reference_Type)
  </acceptance_criteria>
  <done>
    Pandera schema rejects all four drift types; date-only enforced; signed payments allowed.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: pipeline/store.py idempotent DuckDB upsert + test_store.py covering PIPE-03</name>
  <files>pipeline/store.py, tests/test_store.py</files>
  <read_first>
    - .planning/phases/01-pipeline-first-chart/01-RESEARCH.md (Pattern 1 lines 271-310)
    - pipeline/schema.py (just created)
    - tests/conftest.py
  </read_first>
  <behavior>
    - `upsert(df, db_path)` creates the `raw_generation` table on first call with PK (Settlement_Date, CfD_ID)
    - Running `upsert(df, db_path)` then `upsert(df, db_path)` again produces an identical table (same row count, same SUM aggregates for every numeric column)
    - When the second call has a modified `CFD_Generation_MWh` value for a row with an existing PK, the stored value updates to the new value
    - The Settlement_Date column in DuckDB has SQL type `DATE` (not TIMESTAMP)
    - `upsert` returns the row count affected (int)
    - Calling `upsert` on a validated DataFrame never raises on the committed fixture
  </behavior>
  <action>
    1. Create `pipeline/store.py`:
       ```python
       """Polars -> DuckDB idempotent upsert (PIPE-03)."""
       from __future__ import annotations
       from pathlib import Path
       import duckdb
       import polars as pl
       from pipeline.schema import validate

       _VALUE_COLS = [
           "Name_of_CfD_Unit", "Technology", "Allocation_round", "Reference_Type",
           "CFD_Generation_MWh", "Avoided_GHG_tonnes_CO2e", "CFD_Payments_GBP",
           "Avoided_GHG_Cost_GBP", "Strike_Price_GBP_Per_MWh",
           "Market_Reference_Price_GBP_Per_MWh", "Weighted_IMRP_GBP_Per_MWh",
       ]

       _DDL = """
       CREATE TABLE IF NOT EXISTS raw_generation (
           Settlement_Date DATE NOT NULL,
           CfD_ID VARCHAR NOT NULL,
           Name_of_CfD_Unit VARCHAR,
           Technology VARCHAR,
           Allocation_round VARCHAR,
           Reference_Type VARCHAR,
           CFD_Generation_MWh DOUBLE,
           Avoided_GHG_tonnes_CO2e DOUBLE,
           CFD_Payments_GBP DOUBLE,
           Avoided_GHG_Cost_GBP DOUBLE,
           Strike_Price_GBP_Per_MWh DOUBLE,
           Market_Reference_Price_GBP_Per_MWh DOUBLE,
           Weighted_IMRP_GBP_Per_MWh DOUBLE,
           PRIMARY KEY (Settlement_Date, CfD_ID)
       );
       """

       def upsert(df: pl.DataFrame, db_path: str | Path) -> int:
           df = validate(df)
           con = duckdb.connect(str(db_path))
           try:
               con.execute(_DDL)
               con.register("incoming", df.to_arrow())
               set_clause = ", ".join(
                   f"{c} = EXCLUDED.{c}" for c in _VALUE_COLS
               )
               con.execute(f"""
                   INSERT INTO raw_generation
                   SELECT Settlement_Date, CfD_ID, Name_of_CfD_Unit, Technology,
                          Allocation_round, Reference_Type,
                          CFD_Generation_MWh, Avoided_GHG_tonnes_CO2e,
                          CFD_Payments_GBP, Avoided_GHG_Cost_GBP,
                          Strike_Price_GBP_Per_MWh,
                          Market_Reference_Price_GBP_Per_MWh,
                          Weighted_IMRP_GBP_Per_MWh
                   FROM incoming
                   ON CONFLICT (Settlement_Date, CfD_ID) DO UPDATE SET
                       {set_clause};
               """)
               count = con.execute("SELECT COUNT(*) FROM raw_generation;").fetchone()[0]
               return int(count)
           finally:
               con.close()
       ```
    2. Create `tests/test_store.py`:
       - `test_creates_table_first_call(fresh_duckdb, sample_csv_path)`: upsert, then connect and verify `raw_generation` exists with expected column count (13).
       - `test_idempotent(fresh_duckdb, sample_csv_path)`: upsert twice; compare `SELECT SUM(CFD_Generation_MWh), SUM(CFD_Payments_GBP), COUNT(*) FROM raw_generation` before and after second call — must be identical.
       - `test_update_on_conflict(fresh_duckdb, sample_csv_path)`: upsert once; mutate one row's CFD_Generation_MWh to add 999.0; upsert again; query that PK and assert the new value is stored.
       - `test_settlement_date_is_date_type(fresh_duckdb, sample_csv_path)`: after upsert, `PRAGMA table_info('raw_generation')` (or `SELECT typeof(Settlement_Date) FROM raw_generation LIMIT 1`) returns `DATE`.
       - `test_returns_row_count(fresh_duckdb, sample_csv_path)`: return value equals `SELECT COUNT(*)`.
  </action>
  <verify>
    <automated>uv run pytest tests/test_store.py tests/test_schema.py tests/test_units.py -x -q</automated>
  </verify>
  <acceptance_criteria>
    - `uv run pytest tests/test_store.py -x -q` exits 0
    - `grep -q "ON CONFLICT" pipeline/store.py` succeeds
    - `grep -q "PRIMARY KEY" pipeline/store.py` succeeds
    - `grep -q "Settlement_Date DATE" pipeline/store.py` succeeds
    - Test file defines at least 5 test functions covering behavior bullets
    - Full phase test suite so far passes: `uv run pytest tests/ -x -q` exits 0
  </acceptance_criteria>
  <done>
    Idempotent upsert proven; schema, units, store all green; foundation ready for fetcher/validator to build on.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem -> pipeline | CSV file on disk is parsed; upstream-controlled content |
| pipeline -> DuckDB | Validated DataFrame written via parameterised upsert (no string interpolation of user data) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-01-01-01 | Tampering | pipeline/schema.py | mitigate | Pandera `strict=True` rejects unknown columns; enum `isin` rejects injected values |
| T-01-01-02 | Tampering | pipeline/store.py | mitigate | Upsert uses DuckDB Arrow registration + column-name allowlist `_VALUE_COLS`, no user data in SQL string |
| T-01-01-03 | Information Disclosure | tests/fixtures | accept | Fixture contains only public LCCC data; no PII, no secrets |
| T-01-01-04 | Denial of Service | pipeline/store.py | accept | DuckDB file is local; no network attack surface at this layer |
</threat_model>

<verification>
- `uv run pytest tests/ -x -q` exits 0 (all three test modules green)
- `grep -r "pandas" pipeline/` returns no results (Polars only — prototype baggage stays out)
- `uv run python -c "from pipeline.schema import schema, validate; from pipeline.store import upsert; from pipeline.units import GBP_M, GBP_BN; print('ok')"` prints `ok`
- `ls tests/fixtures/cfd_sample.csv` succeeds
</verification>

<success_criteria>
- Four test files exist and pass: test_units.py, test_schema.py, test_store.py, conftest.py importable
- `pipeline/units.py`, `pipeline/schema.py`, `pipeline/store.py` exist and are importable
- Pandera schema is `strict=True`
- DuckDB upsert uses `ON CONFLICT (Settlement_Date, CfD_ID) DO UPDATE`
- Settlement_Date is `DATE` in DuckDB (PIPE-08 enforced)
- `cfd_sample.csv` fixture contains every required enum combo + 2022 clawback row
</success_criteria>

<output>
After completion, create `.planning/phases/01-pipeline-first-chart/01-01-SUMMARY.md` documenting: modules created, schema enum sets, PK choice verification result (confirm or flag A1), test counts.
</output>
