variable "name" {
  type = string
}

variable "image" {
  type = string
}

variable "envs" {
  type = list(object({
    name  = string
    value = string
  }))
}

variable "location" {
  type = string
}

resource "google_cloud_run_v2_service" "service" {
  name     = var.name
  location = var.location

  template {
    containers {
      image = var.image
      envs  = var.envs
    }
    scaling {
      min_instances = 0
      max_instances = 1
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

output "url" {
  value = google_cloud_run_v2_service.service.uri
}
output "service_account" {
  value = google_cloud_run_v2_service.service.template[0].service_account
}