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
