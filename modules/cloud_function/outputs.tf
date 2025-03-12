output "service_account" {
  value = google_cloudfunctions2_function.function.service_config[0].service_account_email
}