# Validation evidence

Evidence is separated into checks executed during this revision, earlier recorded checks and account-specific steps still missing. Offline rendering and mocks do not prove cloud deployment.

## Repository review: 2026-11-09

- Moved the historical 2026-11-04 Streamlit image into the [local development guide](optional/local-development.md#historical-local-screenshot), with its interface, source file, date and counts stated explicitly. README presents the actual Databricks links and recorded cloud results.
- Corrected the saved-snapshot command to pass `source_mode=volume`; the default Job mode is `api`. First-deployment examples now explicitly pause the schedule until a manual run passes.
- Checked the dashboard guide against the versioned asset's actual counters and source-health columns.
- Added `scripts/check_docs.py` to CI and `make test`. It checks public Markdown links/anchors and rejects links to excluded files or tracked personal study material. Smoke checks covered broken/private/outside links, duplicate headings and fenced examples.
- Local checks passed after the review: Ruff, 38 tests and all 16 public Markdown files. The workflow repeats these checks from a clean GitHub checkout.
- Authenticated inspection confirmed the latest Job run succeeded, the published dashboard exists, its draft matches the versioned JSON, and the 07:00 schedule remains active. `bundle plan` reported six unchanged resources and no additions, updates or deletions.

## Authenticated Databricks verification: 2026-11-09

The project is now deployed and verified on the real workspace. See [live deployment evidence](databricks-deployment.md) and its sanitized JSON record for resource IDs, query results and the successful five-task run.

- Official CLI v1.24.0 installed from a checksum-verified release and authenticated through OAuth.
- Authenticated bundle validation passed. The reviewed deployment preserved schemas, Volume, Job and dashboard; zero resources were deleted.
- Fresh direct-API run `732812466979937` succeeded through ingestion, Spark transformations, 18 integrity checks, coverage/freshness checks and dashboard refresh.
- Live SQL returned six observation dates, latest count 29 and 4/4 source coverage. Delta format and liquid-clustering keys were confirmed.
- The dashboard was published using the existing ID and viewer credentials; daily 07:00 Vietnam-time API collection remains active.
- Local regression checks passed: 38 tests and Ruff.

The local and historical records below precede workspace authentication. They are retained as earlier evidence rather than the current deployment status.

## English documentation revision: 2026-11-09

Environment: Windows, Python 3.12 and the dependencies in `uv.lock`. Setup used `uv sync --frozen --extra cloud --extra dev --extra databricks`.

| Check | Result |
|---|---|
| Baseline pytest suite before edits | 35 passed |
| Final lint, tests and documentation checks | Passed; details below |
| Docker Compose configuration | Passed |
| Docker runtime | Not available: Linux Docker engine pipe absent |
| CLI status during the initial local phase | Terraform unavailable locally; Databricks CLI installed and authenticated in the later live phase |

This revision translates documentation, source comments, CLI messages, bundle descriptions and notebook explanations; replaces personal setup paths/hosts; and aligns lint commands. It preserves ingestion and metric rules. Public documentation covers architecture, operations, deployment and validation.

### Final verification

| Check | Result |
|---|---|
| `uv run ruff check src tests dashboard scripts` | Passed |
| Final `uv run pytest -q` | 35 passed |
| Databricks SQL renderer | 19 models and 18 checks rendered |
| BigQuery offline compiler | 19 models rendered; remote queries forbidden |
| CLI help for SQL helper and Databricks uploader | English help rendered successfully |
| Initial bundle YAML inspection, before live reconciliation | Notebook paths, four-task order and paused schedule checked offline |
| Documentation links and language scan | All local links/anchors resolve; no Vietnamese authored text found |
| Fresh source-only copy: `uv sync --frozen` | Passed with default dependencies and a new virtual environment |
| Fresh copy: `uv run sea-it-jobs demo` | 19 models + 3 seeds + 18 tests; PASS=40, ERROR=0 |
| Fresh copy: country/source-health SQL presets | Passed; synthetic outage and country counts preserved |
| Fresh copy: Streamlit AppTest | Three charts, synthetic label and no exceptions |

The fresh copy excluded virtual environments, generated data, dbt outputs and local credentials. It demonstrates source-only demo reproduction on this machine, not a live API/cloud deployment. No new market observations were collected during this revision. The English revision reduced documentation duplication while keeping setup, data rules, failure recovery, optional deployment paths and earlier validation evidence.

## Documentation layout and GitHub checkout: 2026-11-09

Public guides are indexed in [docs/README](README.md), with Databricks instructions under `deployment/` and GCP alternatives under `optional/`.

| Check | Result |
|---|---|
| Dedicated Git repository | Project root contains `pyproject.toml`; published to [GitHub](https://github.com/Tanh2k8-123/jobs-it-vn-sg-data-pipeline) |
| Public Markdown links in a fresh GitHub clone | All checked links/anchors passed; no missing local files |
| Personal study materials | Excluded by Git, Docker build context and Databricks bundle sync |
| Public links to private study materials | None |
| Lint, pytest, Compose config and Databricks SQL renderer after reorganization | Passed; 35 tests, 19 models and 18 integrity queries |
| [GitHub Actions on the initial source commit](https://github.com/Tanh2k8-123/jobs-it-vn-sg-data-pipeline/actions/runs/42550303274) | Passed on Ubuntu: locked install, Ruff, pytest, both SQL renderers, Compose config and Terraform format/init/validate |

The clone check verifies committed files and documentation links. Live API/cloud deployment still requires the account-specific steps below. Automated checkout validation is available in [GitHub Actions](https://github.com/Tanh2k8-123/jobs-it-vn-sg-data-pipeline/actions).

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

- Published-dashboard access from a reviewer-equivalent account outside the current deployment principal.
- Real GCP plan/apply, GCS writes, BigQuery loads or cloud dbt build; no account credentials are used by offline checks.
- Docker image builds, live containers or a live Kestra DAG in this environment.
- A published Looker Studio report, live API/cloud quick-start reproduction from a fresh clone, cohort submission or peer reviews.

Catalog access, direct Lever connectivity and serverless execution were confirmed in the deployed workspace. Other accounts still need to verify their own permissions/network access, and reviewer access remains an explicit check. Follow [Databricks setup](deployment/databricks.md), then complete the [submission checklist](submission-checklist.md).
