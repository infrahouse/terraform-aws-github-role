# Security

OIDC removes the biggest risk of CI/CD credentials — long-lived access keys stored as repository secrets.
What is left to get right is *how much* the short-lived credentials may do.

## Grant Least Privilege

The module attaches no policies on purpose. Add only what the workflow needs:

```hcl
data "aws_iam_policy_document" "artifacts" {
  statement {
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::release-artifacts/website/*"]
  }
}

resource "aws_iam_role_policy" "artifacts" {
  name   = "publish-artifacts"
  role   = module.github_role.github_role_name
  policy = data.aws_iam_policy_document.artifacts.json
}
```

!!! danger
    Do not attach `AdministratorAccess`. Anyone who can merge — or run a workflow — in the repository then
    effectively owns the AWS account.

## Narrow the Subject Claim

By default the trust policy matches `repo:<org>/<repo>:*`, so any branch, tag, or pull request workflow
**in that repository** can assume the role: the effective boundary is "anyone with push access", not
"whatever ships through the default branch". That is fine for a role that reads state or runs
`terraform plan`. For a role with production permissions (pushing images, updating services, applying
infrastructure), narrow it with `subject_claims`:

```hcl
module "github_role" {
  # source and version as in Getting Started
  gh_org_name    = "infrahouse"
  repo_name      = "my-service"
  subject_claims = ["ref:refs/heads/main"]
}
```

- `ref:refs/heads/main` admits only workflows running on `main`, so getting access means getting a change
  merged. Pair it with branch protection that requires review.
- `environment:production` is checked by GitHub before it issues the token, so it composes with the
  environment's
  [deployment protection rules](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments):
  a deployment branch policy, and required reviewers where your GitHub plan offers them. Without such rules,
  a job on any branch can name the environment, which makes it weaker than `ref:refs/heads/main`.

The claim a job sends depends on how it runs; see [Configuration](configuration.md#subject_claims).

Plan around what the trust policy allows:

- **One role per repository.** Never share a role between repositories with different blast radii.
- **One role per environment.** Separate `staging` and `production` roles, ideally in separate AWS accounts.
- **Protect the apply path.** Narrow `subject_claims`, and use branch protection on `main` and
  [GitHub environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
  with protection rules, so privileged workflows need human approval.
- **Review workflow changes like IAM changes.** A pull request that edits `.github/workflows/` can use every
  permission the role has.

Workflows triggered by `pull_request` from a **fork** do not receive an OIDC token, so forks cannot assume
the role. Be careful with `pull_request_target`, which runs with the base repository's permissions.

## Watch the Policies You Attach

The module does not expose a `permissions_boundary` argument, so the guardrail is the set of policies you
attach. Keep them:

- **Resource-scoped** — name buckets, tables, and repositories explicitly instead of `"*"`
- **Versioned** — define them with `aws_iam_policy_document` in the same repository, so every permission
  change goes through review
- **Free of privilege escalation** — `iam:*`, `sts:AssumeRole` on broad resources, or `lambda:UpdateFunction*`
  on privileged functions let a workflow grant itself more than you intended

If your governance requires a permissions boundary on CI/CD roles, manage such roles outside this module.

## Keep Sessions Short

`max_session_duration` defaults to one hour. Longer sessions mean a leaked token stays useful longer — raise
it only for jobs that need it, and consider a dedicated role for those jobs.

## Repository Renames and Immutable Claims

GitHub is moving to immutable subject claims (`repo:org@<org_id>/repo@<repo_id>:*`) so that renaming a
repository does not silently transfer access. This module trusts both the legacy and immutable formats.
Because the numeric IDs are wildcards, a *new* repository created with a previously used name in the same
organization would also match — delete roles for repositories you retire.

## Audit Who Used the Role

Every assumption shows up in CloudTrail as `AssumeRoleWithWebIdentity`. The event records the token's
subject, which tells you the exact repository, ref, and workflow:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --query 'Events[].CloudTrailEvent' --output text | jq -r '.userIdentity.userName'
```

Find all roles this module created in an account:

```bash
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=created_by_module,Values=infrahouse/github-role/aws \
  --resource-type-filters iam:role
```

Review those roles periodically: remove roles for archived repositories and trim policies that grew during
incidents.

## Reporting a Vulnerability

Found a security issue in this module? See
[SECURITY.md](https://github.com/infrahouse/terraform-aws-github-role/blob/main/SECURITY.md) for how to
report it privately.
