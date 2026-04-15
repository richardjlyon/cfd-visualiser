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

| Variable | Default | Description |
|----------|---------|-------------|
| `PIPELINE_HC_URL` | *(unset)* | Healthchecks.io ping URL; omit in dev to skip ping |
| `PIPELINE_LATEST_CSV` | `data/latest.csv` | Path for the downloaded (uncompressed) CSV |
| `PIPELINE_RAW_DIR` | `data/raw` | Directory for gzipped date-stamped snapshots |
| `PIPELINE_DB_PATH` | `data/cfd.duckdb` | Path to the DuckDB data file |

## Data flow

```
LCCC CSV endpoint
    │  httpx (retries=3, timeout=60s)
    ▼
pipeline/fetch.py
    ├── writes data/latest.csv (uncompressed, overwritten daily)
    └── writes data/raw/YYYY-MM-DD.csv.gz (gzip archive, kept)
         │
    ▼
pipeline/validate.py  (Pandera strict schema — exits 2 on drift)
    │  Settlement_Date: str → pl.Date (UTC-naive, date-only)
    ▼
pipeline/store.py  (DuckDB upsert ON CONFLICT DO UPDATE)
    │  PK: (Settlement_Date, CfD_ID)
    ▼
Healthchecks.io ping (optional — PIPELINE_HC_URL)
```

## Adding new data sources

1. Add a fetch module under `pipeline/` following the same pattern as `fetch.py`.
2. Normalise any date columns to `pl.Date` (UTC-naive) before passing to DuckDB.
3. Store in a separate table in `data/cfd.duckdb`; do not mix with `raw_generation`.
