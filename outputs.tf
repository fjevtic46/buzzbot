# Example output (you can add more outputs as needed)
output "user_service_urls" {
  value = {
    for user_id, module in module.user_services :
    user_id => module.start_service_url
  }
}