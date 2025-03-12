output "url" {
  value = google_cloud_run_v2_service.service.uri
}
output "service_account" {
  value = google_cloud_run_v2_service.service.template[0].service_account
}