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
}

variable "environment" {
  description = "Environment name (prod, staging)"
  type        = string
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
  description = "Custom domain for Cloud Run service mapping (e.g. gallery.example.com). Leave empty to skip."
  type        = string
  default     = ""
}

# Cost Management Variables
variable "min_instances" {
  description = "Minimum number of Cloud Run instances (keep 0 for scale-to-zero)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances (limit costs)"
  type        = number
  default     = 1
}

variable "memory_limit" {
  description = "Memory limit per container"
  type        = string
  default     = "512Mi"
}

variable "cpu_limit" {
  description = "CPU limit per container"
  type        = string
  default     = "1000m"
}

variable "billing_account" {
  description = "Billing Account ID for Budget Alerts (e.g. 010101-010101-010101)"
  type        = string
  default     = "" # Default empty to skip if not provided
}

variable "budget_amount" {
  description = "Monthly budget amount"
  type        = number
  default     = 1000 # Default 1000 units
}

variable "currency_code" {
  description = "Currency code for budget"
  type        = string
  default     = "JPY"
}
