output "github_role_name" {
  description = "Name of the IAM role created for GitHub Actions"
  value       = aws_iam_role.github.name
}

output "github_role_arn" {
  description = "ARN of the IAM role created for GitHub Actions"
  value       = aws_iam_role.github.arn
}
