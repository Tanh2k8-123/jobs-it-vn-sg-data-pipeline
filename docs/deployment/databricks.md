# Run on Databricks Free Edition

Run commands from the directory containing `pyproject.toml`. Start with the local [quick start](../../README.md#quick-start-run-locally-first) if these tools are new to you.

## 1. Understand the flow

```text
Lever API → Python collector → JSON + manifest in Unity Catalog Volume
         → Bronze Delta → Silver normalization → Gold metrics → AI/BI dashboard
```

A **Volume** stores files; a **Delta table** stores transactional table data. Bronze, Silver and Gold mean original, standardized and reporting data. No GCP project ID is needed.

| Mode | Where collection happens | Use it when |
|---|---|---|
| `volume` (default) | Your machine collects and uploads snapshots | The reliable starting path when notebook internet access is restricted |
| `api` | A notebook calls Lever and saves files to the Volume | You have confirmed the workspace can reach Lever |

Free Edition uses serverless compute and can restrict outbound access. Check your actual account: [official limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

## 2. Install and sign in

Install the current [Databricks CLI](https://docs.databricks.com/aws/en/dev-tools/cli/install) separately from the Python SDK. Both must be available in the shell you use. In WSL, run `export UV_PROJECT_ENVIRONMENT=.venv-wsl` before `uv sync`, in each new terminal. Do not reuse a Windows `.venv` in WSL.

```bash
uv sync --frozen --extra databricks
databricks --version
databricks auth login --host https://YOUR_WORKSPACE_HOST --profile tech-jobs-free
databricks catalogs list --profile tech-jobs-free
```

Replace `https://YOUR_WORKSPACE_HOST` with your workspace URL. Complete the browser login. The profile stores local authentication configuration; do not commit `.databrickscfg`, tokens or passwords.

The bundle gets its workspace from `--profile` rather than a personal URL in source code. See [bundle authentication](https://docs.databricks.com/aws/en/dev-tools/bundles/authentication).

## 3. Deploy the resources

```bash
databricks bundle validate --profile tech-jobs-free
databricks bundle deploy --profile tech-jobs-free
databricks bundle summary --profile tech-jobs-free
```

The default catalog is `workspace`. If yours differs, change `variables.catalog.default` in `databricks.yml` before deployment. Keep that catalog consistent in upload paths and dashboard SQL.

The bundle defines three schemas, one managed Volume and a Job with four sequential serverless notebook tasks:

| Task | Notebook | Result |
|---|---|---|
| `setup` | `00_setup.py` | Create Bronze Delta table and raw views |
| `ingest_bronze` | `01_ingest_bronze.py` | Validate snapshots and load Bronze |
| `build_silver_gold` | `02_build_silver_gold.py` | Build normalized and reporting models |
| `quality_checks` | `03_quality_checks.py` | Check integrity, source coverage and freshness |

Notebook libraries are declared in the bundle. Spark is supplied by Databricks; do not install PySpark. The notebook renders 19 shared SQL models and 18 integrity checks; it does not run `dbt build`. Read the [storage design](../architecture.md#snapshots-and-loading) for atomic Bronze envelopes and replay behavior.

Find the deployed Job ID in `bundle summary` or its URL under **Jobs & Pipelines**. It is the number after `/jobs/`.

## 4. Collect, upload and run

Replace `JOB_ID` with that number:

```bash
uv run python scripts/run_databricks.py --collect --job-id JOB_ID
```

This command checks authentication and the Volume, collects fresh data locally, uploads JSON then manifest, triggers the Job with `source_mode=volume` and waits for completion. The default Volume is `/Volumes/workspace/tech_jobs_bronze/raw_snapshots`.

For another catalog/prefix, add `--volume-path /Volumes/YOUR_CATALOG/YOUR_PREFIX_bronze/raw_snapshots`. For another login profile, add `--profile YOUR_PROFILE`.

To upload an existing run without collecting again:

```bash
uv run python scripts/run_databricks.py --run-id SAVED_RUN
databricks bundle run tech_jobs_daily --profile tech-jobs-free
```

Use the run ID from its manifest. For an intentionally old snapshot, disable only the freshness requirement for that invocation:

```bash
databricks bundle run tech_jobs_daily --profile tech-jobs-free --params source_mode=volume,require_fresh=false
```

This reprocesses the original date. Source failures still fail the quality task; `require_fresh=false` does not waive coverage checks.

## 5. Verify the output

Run in SQL Editor using your serverless SQL warehouse:

```sql
select snapshot_date, tech_postings, successful_boards, expected_boards
from workspace.tech_jobs_gold.mart_daily_overview
order by snapshot_date desc;

select snapshot_date, country_code, tech_postings
from workspace.tech_jobs_gold.mart_daily_country
order by snapshot_date desc, country_code;
```

VN + SG can exceed the overall count because one posting may link to both countries. Continue with [dashboard setup](dashboard.md).

## 6. Optional: collect inside the notebook

First test a small request in a serverless notebook:

```python
import requests

response = requests.get(
    "https://api.lever.co/v0/postings/shopback-2",
    params={"mode": "json", "limit": 1},
    timeout=(10, 20),
)
response.raise_for_status()
print(type(response.json()))
```

If allowed and valid, run:

```bash
databricks bundle run tech_jobs_daily --profile tech-jobs-free --params source_mode=api,require_fresh=true
```

If blocked, continue with local collection/upload. Do not assume every Free Edition account has the same outbound access.

## 7. Enable daily collection

The bundle includes a **paused** 07:00 `Asia/Ho_Chi_Minh` schedule. Enable automation only after a successful manual run.

- **API mode:** set the Job's default `source_mode` to `api` in `databricks.yml`, then unpause its schedule. A one-off `--params` does not change the default.
- **Volume mode:** schedule `run_databricks.py --collect --job-id JOB_ID` on your machine or authenticated CI. The collector uploads and triggers the Job. Scheduling only the Job rereads saved snapshots and cannot collect new API data.

The collector host must be running and authentication valid. Keep `require_fresh=true` for daily operation. Development-mode deployment can pause schedules again; check after redeployment and save the intended operational configuration in Git. See [deployment modes](https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes).

## Evidence and troubleshooting

- API failure: inspect the manifest/source-health table; retry collection with a new run ID.
- Upload/load failure: retry the saved run, preserving its files and date.
- SQL/check failure: inspect the failing task and rerun after fixing it; original snapshots remain available.
- Old observation date: verify the collector ran, not just the transformation Job.

Offline tests do not prove cloud execution. Save a successful real Job run, table/query results, schedule evidence and dashboard access proof. Current evidence is in [validation](../validation.md); recovery commands are in the [runbook](../runbook.md).
