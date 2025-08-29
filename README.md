# terraform-aws-github-role
The module creates an IAM role that can be used by a GitHub Action worker.

The role doesn't have any attached policies. Instead, the module returns the role's ARN and name.
The user is expected to attach necessary policies to the role.

## Usage

Let's say we have a GitHub repo [infrahouse/aws-control](https://github.com/infrahouse/aws-control).
We want to create a role that we can use in GitHub Actions 
in the [infrahouse/aws-control](https://github.com/infrahouse/aws-control) repository.

The module will create the role. A GitHub Actions worker 
in the [infrahouse/aws-control](https://github.com/infrahouse/aws-control) repo will be able to assume it.
```hcl
module "test-runner" {
  source      = "infrahouse/github-role/aws"
  version     = "1.0.0"
  gh_org_name = "infrahouse"
  repo_name   = "test"
  role_name   = "my-custom-github-role"  # Optional: defaults to ih-tf-{repo_name}-github
}
```
Now that we have the role, let's attach the `AdministratorAccess` policy to it. 
```hcl
data "aws_iam_policy" "administrator-access" {
  name     = "AdministratorAccess"
}

resource "aws_iam_role_policy_attachment" "test-runner-admin-permissions" {
  policy_arn = data.aws_iam_policy.administrator-access.arn
  role       = module.test-runner.github_role_name
}
```

So, now we have the role that can be authenticated
 in [infrahouse/aws-control](https://github.com/infrahouse/aws-control) and have admin permissions in the AWS account.

## Security Best Practices

> **⚠️ Important**: It is not recommended to grant `AdministratorAccess` to a GitHub Actions worker.
> The example above is for illustration purposes only.

Follow these security best practices:

- **Principle of Least Privilege**: Only grant the minimum permissions required for your workflow
- **Use Specific Policies**: Create custom policies or use AWS managed policies that match your specific needs
- **Environment Separation**: Use different roles for different environments (dev, staging, prod)
- **Regular Audits**: Periodically review and rotate the permissions attached to your GitHub Actions roles
- **Conditional Access**: Consider adding conditions to your trust policy to restrict access by branch, repository, or other factors

Example of a more secure policy attachment:
```hcl
data "aws_iam_policy" "s3-read-only" {
  name = "AmazonS3ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "test-runner-s3-permissions" {
  policy_arn = data.aws_iam_policy.s3-read-only.arn
  role       = module.test-runner.github_role_name
}
```

## Prerequisites

Before using this module, you need to set up an OpenID Connect (OIDC) identity provider in your AWS account for GitHub Actions. You can use the [terraform-aws-gh-identity-provider](https://github.com/infrahouse/terraform-aws-gh-identity-provider) module:

```hcl
module "github_identity_provider" {
  source = "infrahouse/gh-identity-provider/aws"
}
```

> **Note**: This OIDC provider setup is required only once per AWS account.

## GitHub Actions Usage

Once the role is created and the OIDC provider is set up, you can use it in your GitHub Actions workflows:

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
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Deploy resources
        run: |
          # Your deployment commands here
          aws s3 ls  # Example command using assumed role
```

> **Note**: Set `AWS_ROLE_ARN` as a repository secret with the value from `module.test-runner.github_role_arn`

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
| <a name="input_repo_name"></a> [repo\_name](#input\_repo\_name) | Repository name in GitHub. Without the organization part. | `string` | n/a | yes |
| <a name="input_role_name"></a> [role\_name](#input\_role\_name) | Name of the role. If left unset, the role name will be `ih-tf-var.repo_name-github`. | `string` | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_github_role_arn"></a> [github\_role\_arn](#output\_github\_role\_arn) | ARN of the IAM role created for GitHub Actions |
| <a name="output_github_role_name"></a> [github\_role\_name](#output\_github\_role\_name) | Name of the IAM role created for GitHub Actions |
