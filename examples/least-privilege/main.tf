provider "aws" {
  region = var.region
}

module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.5.0"

  gh_org_name          = var.gh_org_name
  repo_name            = var.repo_name
  role_name            = var.role_name
  max_session_duration = var.max_session_duration
}

data "aws_s3_bucket" "artifacts" {
  bucket = var.artifacts_bucket
}

# Only the actions the deployment workflow performs, only on its own prefix.
data "aws_iam_policy_document" "publish_artifacts" {
  statement {
    sid       = "ListArtifactsBucket"
    actions   = ["s3:ListBucket"]
    resources = [data.aws_s3_bucket.artifacts.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${var.repo_name}/*"]
    }
  }

  statement {
    sid = "PublishArtifacts"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${data.aws_s3_bucket.artifacts.arn}/${var.repo_name}/*"]
  }
}

resource "aws_iam_role_policy" "publish_artifacts" {
  name   = "publish-artifacts"
  role   = module.github_role.github_role_name
  policy = data.aws_iam_policy_document.publish_artifacts.json
}
