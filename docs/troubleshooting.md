# Troubleshooting

## `terraform plan` fails: no matching OIDC provider

```text
Error: no matching OpenID Connect Provider found
  with data.aws_iam_openid_connect_provider.github
```

The account has no GitHub OIDC identity provider, or the credentials point at the wrong account.

```bash
aws sts get-caller-identity           # is this the account you meant?
aws iam list-open-id-connect-providers # is the GitHub provider there?
```

Create it once per account:

```hcl
module "github_identity_provider" {
  source  = "registry.infrahouse.com/infrahouse/gh-identity-provider/aws"
  version = "1.1.1"
}
```

The provider URL must be exactly `https://token.actions.githubusercontent.com`.

## Workflow fails: `Not authorized to perform sts:AssumeRoleWithWebIdentity`

The most common failure, and it always means the token's claims did not satisfy the trust policy. Work
through these in order:

1. **Missing `id-token: write`.** Without it the runner cannot mint an OIDC token at all:

    ```yaml
    permissions:
      id-token: write
      contents: read
    ```

2. **Wrong repository.** The role only trusts `<gh_org_name>/<repo_name>`. A workflow in another repository
   — including one that was renamed or moved to another organization — is rejected. Check the module inputs
   against the repository slug, character for character.
3. **Fork pull request.** `pull_request` runs from forks get no OIDC token. Use `workflow_dispatch`, a
   `pull_request_target` job you have reviewed carefully, or run deployments only from branches in the base
   repository.
4. **Wrong ARN.** `role-to-assume` must be the ARN from `module.<name>.github_role_arn` for *this* account.
5. **Custom audience.** The trust policy requires `aud = sts.amazonaws.com`. Remove any `audience:` input
   from `aws-actions/configure-aws-credentials` unless the provider is configured for it.
6. **Old module version after a repository rename.** Renamed repositories get immutable subject claims
   (`repo:org@<org_id>/repo@<repo_id>:*`). Module versions before that support only matched the legacy
   format — upgrade the module and re-apply.

To see the claim AWS actually received, print the subject in the workflow:

```yaml
- name: Show OIDC subject
  uses: actions/github-script@v7
  with:
    script: |
      const token = await core.getIDToken('sts.amazonaws.com')
      const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString())
      core.info(`sub: ${payload.sub}`)
      core.info(`aud: ${payload.aud}`)
```

Compare the printed `sub` with the patterns in the role's trust policy:

```bash
aws iam get-role --role-name ih-tf-aws-control-github \
  --query 'Role.AssumeRolePolicyDocument.Statement[0].Condition'
```

## Workflow fails: `Credentials could not be loaded`

`aws-actions/configure-aws-credentials` could not obtain a token. Usually the job is missing
`permissions: id-token: write`, or the step runs on a self-hosted runner behind a proxy that blocks
`token.actions.githubusercontent.com`.

## `The requested DurationSeconds exceeds the MaxSessionDuration set for this role`

The workflow asked for a longer session than the role allows. Raise the module input and the workflow input
together:

```hcl
max_session_duration = 7200
```

```yaml
role-duration-seconds: 7200
```

AWS caps `max_session_duration` at 43200 seconds (12 hours).

## `EntityAlreadyExists: Role with name ih-tf-<repo>-github already exists`

A role with that name already exists in the account — often created by an earlier manual setup or another
Terraform state. Either import it:

```bash
terraform import 'module.github_role.aws_iam_role.github' ih-tf-aws-control-github
```

…or pick a different name with `role_name`.

## Role assumed successfully, but AWS calls return `AccessDenied`

Authentication worked; authorization did not. This module attaches **no** permissions, so a fresh role can
do nothing until you attach a policy. List what is attached:

```bash
aws iam list-attached-role-policies --role-name ih-tf-aws-control-github
aws iam list-role-policies --role-name ih-tf-aws-control-github
```

See [Examples](examples.md) for policy patterns.

## `Role name must contain only ... and be 1–64 characters`

IAM role names are limited to 64 characters, and the default name adds 11 characters to the repository name
(`ih-tf-` + `-github`). Long repository names need an explicit shorter `role_name`.

## Terraform wants to replace the role

Changing `role_name` (or `repo_name`, when `role_name` is unset) forces a new role: the name is immutable in
IAM. The replacement gets a new ARN, so update `role-to-assume` in the workflows that reference it. Changing
`max_session_duration` or tags updates the role in place.

## Still stuck?

- Look up the failed attempt in CloudTrail — `AssumeRoleWithWebIdentity` events include the rejected subject
- Open an issue at
  [github.com/infrahouse/terraform-aws-github-role/issues](https://github.com/infrahouse/terraform-aws-github-role/issues)
- [Contact InfraHouse](https://infrahouse.com/contact) if you would like help with your setup
