variable "project_id" {
  type        = string
  description = "Existing billing-enabled Google Cloud project."
}
variable "location" {
  type    = string
  default = "asia-southeast1"
}
variable "bucket_name" {
  type        = string
  description = "Globally unique raw snapshot bucket name."
}
variable "raw_dataset" {
  type    = string
  default = "tech_jobs_raw"
}
variable "analytics_dataset" {
  type    = string
  default = "tech_jobs_analytics"
}
variable "deletion_protection" {
  type        = bool
  default     = true
  description = "Protect raw BigQuery tables against accidental deletion."
}
