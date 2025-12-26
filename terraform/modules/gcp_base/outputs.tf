output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.name}"
}

output "storage_bucket_name" {
  value = google_storage_bucket.uploads.name
}

output "service_account_email" {
  value = google_service_account.app_sa.email
}

output "cloud_tasks_queue_id" {
  value = google_cloud_tasks_queue.default.id
}

output "cloud_run_url" {
  value = google_cloud_run_service.default.status[0].url
}

output "domain_mapping_records" {
  value = length(google_cloud_run_domain_mapping.default) > 0 ? google_cloud_run_domain_mapping.default[0].status[0].resource_records : []
}
