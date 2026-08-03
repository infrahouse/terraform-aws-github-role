output "github_role_arn" {
  description = "Role ARN to pass to aws-actions/configure-aws-credentials as `role-to-assume`."
  value       = module.github_role.github_role_arn
}

output "github_role_name" {
  description = "Name of the created IAM role."
  value       = module.github_role.github_role_name
}
