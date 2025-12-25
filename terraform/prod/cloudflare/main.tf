terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">= 4.0"
    }
  }
  backend "local" {
    path = "terraform.tfstate"
  }
}

# Remote State to fetch GCP outputs (Cloud Run Domain Mapping)
data "terraform_remote_state" "gcp" {
  backend = "local"
  config = {
    path = "../../prod/gcp/terraform.tfstate"
  }
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "cloudflare_zone_id" {
  type = string
}

variable "custom_domain" {
  type = string
}

module "cloudflare_dns" {
  source = "../../modules/cloudflare_base"

  api_token   = var.cloudflare_api_token
  zone_id     = var.cloudflare_zone_id
  domain_name = var.custom_domain
  proxied     = true
  # Fetch dns records from GCP state
  cloud_run_domain_mapping_records = try(data.terraform_remote_state.gcp.outputs.domain_mapping_records, [])
}
