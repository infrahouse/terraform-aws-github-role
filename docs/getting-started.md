# Getting Started

This page walks you from an empty AWS account to a GitHub Actions workflow that runs `aws s3 ls` without any
static credentials.

## Prerequisites

- **Terraform** `~> 1.5`
- **AWS provider** `>= 5.11, < 7.0` and credentials that may create IAM roles
- **A GitHub OIDC identity provider** in the AWS account (see below) — the module looks it up, it does not
  create it
- **Access to `registry.infrahouse.com`** if you consume the module from the InfraHouse registry

## Step 1: Create the GitHub OIDC Identity Provider

The identity provider is an account-wide resource: create it **once per AWS account**, not once per
repository.

```hcl
module "github_identity_provider" {
  source  = "registry.infrahouse.com/infrahouse/gh-identity-provider/aws"
  version = "1.1.1"
}
```

If the provider already exists (for example, created by another team), skip this step. You can verify it with:

```bash
aws iam list-open-id-connect-providers
```

The URL of the provider must be `https://token.actions.githubusercontent.com`.

## Step 2: Create the Role

```hcl
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
}
```

`terraform apply` creates an IAM role named `ih-tf-aws-control-github` whose trust policy allows GitHub
Actions workflows in `infrahouse/aws-control` to assume it.

## Step 3: Attach Permissions

The role starts with no permissions at all. Attach what the workflow needs — and nothing more:

```hcl
resource "aws_iam_role_policy" "state_bucket_access" {
  name = "terraform-state-access"
  role = module.github_role.github_role_name
  policy = data.aws_iam_policy_document.state_bucket_access.json
}

data "aws_iam_policy_document" "state_bucket_access" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::my-terraform-state/*"]
  }
}
```

## Step 4: Publish the Role ARN

```hcl
output "github_role_arn" {
  description = "Role for GitHub Actions in infrahouse/aws-control"
  value       = module.github_role.github_role_arn
}
```

The ARN is not a secret, but storing it as a repository variable or secret keeps workflows tidy:

```bash
gh variable set AWS_ROLE_ARN --repo infrahouse/aws-control --body "$(terraform output -raw github_role_arn)"
```

## Step 5: Use the Role in a Workflow

The `id-token: write` permission is what lets the runner request an OIDC token. Without it the login step
fails.

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v5

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: us-west-2

      - name: Verify access
        run: aws sts get-caller-identity
```

## Step 6: Verify

Run the workflow. `aws sts get-caller-identity` prints an assumed-role ARN like:

```text
arn:aws:sts::123456789012:assumed-role/ih-tf-aws-control-github/GitHubActions
```

If it fails, [Troubleshooting](troubleshooting.md) covers the usual causes.

## Next Steps

- [Configuration](configuration.md) — role name, session duration, and other inputs
- [Security](security.md) — how to keep the role's permissions tight
- [Examples](examples.md) — multi-repository and multi-environment setups
