# Examples

Runnable versions of the first two examples live in the
[`examples/`](https://github.com/infrahouse/terraform-aws-github-role/tree/main/examples) directory of the
repository.

## Basic Role

The smallest useful configuration: a role for one repository plus a read-only policy.

```hcl
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
}

resource "aws_iam_role_policy_attachment" "read_only" {
  role       = module.github_role.github_role_name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

output "github_role_arn" {
  value = module.github_role.github_role_arn
}
```

## Least-Privilege Deployment Role

A role that may only run Terraform against one state bucket and one lock table:

```hcl
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
}

data "aws_iam_policy_document" "terraform_state" {
  statement {
    sid       = "ListStateBucket"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::my-terraform-state"]
  }

  statement {
    sid       = "ReadWriteState"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["arn:aws:s3:::my-terraform-state/aws-control/*"]
  }

  statement {
    sid       = "LockTable"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"]
    resources = ["arn:aws:dynamodb:us-west-2:123456789012:table/terraform-locks"]
  }
}

resource "aws_iam_role_policy" "terraform_state" {
  name   = "terraform-state-access"
  role   = module.github_role.github_role_name
  policy = data.aws_iam_policy_document.terraform_state.json
}
```

## Several Repositories

The trust policy covers a single repository, so create one role per repository:

```hcl
locals {
  repositories = ["aws-control", "website", "data-pipeline"]
}

module "github_role" {
  source   = "registry.infrahouse.com/infrahouse/github-role/aws"
  version  = "1.4.0"
  for_each = toset(local.repositories)

  gh_org_name = "infrahouse"
  repo_name   = each.value
}

output "github_role_arns" {
  value = { for repo, mod in module.github_role : repo => mod.github_role_arn }
}
```

## Custom Name and Longer Sessions

A migration job that runs for three hours needs both a longer role session and a matching request from the
workflow:

```hcl
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name          = "infrahouse"
  repo_name            = "data-pipeline"
  role_name            = "data-pipeline-migrations"
  max_session_duration = 10800 # 3 hours
}
```

```yaml
- uses: aws-actions/configure-aws-credentials@v5
  with:
    role-to-assume: arn:aws:iam::123456789012:role/data-pipeline-migrations
    aws-region: us-west-2
    role-duration-seconds: 10800
```

## Separate Plan and Apply Roles

Give the same repository two roles with different permissions and pick one per job:

```hcl
module "plan_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
  role_name   = "aws-control-plan"
}

module "apply_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
  role_name   = "aws-control-apply"
}

resource "aws_iam_role_policy_attachment" "plan_read_only" {
  role       = module.plan_role.github_role_name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
```

Both roles trust every workflow in the repository, so restrict *who* may run the apply job with a
[GitHub environment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
and required reviewers.

## Roles in Several Accounts

Provider aliases put a role for the same repository in each account:

```hcl
provider "aws" {
  alias  = "staging"
  region = "us-west-2"
  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/OrganizationAccountAccessRole"
  }
}

provider "aws" {
  alias  = "production"
  region = "us-west-2"
  assume_role {
    role_arn = "arn:aws:iam::222222222222:role/OrganizationAccountAccessRole"
  }
}

module "staging_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"
  providers = {
    aws = aws.staging
  }

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
}

module "production_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"
  providers = {
    aws = aws.production
  }

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
}
```

Each account needs its own GitHub OIDC identity provider.

## Pushing Images to ECR

```hcl
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name = "infrahouse"
  repo_name   = "website"
}

data "aws_iam_policy_document" "ecr_push" {
  statement {
    sid       = "GetAuthorizationToken"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "PushImages"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = ["arn:aws:ecr:us-west-2:123456789012:repository/website"]
  }
}

resource "aws_iam_role_policy" "ecr_push" {
  name   = "ecr-push"
  role   = module.github_role.github_role_name
  policy = data.aws_iam_policy_document.ecr_push.json
}
```
