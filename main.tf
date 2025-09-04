
resource "aws_iam_role" "github" {
  name                 = var.role_name == null ? "ih-tf-${var.repo_name}-github" : var.role_name
  description          = "Role for a GitHub Actions runner in repo ${var.repo_name}"
  assume_role_policy   = data.aws_iam_policy_document.github-trust.json
  max_session_duration = var.max_session_duration
  tags = merge(
    local.tags,
    {
      module_version : local.module_version
    }
  )
}
