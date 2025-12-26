terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">= 4.0"
    }
  }
}

variable "api_token" {
  description = "Cloudflare API Token"
  type        = string
  sensitive   = true
}

variable "zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "domain_name" {
  description = "The target domain name (e.g. gallery.example.com or staging.gallery.example.com)"
  type        = string
}

variable "cloud_run_domain_mapping_records" {
  description = "The resource records output from google_cloud_run_domain_mapping"
  type = list(object({
    name   = string
    rrdata = string
    type   = string
  }))
  default = []
}

variable "proxied" {
  description = "Whether to enable Cloudflare Proxy (Orange Cloud). Recommended false for initial SSL setup."
  type        = bool
  default     = false
}

provider "cloudflare" {
  api_token = var.api_token
}

# Add DNS records based on Cloud Run Domain Mapping output
resource "cloudflare_dns_record" "cloud_run_record" {
  count   = length(var.cloud_run_domain_mapping_records)
  zone_id = var.zone_id
  name    = var.domain_name
  type    = var.cloud_run_domain_mapping_records[count.index].type
  content = var.cloud_run_domain_mapping_records[count.index].rrdata
  proxied = var.proxied
  ttl     = 300 # 5 min TTL
}
