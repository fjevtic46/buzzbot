variable "user_id" {
  type = string
}

variable "private_key" {
  type = string
}

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "source_bucket" {
  type = string
}

variable "secret_id" {
  type = string
}

module "start_service" {
  source = "../cloud_run_service"

  name     = "${var.user_id}-start"
  location = var.region
  image    = "gcr.io/${var.project_id}/start-service:latest"
  envs = [
    {
      name  = "PROJECT_ID"
      value = var.project_id
    },
    {
      name = "REGION"
      value = var.region
    },
    {
      name = "FUNCTION_TRIGGER_1"
      value = "${var.user_id}-trigger_function_1"
    },
    {
      name = "FUNCTION_TRIGGER_2"
      value = "${var.user_id}-trigger_function_2"
    },
    {
      name = "FUNCTION_TRIGGER_3"
      value = "${var.user_id}-trigger_function_3"
    },
    {
        name = "USER_ID"
        value = var.user_id
    }
  ]
}

module "trigger_function_1" {
  source = "../cloud_function"

  name          = "${var.user_id}-trigger_function_1"
  location      = var.region
  runtime       = "python39"
  entry_point   = "main"
  source_bucket = var.source_bucket
  source_object = "trigger_function_1.zip"
  envs = {
    "FUNCTION_TRIGGER_2" = "${var.user_id}-trigger_function_2"
    "USER_ID" = var.user_id
  }
}

module "trigger_function_2" {
  source = "../cloud_function"

  name          = "${var.user_id}-trigger_function_2"
  location      = var.region
  runtime       = "python39"
  entry_point   = "main"
  source_bucket = var.source_bucket
  source_object = "trigger_function_2.zip"
  envs = {
    "FUNCTION_TRIGGER_3" = "${var.user_id}-trigger_function_3"
    "USER_ID" = var.user_id
  }
}

module "trigger_function_3" {
  source = "../cloud_function"

  name          = "${var.user_id}-trigger_function_3"
  location      = var.region
  runtime       = "python39"
  entry_point   = "main"
  source_bucket = var.source_bucket
  source_object = "trigger_function_3.zip"
  envs = {
    "USER_ID" = var.user_id
  }
}

resource "google_secret_manager_secret_version" "user_private_key_version" {
  secret = var.secret_id
  secret_data = base64encode(var.private_key)
}

resource "google_secret_manager_secret_iam_member" "cloud_run_access" {
  secret_id = var.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.start_service.service_account}"
}

resource "google_secret_manager_secret_iam_member" "cloud_functions_access_1" {
  secret_id = var.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.trigger_function_1.service_account}"
}

resource "google_secret_manager_secret_iam_member" "cloud_functions_access_2" {
  secret_id = var.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.trigger_function_2.service_account}"
}

resource "google_secret_manager_secret_iam_member" "cloud_functions_access_3" {
  secret_id = var.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.trigger_function_3.service_account}"
}

output "start_service_url" {
  value = module.start_service.url
}