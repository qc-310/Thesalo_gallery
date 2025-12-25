terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable APIs (Optional: Can be slow or fail if permissions missing. Often better to do manually, but including for completeness)
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudtasks.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "thesalo-repo"
  description   = "Docker repository for Thesalo Gallery"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# --- Secrets Definition ---

resource "google_secret_manager_secret" "db_url" {
  secret_id = "thesalo-db-url"
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
  secret_id = "thesalo-flask-secret"
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
  secret_id = "thesalo-google-client-id"
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
  secret_id = "thesalo-google-client-secret"
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
  secret_id = "thesalo-owner-email"
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
  name          = "thesalo-uploads-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  # Prevent public access enforcement
  public_access_prevention = "enforced"

  depends_on = [google_project_service.apis]
}

# 4. Service Account for Cloud Run
resource "google_service_account" "app_sa" {
  account_id   = "thesalo-app-sa"
  display_name = "Thesalo Gallery App Service Account"
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
# Note: Usually queues are project-level, but IAM can be set on Queue resource. 
# We need to create the queue first.

# 5. Cloud Tasks Queue
resource "google_cloud_tasks_queue" "default" {
  name       = "image-processing-queue"
  location   = var.region
  depends_on = [google_project_service.apis]
}

resource "google_cloud_tasks_queue_iam_member" "sa_task_enqueuer" {
  name   = google_cloud_tasks_queue.default.id
  role   = "roles/cloudtasks.enqueuer"
  member = "serviceAccount:${google_service_account.app_sa.email}"
}

# Grant App SA permission to act as itself (often needed for OIDC token generation targeting itself)
resource "google_service_account_iam_member" "sa_user_self" {
  service_account_id = google_service_account.app_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.app_sa.email}"
}

# 6. Cloud Run Service (Placeholder)
resource "google_cloud_run_service" "default" {
  name       = "thesalo-web"
  location   = var.region
  depends_on = [google_project_service.apis]

  template {
    spec {
      container_concurrency = 80 # Default is 80
      timeout_seconds       = 300
      service_account_name  = google_service_account.app_sa.email
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder
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
      }
    }
  }


  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Allow Cloud Tasks (via App SA) to invoke Cloud Run
# The App SA has 'enqueuer' role on the queue, and 'serviceAccountUser' on itself.
# When Cloud Tasks executes the task, it uses the OIDC token of the 'oidc_token.service_account_email' (which is App SA).
# So App SA needs 'run.invoker' on this Cloud Run service.
resource "google_cloud_run_service_iam_member" "sa_invoker" {
  service  = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.app_sa.email}"
}

# Allow unauthenticated access for the Web UI (User Access)
# Or restrict if using IAP (but this is public app).
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
