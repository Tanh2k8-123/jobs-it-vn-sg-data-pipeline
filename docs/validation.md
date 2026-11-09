# Validation evidence

Evidence is separated into checks executed during this revision, earlier recorded checks and account-specific steps still missing. Offline rendering and mocks do not prove cloud deployment.

## English documentation revision: 2026-11-09

Environment: Windows, Python 3.12 and the dependencies in `uv.lock`. Setup used `uv sync --frozen --extra cloud --extra dev --extra databricks`.

| Check | Result |
|---|---|
| Baseline pytest suite before edits | 35 passed |
| Final lint, tests and documentation checks | Passed; details below |
| Docker Compose configuration | Passed |
| Docker runtime | Not available: Linux Docker engine pipe absent |
| Terraform / Databricks CLI in this shell | Not installed; no authenticated deployment performed |

This revision translates documentation, source comments, CLI messages, bundle descriptions and notebook explanations; replaces personal setup paths/hosts; and aligns lint commands. It preserves ingestion and metric rules. Public documentation covers architecture, operations, deployment and validation.

### Final verification

| Check | Result |
|---|---|
| `uv run ruff check src tests dashboard scripts` | Passed |
| Final `uv run pytest -q` | 35 passed |
| Databricks SQL renderer | 19 models and 18 checks rendered |
| BigQuery offline compiler | 19 models rendered; remote queries forbidden |
| CLI help for SQL helper and Databricks uploader | English help rendered successfully |
| Bundle YAML inspection | Notebook paths, four-task order and paused schedule checked offline |
| Documentation links and language scan | All local links/anchors resolve; no Vietnamese authored text found |
| Fresh source-only copy: `uv sync --frozen` | Passed with default dependencies and a new virtual environment |
| Fresh copy: `uv run sea-it-jobs demo` | 19 models + 3 seeds + 18 tests; PASS=40, ERROR=0 |
| Fresh copy: country/source-health SQL presets | Passed; synthetic outage and country counts preserved |
| Fresh copy: Streamlit AppTest | Three charts, synthetic label and no exceptions |

The fresh copy excluded virtual environments, generated data, dbt outputs and local credentials. It demonstrates source-only demo reproduction on this machine, not a live API/cloud deployment. No new market observations were collected during this revision. The English revision reduced documentation duplication while keeping setup, data rules, failure recovery, optional deployment paths and earlier validation evidence.

## Earlier recorded live validation: 2026-11-04

The previous validation record reports a live Lever audit and local pipeline run `20261104T140000_70f214e5`, observed on 2026-11-04:

| Source | Original postings |
|---|---:|
| ShopBack | 80 |
| Portcast | 9 |
| GRADION | 11 |
| GoTo Group | 40 |
| Total | 140 |

Recorded results: **37** distinct target-market technology postings, **17** linked to VN, **24** to SG, **4** linked to both, and **4/4** source coverage. These describe selected companies on one actual date. The raw files/warehouse are gitignored and are not required committed inputs; a new checkout must recollect or use the labeled demo. The committed [audit summary](source-audit.json) and [screenshot](../dashboard/screenshots/local-overview.png) preserve supporting evidence.

| Earlier check | Recorded result |
|---|---|
| Original local tests, then Databricks-adapted full suite | 24 passed initially; 35 after adaptation |
| Real extraction → DuckDB → dbt → export | Passed |
| Local `dbt build` | 19 models + 3 seeds + 18 tests; 40 total passed |
| Reload saved run | 140 raw posting rows and 4 run rows, unchanged |
| BigQuery offline rendering and SQL dialect parsing | 19 models passed; no remote queries |
| Streamlit AppTest | Real-data and all-failed-source cases rendered without exceptions |
| Headless Chromium render | Charts rendered; screenshot saved |
| Terraform 1.14.0 format/validate | Passed with Google provider 7.46.2 |
| Docker Compose configuration | Valid |
| Kestra v1.1.6 / PostgreSQL 17.7 image manifests | Available from registry; containers not run |
| Databricks SQL rendering/parsing | 19 models and 18 integrity queries passed |
| Shared-model dependency order and Spark JSON/array selection | Passed |
| Snapshot envelope, replay/copy conflicts and upload ordering | Passed using local files/mocks |
| Bundle checked against official CLI v1.24.0 JSON schema | Passed offline; archive checksum verified against release |
| Uploader help, SQL renderer and Ruff | Passed |
| Read-only SQL helper | Real/demo queries, exercises, absent database and invalid-column cases checked |

The earlier environment used Python 3.12, uv 0.11.19, dbt-core 1.12.6, dbt-duckdb 1.11.1 and dbt-bigquery 1.12.1. These are historical results, not new cloud execution claims.

## Coverage of automated checks

Tests exercise malformed JSON, pagination limits/capped pages, duplicate IDs, incomplete extraction, valid empty snapshots, corrupted checksums, replay idempotency, multi-country counting, all/partial source outages and latest-successful daily selection. Cloud mocks verify create-only publication, manifest-last upload, conflict rejection and transactional staging/cleanup.

Reproduce the offline renderers:

```bash
uv run python scripts/compile_bigquery_offline.py
uv run python scripts/render_databricks_sql.py
```

The BigQuery compiler injects anonymous credentials only into the compiler and rejects remote query calls. The Databricks renderer writes SQL locally without a workspace login. Neither proves execution or permissions on the actual service.

## Not yet demonstrated

- An authenticated Databricks `bundle validate`/deploy, successful real Job, scheduled fresh collection or hosted dashboard access.
- Real GCP plan/apply, GCS writes, BigQuery loads or cloud dbt build; no account credentials are used by offline checks.
- Docker image builds, live containers or a live Kestra DAG in this environment.
- A published Looker Studio report, dedicated GitHub clean-clone validation, cohort submission or peer reviews.

Confirm catalog permissions, Free Edition API access, serverless dependencies and dashboard sharing in your actual workspace. Follow [Databricks setup](deployment/databricks.md), then complete the [submission checklist](submission-checklist.md).
