output "raw_bucket" { value = google_storage_bucket.raw.url }
output "runtime_service_account" { value = google_service_account.pipeline.email }
output "raw_dataset" { value = google_bigquery_dataset.raw.dataset_id }
output "analytics_dataset" { value = google_bigquery_dataset.analytics.dataset_id }
