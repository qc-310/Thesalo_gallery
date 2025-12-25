terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

# 1. Enable IAM Credentials API (Required for Workload Identity)
resource "google_project_service" "required_apis" {
  for_each = toset([
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Workload Identity Pool
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = var.pool_id
  display_name              = "GitHub Actions Pool"
  description               = "Identity pool for GitHub Actions"
  disabled                  = false
  depends_on                = [google_project_service.required_apis]
}

# 3. Workload Identity Provider
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  display_name                       = "GitHub Actions Provider"
  description                        = "OIDC Provider for GitHub Actions"
  disabled                           = false

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# 4. Service Account for DevOps (CI/CD)
resource "google_service_account" "devops_sa" {
  account_id   = var.sa_id
  display_name = "DevOps Service Account for GitHub Actions"
}

# 5. Allow GitHub Actions (from specific repo) to impersonate this Service Account
resource "google_service_account_iam_member" "workload_identity_user_repo" {
  service_account_id = google_service_account.devops_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}"
}

# 6. Grant Permissions to the Service Account
# Note: "Editor" is a broad role. For production hardening, split into granular roles.
resource "google_project_iam_member" "devops_sa_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.devops_sa.email}"
}

resource "google_project_iam_member" "devops_sa_cloudtasks" {
  project = var.project_id
  role    = "roles/cloudtasks.admin"
  member  = "serviceAccount:${google_service_account.devops_sa.email}"
}

resource "google_project_iam_member" "devops_sa_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.devops_sa.email}"
}

resource "google_project_iam_member" "devops_sa_artoregistry" {
  project = var.project_id
  role    = "roles/artifactregistry.admin" # Writer needed for push, Admin for create if needed
  member  = "serviceAccount:${google_service_account.devops_sa.email}"
}

resource "google_project_iam_member" "devops_sa_run" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.devops_sa.email}"
}

resource "google_project_iam_member" "devops_sa_iam_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.devops_sa.email}"
}
