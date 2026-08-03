provider "aws" {
  region = var.region
}

# A GitHub OIDC identity provider must already exist in the account.
# See https://github.com/infrahouse/terraform-aws-gh-identity-provider
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.5.0"

  gh_org_name = var.gh_org_name
  repo_name   = var.repo_name
}

# The module creates no permissions, so attach what the workflow needs.
resource "aws_iam_role_policy_attachment" "read_only" {
  role       = module.github_role.github_role_name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
