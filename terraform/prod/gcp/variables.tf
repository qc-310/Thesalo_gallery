variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "db_url" {
  description = "Database connection string"
  type        = string
  sensitive   = true
}

variable "flask_secret" {
  description = "Flask secret key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth Client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret"
  type        = string
  sensitive   = true
}

variable "owner_email" {
  description = "Owner email address"
  type        = string
  sensitive   = true
}

variable "custom_domain" {
  description = "Custom domain for Cloud Run service mapping"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub Repository (owner/repo) for OIDC"
  type        = string
}

variable "billing_account" {
  description = "Billing Account ID (optional)"
  type        = string
  default     = ""
}
