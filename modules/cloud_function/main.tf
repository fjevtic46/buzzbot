variable "name" {
  type = string
}

variable "location" {
  type = string
}

variable "runtime" {
  type = string
}

variable "entry_point" {
  type = string
}

variable "source_bucket" {
  type = string
}

variable "source_object" {
  type = string
}

variable "envs" {
  type = map(string)
}

resource "google_cloudfunctions2_function" "function" {
  name     = var.name
  location = var.location

  build_config {
    runtime     = var.runtime
    entry_point = var.entry_point
    source {
      storage_source {
        bucket = var.source_bucket
        object = var.source_object
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "256Mi"
    timeout_seconds    = 60
    all_users_granted_access = true
    environment_variables = var.envs
  }
}
output "service_account" {
  value = google_cloudfunctions2_function.function.service_config[0].service_account_email
}