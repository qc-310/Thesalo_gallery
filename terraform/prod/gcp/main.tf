terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
  backend "gcs" {
    bucket = "thesalo-tfstate-thesalo-gallery"
    prefix = "prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "gcp_app" {
  source = "../../modules/gcp_base"

  project_id           = var.project_id
  region               = var.region
  environment          = "prod"
  db_url               = var.db_url
  flask_secret         = var.flask_secret
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
  owner_email          = var.owner_email
  custom_domain        = "www.thesalo-gallery.com" # Prod domain
  billing_account      = var.billing_account
  budget_amount        = 1000 # 1000 JPY
  image_tag            = var.image_tag
  startup_cpu_boost    = true
  max_instances        = 2
}

module "gh_oidc" {
  source      = "../../modules/gh_oidc"
  project_id  = var.project_id
  github_repo = var.github_repo
  pool_id     = "github-oidc-pool"
  provider_id = "github-oidc-provider"
}
