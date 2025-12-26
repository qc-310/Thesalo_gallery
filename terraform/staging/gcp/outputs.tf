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
