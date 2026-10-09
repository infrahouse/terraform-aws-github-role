## Data Sources
locals {
  gha_hostname = "token.actions.githubusercontent.com"

  # Every allowed claim suffix in both repository-name formats:
  # - legacy, with mutable org/repo names: repo:<org>/<repo>:<claim>
  # - immutable, mandatory for new/renamed repos from 2026-07-15. GitHub injects numeric org/repo IDs after an
  #   "@": repo:<org>@<org_id>/<repo>@<repo_id>:<claim>
  subject_patterns = flatten([
    for claim in var.subject_claims : [
      "repo:${var.gh_org_name}/${var.repo_name}:${claim}",
      "repo:${var.gh_org_name}@*/${var.repo_name}@*:${claim}",
    ]
  ])
}

data "aws_iam_openid_connect_provider" "github" {
  url = "https://${local.gha_hostname}"
}

data "aws_iam_policy_document" "github-trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type = "Federated"
      identifiers = [
        data.aws_iam_openid_connect_provider.github.arn
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.gha_hostname}:aud"
      values = [
        "sts.amazonaws.com"
      ]
    }
    condition {
      test     = "StringLike"
      variable = "${local.gha_hostname}:sub"
      values   = local.subject_patterns
    }
  }
}
