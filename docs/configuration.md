# Configuration

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|:--------:|-------------|
| `gh_org_name` | `string` | n/a | yes | GitHub organization (or user) that owns the repository |
| `repo_name` | `string` | n/a | yes | Repository name without the organization part |
| `role_name` | `string` | `null` | no | Role name. Defaults to `ih-tf-<repo_name>-github` |
| `max_session_duration` | `number` | `3600` | no | Maximum session duration in seconds (AWS allows 3600–43200) |
| `subject_claims` | `list(string)` | `["*"]` | no | Subject claim suffixes allowed to assume the role; `["*"]` allows any workflow |

### `gh_org_name`

The organization part of the repository slug. For `infrahouse/aws-control` it is `infrahouse`. It ends up in
the trust policy's `sub` condition, so it must match GitHub exactly, including case-insensitive spelling as
GitHub reports it in the token.

```hcl
gh_org_name = "infrahouse"
```

### `repo_name`

The repository part of the slug — `aws-control` in `infrahouse/aws-control`. Do **not** include the
organization or a leading slash; the module builds `repo:<gh_org_name>/<repo_name>:*` itself.

```hcl
repo_name = "aws-control"
```

### `role_name`

Leave it unset to get `ih-tf-<repo_name>-github`, which keeps role names predictable across accounts. Set it
when a naming convention, a length limit (IAM role names cap at 64 characters), or an existing role name
requires something else.

```hcl
role_name = "deploy-production"
```

!!! warning
    Changing `role_name` on an existing deployment replaces the role. The ARN changes, so update the
    `role-to-assume` value in every workflow that uses it.

### `max_session_duration`

How long the credentials handed to a workflow stay valid. AWS accepts 3600 (1 hour) through 43200
(12 hours). Raise it only for jobs that genuinely run longer than an hour — a shorter session limits the
blast radius of a leaked token.

```hcl
max_session_duration = 7200  # 2 hours
```

The workflow must also ask for the longer session:

```yaml
- uses: aws-actions/configure-aws-credentials@v5
  with:
    role-to-assume: ${{ vars.AWS_ROLE_ARN }}
    aws-region: us-west-2
    role-duration-seconds: 7200
```

### `subject_claims`

Which workflows of the repository may assume the role. Each entry is the part of the OIDC `sub` claim after
`repo:<org>/<repo>:`; the module adds that prefix in both the legacy and the immutable format, so you never
write `repo:<org>@*/<repo>@*:` yourself. The default `["*"]` allows every workflow in the repository.

Narrow it for a role with production access:

```hcl
subject_claims = ["ref:refs/heads/main"]       # workflows running on main
subject_claims = ["environment:production"]    # jobs that run in the production environment
```

The suffix GitHub puts in the token depends on the job:

| Job | Subject suffix |
|-----|----------------|
| Sets `environment: <name>` | `environment:<name>` |
| Triggered by `pull_request` | `pull_request` |
| Anything else (`push`, `workflow_dispatch`, `workflow_run`, `schedule`, ...) | `ref:refs/heads/<branch>` or `ref:refs/tags/<tag>` |

So a job with `environment: production` that runs on `main` matches `environment:production`, not
`ref:refs/heads/main`. Pick the claim your workflow actually sends.

`ref:refs/heads/main` still lets anyone who can get a workflow onto `main` assume the role, which is why branch
protection on `main` matters. `environment:production` is only as strong as the environment's protection
rules: without a deployment branch policy, a job on any branch can name the environment. See
[Security](security.md#narrow-the-subject-claim).

Entries must not be empty or start with `repo:` (the module would produce a pattern that never matches), and
the list must not be empty; the variable's validation rejects those.

## Outputs

| Name | Description |
|------|-------------|
| `github_role_arn` | ARN of the created role — the value for `role-to-assume` in a workflow |
| `github_role_name` | Name of the created role — use it when attaching policies |

```hcl
output "github_role_arn" {
  value = module.github_role.github_role_arn
}

resource "aws_iam_role_policy_attachment" "readonly" {
  role       = module.github_role.github_role_name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
```

## Provider Requirements

| Requirement | Version |
|-------------|---------|
| Terraform | `~> 1.5` |
| `hashicorp/aws` | `>= 5.11, < 7.0` |

The module inherits the `aws` provider from the calling configuration, so the role is created in whichever
account and region that provider points at (IAM is global; the region only affects the API endpoint).

## Tagging

The role is tagged with:

| Tag | Value |
|-----|-------|
| `created_by_module` | `infrahouse/github-role/aws` |
| `module_version` | Version of this module, for example `1.4.0` |

Add your own tags account-wide through the provider:

```hcl
provider "aws" {
  default_tags {
    tags = {
      created_by  = "infrahouse/aws-control"
      environment = "production"
    }
  }
}
```

## One Module Instance Per Repository

The trust policy targets a single repository. To grant several repositories access, instantiate the module
once per repository — see [Examples](examples.md).
