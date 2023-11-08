resource "aws_iam_role" "github" {
  name               = "ih-tf-${var.repo_name}-github"
  description        = "Role for a GitHub Actions runner in repo ${var.repo_name}"
  assume_role_policy = data.aws_iam_policy_document.github-trust.json
}