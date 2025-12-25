output "artifact_registry_url" {
  value = module.gcp_app.artifact_registry_url
}

output "storage_bucket_name" {
  value = module.gcp_app.storage_bucket_name
}

output "service_account_email" {
  value = module.gcp_app.service_account_email
}

output "cloud_tasks_queue_id" {
  value = module.gcp_app.cloud_tasks_queue_id
}

output "cloud_run_url" {
  value = module.gcp_app.cloud_run_url
}

output "domain_mapping_records" {
  value = module.gcp_app.domain_mapping_records
}

output "workload_identity_provider" {
  description = "GCP Workload Identity Provider ID"
  value       = module.gh_oidc.workload_identity_provider
}

output "ci_service_account_email" {
  description = "GCP Service Account Email for CI/CD"
  value       = module.gh_oidc.service_account_email
}
