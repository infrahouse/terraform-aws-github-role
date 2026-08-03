# InfraHouse github-role

Terraform module that creates an AWS IAM role a GitHub Actions workflow can assume via OpenID Connect (OIDC) —
no long-lived access keys, no secrets to rotate.

The module creates **only the role and its trust policy**. Permissions are yours to attach, which keeps the
module small and lets you follow the principle of least privilege for every repository.

## Features

- **Keyless authentication** — GitHub Actions exchanges its OIDC token for temporary AWS credentials
- **Repository-scoped trust** — only workflows in `<gh_org_name>/<repo_name>` can assume the role
- **Immutable subject claims** — accepts both the legacy `repo:org/repo:*` and the new
  `repo:org@<org_id>/repo@<repo_id>:*` subject formats GitHub rolls out for new and renamed repositories
- **No baked-in permissions** — attach exactly the policies your workflow needs
- **Configurable session length** — `max_session_duration` for long-running jobs
- **Predictable naming** — `ih-tf-<repo_name>-github` by default, overridable with `role_name`
- **Provenance tags** — `created_by_module` and `module_version` tags on the role

## Quick Start

```hcl
module "github_role" {
  source  = "registry.infrahouse.com/infrahouse/github-role/aws"
  version = "1.5.0"

  gh_org_name = "infrahouse"
  repo_name   = "aws-control"
}

data "aws_iam_policy" "s3_read_only" {
  name = "AmazonS3ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "github_role_s3" {
  policy_arn = data.aws_iam_policy.s3_read_only.arn
  role       = module.github_role.github_role_name
}

output "github_role_arn" {
  value = module.github_role.github_role_arn
}
```

The module expects a GitHub OIDC identity provider to already exist in the AWS account. See
[Getting Started](getting-started.md) for how to create it.

## Where to Next

- [Getting Started](getting-started.md) — prerequisites and your first deployment
- [Architecture](architecture.md) — how the OIDC trust relationship works
- [Configuration](configuration.md) — every input and output explained
- [Examples](examples.md) — common use cases
- [Security](security.md) — least privilege and hardening advice
- [Troubleshooting](troubleshooting.md) — errors and how to fix them
- [Changelog](changelog.md) — release history

## Support

Questions or need help with your AWS infrastructure? [Contact InfraHouse](https://infrahouse.com/contact).
