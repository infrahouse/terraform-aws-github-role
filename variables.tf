variable "role_name" {
  description = "Name of the role. If left unset, the role name will be `ih-tf-var.repo_name-github`."
  type        = string
  default     = null
}

variable "gh_org_name" {
  description = "GitHub organization name."
  type        = string
}

variable "repo_name" {
  description = "Repository name in GitHub. Without the organization part."
  type        = string
}

variable "max_session_duration" {
  description = "Maximum session duration in seconds for the IAM role."
  type        = number
  default     = 3600
}

variable "subject_claims" {
  description = <<-EOT
    Subject claim suffixes allowed to assume the role: the part of the OIDC `sub` claim after `repo:<org>/<repo>:`.
    The default `["*"]` lets any workflow in the repository assume it. Narrow it for a role with production
    access, e.g. `["ref:refs/heads/main"]` or `["environment:production"]`. A job that names an environment gets
    an `environment:<name>` subject, not a `ref:` one. The module matches each suffix in both the legacy and the
    immutable repository-name format.
  EOT
  type        = list(string)
  default     = ["*"]

  validation {
    condition = length(var.subject_claims) > 0 && alltrue([
      for claim in var.subject_claims : claim != "" && !startswith(claim, "repo:")
    ])
    error_message = <<-EOT
      subject_claims must be a non-empty list of claim suffixes such as "ref:refs/heads/main" or
      "environment:production", without the "repo:<org>/<repo>:" prefix (the module adds it). Use ["*"] to allow
      any workflow in the repository. Got: ${jsonencode(var.subject_claims)}
    EOT
  }
}
