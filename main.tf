terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Secret for user private keys
resource "google_secret_manager_secret" "user_private_keys" {
  secret_id = "user-private-keys"
  replication {
    automatic = true
  }
}

# Example user data (in a real system, this would come from a database)
variable "users" {
  type = list(object({
    user_id     = string
    private_key = string
  }))
  default = [
    {
      user_id     = "user1",
      private_key = "user1_private_key_value" # Replace with a real key.
    },
    {
      user_id     = "user2",
      private_key = "user2_private_key_value" # Replace with a real key.
    },
  ]
}

# Create user-specific resources using the module
module "user_services" {
  for_each = { for user in var.users : user.user_id => user }
  source   = "./modules/user_service"

  user_id      = each.value.user_id
  private_key  = each.value.private_key
  project_id   = var.project_id
  region       = var.region
  source_bucket = var.source_bucket
  secret_id = google_secret_manager_secret.user_private_keys.id
}

# Cloud Scheduler to trigger the "start" cloud run service every 5 minutes
resource "google_cloud_scheduler_job" "start_cloud_run" {
  name             = "start-cloud-run"
  description      = "Triggers the start cloud run every 5 minutes"
  schedule         = "*/5 * * * *"
  time_zone        = "Etc/UTC"
  pubsub_target {
    topic_name = google_pubsub_topic.trigger_topic.name
    data = base64encode("trigger")
  }
}

# Pubsub Topic
resource "google_pubsub_topic" "trigger_topic" {
  name = "start-cloud-run-trigger"
}

# Grant cloud scheduler publish permissions to the topic.
resource "google_pubsub_topic_iam_member" "scheduler_pubsub" {
  topic = google_pubsub_topic.trigger_topic.id
  role  = "roles/pubsub.publisher"
  member = "serviceAccount:service-${var.project_id}@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
}