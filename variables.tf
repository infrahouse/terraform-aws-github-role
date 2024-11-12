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
}
