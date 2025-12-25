output "workload_identity_provider" {
  description = "The Workload Identity Provider resource name"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}

output "service_account_email" {
  description = "The Email of the DevOps Service Account"
  value       = google_service_account.devops_sa.email
}
