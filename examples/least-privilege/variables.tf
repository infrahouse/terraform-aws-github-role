variable "region" {
  description = "AWS region where the Terraform provider operates. IAM roles themselves are global."
  type        = string
  default     = "us-west-2"
}

variable "gh_org_name" {
  description = "GitHub organization name. For instance, `infrahouse` in `infrahouse/aws-control`."
  type        = string
}

variable "repo_name" {
  description = "Repository name without the organization part. For instance, `aws-control`."
  type        = string
}

variable "role_name" {
  description = "Name of the role. If left unset, the role name will be `ih-tf-<repo_name>-github`."
  type        = string
  default     = null
}

variable "artifacts_bucket" {
  description = <<-EOT
    Name of an existing S3 bucket where the workflow publishes artifacts.
    The role gets access to the `<repo_name>/` prefix of this bucket only.
  EOT
  type        = string
}

variable "max_session_duration" {
  description = "Maximum session duration in seconds for the IAM role."
  type        = number
  default     = 3600

  validation {
    condition     = var.max_session_duration >= 3600 && var.max_session_duration <= 43200
    error_message = "max_session_duration must be between 3600 and 43200 seconds. Got: ${var.max_session_duration}"
  }
}
