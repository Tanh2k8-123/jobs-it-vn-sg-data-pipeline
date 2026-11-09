# Commands and recovery

Run from the directory containing `pyproject.toml`. `--target local` uses DuckDB; `--target cloud` uses the optional GCP path. Databricks uses the separate uploader and bundle commands below.

## Everyday commands

```bash
uv run sea-it-jobs audit
uv run sea-it-jobs pipeline --target local
uv run streamlit run dashboard/app.py
```

One batch gets one run ID. Enabled boards are processed independently. A failed board produces failure metadata; other boards continue. The pipeline builds available metrics, then exits nonzero if an extraction failed. Collection dates use `Asia/Ho_Chi_Minh` by default; timestamps are UTC.

To run stages separately:

```bash
uv run sea-it-jobs extract --run-id manual_001 --page-size 50
uv run sea-it-jobs load --run-id manual_001 --target local
uv run sea-it-jobs transform --target local
uv run sea-it-jobs check-run --run-id manual_001
```

Use `--boards shopback-2` on `extract`/`pipeline` to collect a subset; other enabled sources can appear missing. `extract --allow-partial` lets an orchestrator publish failures before a final `check-run`; it does not make incomplete records valid. Generated run IDs combine UTC time and a random suffix.

For the deployed Databricks API path:

```bash
databricks bundle run tech_jobs_daily --profile tech-jobs-free
```

If workspace network access requires local collection/upload, use:

```bash
uv run python scripts/run_databricks.py --collect --job-id JOB_ID
```

See [Databricks setup](deployment/databricks.md) for profiles, upload paths and scheduling.

## Choose the right retry

| Failure | Action |
|---|---|
| API request/validation | Inspect manifest, fix the cause and extract with a **new run ID** |
| Upload/load | Retry the same saved run without contacting the source |
| SQL/model/test | Fix SQL/rules and rerun `transform`; keep raw snapshots |
| Checksum mismatch | Recover original bytes; do not edit the manifest hash |
| Freshness check | Confirm collection/upload ran today, not only transformation |
| Missing coverage | Inspect `mart_source_health` and the failed board's manifest |

Transient 429/5xx and connection/read errors use bounded retries with backoff. A 404 is not retried. Duplicate IDs or an exhausted page guard mark extraction incomplete. A successful `[]` is a valid zero, not a failure.

## Reuse saved data

```bash
uv run sea-it-jobs replay data/local/lever/shopback-2/snapshot_date=YYYY-MM-DD/run_id=RUN
uv run sea-it-jobs transform --target local
```

Replace the path with a real snapshot folder. Replay verifies metadata, IDs, count and SHA-256, then loads the original observation date. It does not backfill history from today's API. Loading/replaying the same saved run is idempotent. Reusing a saved same-day extraction ID reuses its snapshot, including a failed one.

For GCP, retry `load --run-id RUN --target cloud`, or replay a `gs://` snapshot as shown in [GCP setup](optional/gcp.md). GCS rejects conflicting contents. BigQuery commits raw postings and run metadata together; staging expires after one hour. Retry transaction conflicts using the same saved run.

For Databricks, upload a saved run with `run_databricks.py --run-id RUN`, then run the Job with `--params source_mode=volume,require_fresh=true`. Without the mode override, this deployment's default would collect from the API instead. Matching existing Volume files are accepted; different bytes are rejected. Historical snapshots need the explicit `require_fresh=false` invocation in the setup guide.

## Model failures and stale dashboards

Inspect `dbt/logs/dbt.log` and `dbt/target/run_results.json`, or the failing Databricks task. Local CSV publication occurs only after a successful build, so a failed build can leave the previous dashboard generation visible.

Check the observation date, successful/expected boards and latest-attempt status. An earlier complete same-day snapshot can remain selected after a later failure. Missing days are never filled with assumed counts. After a new local export, click **Refresh data**. Check Kestra executions or Databricks/collector schedules if the date is stale.

## Change monitored sources

Audit first, then edit `config/boards.csv`. Local/GCP `transform` synchronizes `dbt/seeds/companies.csv`; Databricks reads the same board configuration. Coverage uses the current enabled roster for all dates. Disclose roster changes and avoid reading them as hiring changes. Review role/location seeds against real postings before changing classification rules.

## Docker (optional)

Requires Compose >=2.24 and a running Linux Docker engine:

```bash
docker compose --profile tools build pipeline
docker compose --profile tools run --rm pipeline pipeline --target local
docker compose up -d dashboard
docker compose --profile orchestration up -d --build postgres kestra
```

Ports are bound to localhost. Change the example passwords in `.env` before starting Kestra. Its image includes Python/dbt and uses a Process runner without mounting the Docker socket. See [Kestra operations](optional/kestra.md) for flow import, scheduling and credentials.

Stop services with `docker compose --profile orchestration down`. Named volumes retain execution history; adding `--volumes` removes it. Keep Windows and WSL virtual environments separate. Paths/cloud IDs are configurable through `.env`; credentials, raw output and Terraform state stay untracked.
