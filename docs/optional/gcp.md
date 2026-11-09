# Google Cloud setup

This is the optional GCP path. The selected cloud target is [Databricks Free Edition](../deployment/databricks.md). Choose one deployment path; local runs need neither cloud account.

Run from the repository root. Select an existing billing-enabled project that you administer.
Install the Google Cloud CLI and Terraform using their official installation instructions.

## 1. Authenticate the provisioning operator

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

The provisioning operator needs permission to enable APIs, create buckets/datasets/service
accounts and set the corresponding IAM bindings. The Terraform runtime service account has
different, narrower data-processing roles. Do not add owner/editor roles to that account.

## 2. Provision

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit project_id and bucket_name.
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan -out=plan.tfplan
terraform -chdir=terraform apply plan.tfplan
terraform -chdir=terraform output
```

Use Terraform >=1.6. In PowerShell, replace `cp` with `Copy-Item` if needed. These commands provision real resources and require your authenticated cloud account.

Bucket and datasets share `asia-southeast1` by default. Change locations before first deployment;
moving existing datasets requires a migration. Raw tables have deletion protection and the bucket
does not allow force-destroy. State is local by default and is gitignored. For team use, configure
a separate protected GCS Terraform backend before sharing administration.

## 3. Configure the application

Copy `.env.example` to `.env` and set:

```dotenv
GCP_PROJECT_ID=YOUR_PROJECT_ID
GCP_LOCATION=asia-southeast1
GCS_BUCKET=YOUR_UNIQUE_BUCKET
BQ_RAW_DATASET=tech_jobs_raw
BQ_ANALYTICS_DATASET=tech_jobs_analytics
```

For local execution, ADC uses the authenticated operator. For a deployed VM, attach the runtime
service account and use workload credentials. For local impersonation, an administrator must
grant your principal Service Account Token Creator on the runtime account, then run:

```bash
gcloud auth application-default login \
  --impersonate-service-account=tech-jobs-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Both Python cloud clients and dbt's `method: oauth` use ADC. No key file is needed.

## 4. Run and verify

```bash
uv sync --frozen --extra cloud --extra dev
uv run sea-it-jobs pipeline --target cloud
```

Verify GCS objects exist under `lever/<board>/snapshot_date=<date>/run_id=<run>/`.
Each complete local extraction, including failed-source metadata, is uploaded with the manifest
last. The loader downloads that immutable GCS snapshot, verifies its checksum, stages rows in
BigQuery, and commits the posting/run replacement in one transaction. Temporary tables expire
after one hour and are also deleted after loading. A failed extraction loads only its run record.

Check BigQuery:

```sql
SELECT snapshot_date, tech_postings, successful_boards, expected_boards, coverage_ratio
FROM `YOUR_PROJECT_ID.tech_jobs_analytics.mart_daily_overview`
ORDER BY snapshot_date DESC;
```

Then follow [Looker Studio setup](looker-studio.md). Record the real report URL and
screenshots in your README after publication.

## 5. Reprocess from the lake

```bash
uv run sea-it-jobs replay \
  gs://YOUR_BUCKET/lever/shopback-2/snapshot_date=YYYY-MM-DD/run_id=RUN \
  --target cloud
uv run sea-it-jobs transform --target cloud
```

Replay retains the original observed date. It is not historical backfill from today's API.
Repeated replays must leave analytical counts unchanged.

## Costs and teardown

Create a Cloud Billing budget in your billing account and monitor BigQuery bytes processed.
The project contains no paid VM; Kestra runs on your machine unless you deploy it elsewhere.
Budget alerts are notifications, not a spending cap. Raw history is intentionally retained.
dbt's BigQuery limit is 1 GB per query, not a total spending limit. See the [table-layout rationale](../architecture.md#storage-layout).
Deletion protection must be deliberately changed before deleting raw tables. Do not blindly
destroy a project containing other workloads. Never publish Terraform state or ADC tokens.
