variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "github_repo" {
  description = "GitHub Repository Name (e.g., username/repo)"
  type        = string
}

variable "pool_id" {
  description = "Workload Identity Pool ID"
  type        = string
  default     = "github-actions-pool"
}

variable "provider_id" {
  description = "Workload Identity Provider ID"
  type        = string
  default     = "github-actions-provider"
}

variable "sa_id" {
  description = "Service Account ID for DevOps"
  type        = string
  default     = "devops-sa"
}
