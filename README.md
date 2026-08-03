# terraform-aws-github-role

[![Need Help?](https://img.shields.io/badge/Need%20Help%3F-Contact%20Us-0066CC)](https://infrahouse.com/contact)
[![Docs](https://img.shields.io/badge/docs-github.io-blue)](https://infrahouse.github.io/terraform-aws-github-role/)
[![Registry](https://img.shields.io/badge/Terraform-Registry-purple?logo=terraform)](https://registry.terraform.io/modules/infrahouse/github-role/aws/latest)
[![Release](https://img.shields.io/github/release/infrahouse/terraform-aws-github-role.svg)](https://github.com/infrahouse/terraform-aws-github-role/releases/latest)
[![AWS IAM](https://img.shields.io/badge/AWS-IAM-orange?logo=amazoniam)](https://aws.amazon.com/iam/)
[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=githubactions)](https://docs.github.com/en/actions)
[![Security](https://img.shields.io/github/actions/workflow/status/infrahouse/terraform-aws-github-role/vuln-scanner-pr.yml?label=Security)](https://github.com/infrahouse/terraform-aws-github-role/actions/workflows/vuln-scanner-pr.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

This Terraform module creates an AWS IAM role that a GitHub Actions workflow can assume through OpenID
Connect (OIDC). Workflows in the repository you name exchange their short-lived OIDC token for temporary AWS
credentials — no access keys stored as repository secrets, nothing to rotate.

The module creates the role and its trust policy only. It attaches **no** permission policies; you attach
exactly what your workflow needs to the returned role.

## Why This Module?

Writing the trust policy by hand is where GitHub OIDC setups usually go wrong: the federated principal, the
`aud` condition, and the `sub` pattern all have to be exactly right, and a single typo produces an opaque
`Not authorized to perform sts:AssumeRoleWithWebIdentity`. This module:

- **Gets the trust policy right** — federated principal, audience, and repository subject in one place
- **Handles GitHub's immutable subject claims** — matches both `repo:org/repo:*` and the newer
  `repo:org@<org_id>/repo@<repo_id>:*` format that new and renamed repositories receive from 2026-07-15
- **Stays unopinionated about permissions** — no bundled policies means no accidental over-privilege
- **Names roles predictably** — `ih-tf-<repo_name>-github` by default, so roles are easy to audit across
  accounts
- **Tags what it creates** — `created_by_module` and `module_version` tags make provenance obvious

## Features

- IAM role with a GitHub Actions OIDC trust policy, scoped to one `org/repo`
- Support for legacy and immutable GitHub subject claims
- Optional custom role name (`role_name`)
- Configurable session length (`max_session_duration`, 1 hour by default)
- Outputs the role name and ARN for policy attachment and workflow configuration
- Works with AWS provider 5.11+ and 6.x

## Quick Start

```hcl
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.4.0"

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
}

# The role has no permissions until you attach a policy.
resource "aws_iam_role_policy_attachment" "github_role_s3" {
  role       = module.github_role.github_role_name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

output "github_role_arn" {
  value = module.github_role.github_role_arn
}
```

The module looks up an existing GitHub OIDC identity provider in the account
(`https://token.actions.githubusercontent.com`). Create it once per AWS account with
[terraform-aws-gh-identity-provider](https://github.com/infrahouse/terraform-aws-gh-identity-provider):

```hcl
module "github_identity_provider" {
  source  = "registry.infrahouse.com/infrahouse/gh-identity-provider/aws"
  version = "1.1.1"
}
```

Then use the role in a workflow — `id-token: write` is what lets the runner request an OIDC token:

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

## Documentation

Full documentation is available at
[infrahouse.github.io/terraform-aws-github-role](https://infrahouse.github.io/terraform-aws-github-role/).

- [Getting Started](https://infrahouse.github.io/terraform-aws-github-role/getting-started/) — prerequisites
  and first deployment
- [Architecture](https://infrahouse.github.io/terraform-aws-github-role/architecture/) — how the OIDC trust
  relationship works
- [Configuration](https://infrahouse.github.io/terraform-aws-github-role/configuration/) — variable
  reference
- [Examples](https://infrahouse.github.io/terraform-aws-github-role/examples/) — common use cases
- [Security](https://infrahouse.github.io/terraform-aws-github-role/security/) — least privilege and
  hardening
- [Troubleshooting](https://infrahouse.github.io/terraform-aws-github-role/troubleshooting/) — common issues
  and solutions

## Security Best Practices

> **⚠️ Important**: do not grant `AdministratorAccess` to a GitHub Actions role. Anyone who can run a
> workflow in the repository then effectively owns the AWS account.

- **Least privilege** — attach resource-scoped policies for the exact actions the workflow performs
- **One role per repository and environment** — separate `staging` and `production`, ideally in separate
  accounts
- **Protect privileged workflows** — the role trusts every branch of the repository, so gate deployments
  with [GitHub environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
  and required reviewers
- **Short sessions** — keep `max_session_duration` as low as the job allows
- **Audit regularly** — `AssumeRoleWithWebIdentity` events in CloudTrail record which repository and ref used
  the role

More detail: [Security](https://infrahouse.github.io/terraform-aws-github-role/security/).

## Usage

<!-- BEGIN_TF_DOCS -->

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.5 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 5.11, < 7.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 5.11, < 7.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_iam_role.github](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_openid_connect_provider.github](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_openid_connect_provider) | data source |
| [aws_iam_policy_document.github-trust](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_gh_org_name"></a> [gh\_org\_name](#input\_gh\_org\_name) | GitHub organization name. | `string` | n/a | yes |
| <a name="input_max_session_duration"></a> [max\_session\_duration](#input\_max\_session\_duration) | Maximum session duration in seconds for the IAM role. | `number` | `3600` | no |
| <a name="input_repo_name"></a> [repo\_name](#input\_repo\_name) | Repository name in GitHub. Without the organization part. | `string` | n/a | yes |
| <a name="input_role_name"></a> [role\_name](#input\_role\_name) | Name of the role. If left unset, the role name will be `ih-tf-var.repo_name-github`. | `string` | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_github_role_arn"></a> [github\_role\_arn](#output\_github\_role\_arn) | ARN of the IAM role created for GitHub Actions |
| <a name="output_github_role_name"></a> [github\_role\_name](#output\_github\_role\_name) | Name of the IAM role created for GitHub Actions |
<!-- END_TF_DOCS -->

## Examples

See the [`examples/`](examples/) directory for complete working examples:

- [`examples/basic`](examples/basic) — a role for one repository with a read-only policy
- [`examples/least-privilege`](examples/least-privilege) — a deployment role scoped to a single S3 bucket

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache 2.0 License — see the [LICENSE](LICENSE) file for details.
