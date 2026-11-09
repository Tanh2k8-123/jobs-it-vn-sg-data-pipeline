locals {
  raw_fields = [
    { name = "run_id", type = "STRING" },
    { name = "board_slug", type = "STRING" },
    { name = "snapshot_date", type = "DATE" },
    { name = "fetched_at", type = "TIMESTAMP" },
    { name = "job_id", type = "STRING" },
    { name = "posting_json", type = "STRING" },
  ]
  run_fields = [
    { name = "run_id", type = "STRING" },
    { name = "board_slug", type = "STRING" },
    { name = "snapshot_date", type = "DATE" },
    { name = "started_at", type = "TIMESTAMP" },
    { name = "completed_at", type = "TIMESTAMP" },
    { name = "fetched_at", type = "TIMESTAMP" },
    { name = "status", type = "STRING" },
    { name = "extraction_status", type = "STRING" },
    { name = "record_count", type = "INTEGER" },
    { name = "page_count", type = "INTEGER" },
    { name = "error_message", type = "STRING" },
    { name = "sha256", type = "STRING" },
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(["bigquery.googleapis.com", "storage.googleapis.com", "iam.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

resource "google_storage_bucket" "raw" {
  name                        = var.bucket_name
  location                    = upper(var.location)
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = { project = "tech-jobs", managed_by = "terraform" }
  versioning { enabled = true }
  depends_on = [google_project_service.apis]
}

resource "google_bigquery_dataset" "raw" {
  dataset_id                 = var.raw_dataset
  location                   = var.location
  delete_contents_on_destroy = false
  description                = "Original Lever postings and committed extraction runs"
  depends_on                 = [google_project_service.apis]
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                 = var.analytics_dataset
  location                   = var.location
  delete_contents_on_destroy = false
  description                = "dbt staging, models and dashboard marts"
  depends_on                 = [google_project_service.apis]
}

resource "google_bigquery_table" "raw_postings" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "raw_postings"
  deletion_protection = var.deletion_protection
  schema              = jsonencode(local.raw_fields)
  clustering          = ["board_slug", "job_id"]
  time_partitioning {
    type  = "DAY"
    field = "snapshot_date"
  }
}

resource "google_bigquery_table" "ingestion_runs" {
  dataset_id          = google_bigquery_dataset.raw.dataset_id
  table_id            = "ingestion_runs"
  deletion_protection = var.deletion_protection
  schema              = jsonencode(local.run_fields)
  clustering          = ["board_slug", "status"]
  time_partitioning {
    type  = "DAY"
    field = "snapshot_date"
  }
}

resource "google_service_account" "pipeline" {
  account_id   = "tech-jobs-pipeline"
  display_name = "Tech Jobs pipeline runtime"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_bigquery_dataset_iam_member" "runtime" {
  for_each = {
    raw       = google_bigquery_dataset.raw.dataset_id
    analytics = google_bigquery_dataset.analytics.dataset_id
  }
  dataset_id = each.value
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_storage_bucket_iam_member" "runtime" {
  for_each = toset(["roles/storage.objectCreator", "roles/storage.objectViewer"])
  bucket   = google_storage_bucket.raw.name
  role     = each.value
  member   = "serviceAccount:${google_service_account.pipeline.email}"
}
