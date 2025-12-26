terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
}

module "gcp_app" {
  source = "../../modules/gcp_base"

  project_id           = var.project_id
  region               = var.region
  environment          = "staging"
  db_url               = var.db_url
  flask_secret         = var.flask_secret
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
  owner_email          = var.owner_email
  custom_domain        = var.custom_domain
  billing_account      = var.billing_account
  budget_amount        = 1000 # 1000 JPY
  image_tag            = var.image_tag
}
