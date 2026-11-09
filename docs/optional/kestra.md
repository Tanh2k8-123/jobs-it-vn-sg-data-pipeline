# Kestra operation

Kestra is the optional local/GCP scheduler: it runs tasks in order, tracks failures and starts daily batches. The selected Databricks path uses the Job in [Databricks setup](../deployment/databricks.md) instead.

## Start locally

Prerequisites: running Linux Docker engine, Compose >=2.24, populated `.env` with your own local
passwords. The custom Kestra image contains the project, Python and dbt. Process tasks run inside
that container; there is no Docker socket mount and no dependency on a host Python environment.

```bash
docker compose --profile orchestration up -d --build postgres kestra
```

Open http://localhost:8080, sign in with `KESTRA_USER` / `KESTRA_PASSWORD`, then create/import
the flow in `orchestration/kestra/flows/tech_jobs_daily.yml` using the flow editor.
Use namespace `zoomcamp.tech_jobs`. Execute manually with input `target=local`.

The first build downloads pinned Python dependencies and may take several minutes. Configuration
and dbt files are baked into the images; rebuild after changing application/configuration files.
Raw local data is a shared volume. `docker compose up -d dashboard` starts the matching reader.

## DAG

1. `extract_and_validate`: all boards, independent source failures and immutable per-board snapshots.
2. `publish_and_load`: local load or GCS publication followed by lake-to-BigQuery transactional load.
   This task can retry safely with the same execution ID.
3. `dbt_build_and_tests`: all models and data tests; local mode publishes dashboard exports afterwards.
4. `report_source_failures`: returns an execution failure if any source failed, after making
   successful observations and source-coverage information available.

Flow concurrency is one, preventing overlapping local warehouse writers. Python request retry
is bounded; invalid data or exhausted pagination fails the source rather than recording zero.
Extraction is not retried under a new identity inside the same flow. Re-execute the flow to
produce a new extraction ID after fixing a source outage.

## Schedule

The included schedule is `0 7 * * *` with timezone `Asia/Ho_Chi_Minh` (07:00 Vietnam time).
After a successful manual execution, change `disabled: true` to `false` in the imported flow.
Set both input default and schedule input to `cloud` for the GCP path. The host and Docker
engine must remain running for this local Kestra deployment to execute scheduled flows.

## Cloud credentials in Docker

Authenticate ADC on the host first. Set `ADC_DIR` to the directory that contains
`application_default_credentials.json`, for example `$HOME/.config/gcloud` inside WSL.
This file is mounted read-only; never bake credentials into an image.

```bash
export ADC_DIR="$HOME/.config/gcloud"
docker compose -f docker-compose.yml -f docker-compose.cloud.yml \
  --profile orchestration up -d --build postgres kestra
```

`.env` must contain the same project/bucket/dataset/location values used by Terraform.
Run manually with `target=cloud` before enabling the cloud schedule. ADC credentials must stay
valid; use an attached runtime service account for an always-on cloud VM deployment.

## Failure recovery

Inspect task logs and the run's manifest before retrying. A load failure can be retried using the
same run ID without contacting the source. A dbt failure requires only a transform rerun. An API
failure needs a new extraction run. Do not mark incomplete files successful manually.
See [runbook](../runbook.md) for details. Stop the services with
`docker compose --profile orchestration down`; named volumes retain execution history.

Implementation references:
[Kestra Compose installation](https://kestra.io/docs/installation/docker-compose),
[Shell Commands task](https://kestra.io/plugins/plugin-script-shell/io.kestra.plugin.scripts.shell.commands).
