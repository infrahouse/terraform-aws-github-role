## Data Sources
locals {
  gha_hostname = "token.actions.githubusercontent.com"
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
      values = [
        "repo:${var.gh_org_name}/${var.repo_name}:*"
      ]
    }
  }
}