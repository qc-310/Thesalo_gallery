terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

locals {
  # If environment is prod, use empty suffix.
  # Otherwise, use -environment suffix (e.g. -staging).
  suffix = var.environment == "prod" ? "" : "-${var.environment}"
}

# 1. Enable APIs (Project-wide)
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudtasks.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com" # Required for Budgets
  ])
  service            = each.key
  disable_on_destroy = false
}

# 1.5 Billing Budget
resource "google_billing_budget" "budget" {
  count           = var.billing_account != "" ? 1 : 0
  billing_account = var.billing_account
  display_name    = "Budget-${var.project_id}${local.suffix}"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = var.currency_code
      units         = var.budget_amount
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }
  threshold_rules {
    threshold_percent = 0.9
  }
  threshold_rules {
    threshold_percent = 1.0
  }

  depends_on = [google_project_service.apis]
}

# 2. Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "thesalo-repo${local.suffix}"
  description   = "Docker repository for Thesalo Gallery ${var.environment}"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]

  cleanup_policies {
    id     = "keep-last-5-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-old-versions"
    action = "DELETE"
    condition {
      tag_state = "ANY"
    }
  }
}

# --- Secrets Definition ---

resource "google_secret_manager_secret" "db_url" {
  secret_id = "thesalo-db-url${local.suffix}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_url" {
  secret      = google_secret_manager_secret.db_url.id
  secret_data = var.db_url
}

resource "google_secret_manager_secret" "flask_secret" {
  secret_id = "thesalo-flask-secret${local.suffix}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "flask_secret" {
  secret      = google_secret_manager_secret.flask_secret.id
  secret_data = var.flask_secret
}

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "thesalo-google-client-id${local.suffix}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "google_client_id" {
  secret      = google_secret_manager_secret.google_client_id.id
  secret_data = var.google_client_id
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "thesalo-google-client-secret${local.suffix}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "google_client_secret" {
  secret      = google_secret_manager_secret.google_client_secret.id
  secret_data = var.google_client_secret
}

resource "google_secret_manager_secret" "owner_email" {
  secret_id = "thesalo-owner-email${local.suffix}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "owner_email" {
  secret      = google_secret_manager_secret.owner_email.id
  secret_data = var.owner_email
}

# --- IAM for Secrets ---

resource "google_secret_manager_secret_iam_member" "sa_secret_accessor" {
  for_each = {
    "db_url"               = google_secret_manager_secret.db_url.id
    "flask_secret"         = google_secret_manager_secret.flask_secret.id
    "google_client_id"     = google_secret_manager_secret.google_client_id.id
    "google_client_secret" = google_secret_manager_secret.google_client_secret.id
    "owner_email"          = google_secret_manager_secret.owner_email.id
  }
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_sa.email}"
}

# 3. Cloud Storage Bucket
resource "google_storage_bucket" "uploads" {
  name          = "thesalo-uploads-${var.project_id}${local.suffix}-v2"
  location      = var.region
  storage_class = "STANDARD"

  force_destroy = true

  uniform_bucket_level_access = true

  # Prevent public access enforcement
  public_access_prevention = "enforced"

  lifecycle_rule {
    action {
      type = "AbortIncompleteMultipartUpload"
    }
    condition {
      age = 1 # days
    }
  }

  depends_on = [google_project_service.apis]
}

# 4. Service Account for Cloud Run
resource "google_service_account" "app_sa" {
  account_id   = "thesalo-app-sa${local.suffix}"
  display_name = "Thesalo Gallery App Service Account ${var.environment}"
  depends_on   = [google_project_service.apis]
}

# IAM Bindings

# Grant App SA access to Storage Object Admin on the bucket
resource "google_storage_bucket_iam_member" "sa_storage_admin" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app_sa.email}"
}

# Grant App SA permission to enqueue tasks

# 5. Cloud Tasks Queue
resource "google_cloud_tasks_queue" "default" {
  name       = "processing-queue${local.suffix}"
  location   = var.region
  depends_on = [google_project_service.apis]

  rate_limits {
    max_dispatches_per_second = 1.0 # Protect weak backend
    max_concurrent_dispatches = 2   # Prevent memory overflow
  }

  retry_config {
    max_attempts       = 5      # Don't retry forever
    max_retry_duration = "300s" # 5 minutes total
    min_backoff        = "1s"
    max_backoff        = "60s"
    max_doublings      = 16
  }
}

resource "google_cloud_tasks_queue_iam_member" "sa_task_enqueuer" {
  name   = google_cloud_tasks_queue.default.id
  role   = "roles/cloudtasks.enqueuer"
  member = "serviceAccount:${google_service_account.app_sa.email}"
}

# Grant App SA permission to act as itself
resource "google_service_account_iam_member" "sa_user_self" {
  service_account_id = google_service_account.app_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.app_sa.email}"
}

resource "google_service_account_iam_member" "sa_token_creator" {
  service_account_id = google_service_account.app_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.app_sa.email}"
}

# Grant App SA permission to act as itself (Project Level for broader compatibility)
resource "google_project_iam_member" "sa_user_project" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}

# 6. Cloud Run Service
resource "google_cloud_run_service" "default" {
  name       = "thesalo-web${local.suffix}"
  location   = var.region
  depends_on = [google_project_service.apis]

  template {
    spec {
      container_concurrency = 80
      timeout_seconds       = 300
      service_account_name  = google_service_account.app_sa.email
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/thesalo-repo${local.suffix}/thesalo-web:${var.image_tag}"

        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.uploads.name
        }
        env {
          name  = "CLOUD_TASKS_QUEUE_PATH"
          value = google_cloud_tasks_queue.default.id
        }
        env {
          name  = "STORAGE_BACKEND"
          value = "gcs"
        }
        env {
          name = "CLOUD_RUN_SERVICE_URL"
          # Avoid self-reference cycle; use custom domain if available, otherwise rely on app fallback
          value = var.custom_domain != "" ? "https://${var.custom_domain}" : ""
        }
        # Secrets
        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_url.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "FLASK_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.flask_secret.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "GOOGLE_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_id.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_client_secret.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "OWNER_EMAIL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.owner_email.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name  = "SERVICE_ACCOUNT_EMAIL"
          value = google_service_account.app_sa.email
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"  = tostring(var.min_instances)
        "autoscaling.knative.dev/maxScale"  = tostring(var.max_instances)
        "run.googleapis.com/cpu-throttling" = "true" # Ensure CPU is only allocated during request processing
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "sa_invoker" {
  service  = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.app_sa.email}"
}

resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 7. Custom Domain Mapping
resource "google_cloud_run_domain_mapping" "default" {
  # Create mapping only if custom_domain variable is provided
  count    = var.custom_domain != "" ? 1 : 0
  location = var.region
  name     = var.custom_domain

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.default.name
  }
}
