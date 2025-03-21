variable "project_id" {
  type        = string
  description = "The GCP project ID"
}

variable "region" {
  type        = string
  description = "The GCP region"
  default     = "us-central1"
}

variable "source_bucket" {
  type        = string
  description = "The GCS bucket containing the function source code"
}