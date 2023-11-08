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
  version     = "~> 1.0"
  gh_org_name = "infrahouse"
  repo_name   = "test"
}
```
Now that we have the role, let's attach the `AdministratorAccess` policy to it. 
```hcl
data "aws_iam_policy" "administrator-access" {
  name     = "AdministratorAccess"
}

resource "aws_iam_role_policy_attachment" "test-runner-admin-permissions" {
  policy_arn = data.aws_iam_policy.administrator-access.arn
  role       = module.test-runner.github_role_name.name
}
```

So, now we have the role can can be authenticated 
in [infrahouse/aws-control](https://github.com/infrahouse/aws-control) and have admin permissions in the AWS account.

> Note: It is not recommended to grant `AdministratorAccess` to a GitHub Actions worker.
> The example is for an illustration purpose only.

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.5 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.11 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 5.11 |

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
| <a name="input_repo_name"></a> [repo\_name](#input\_repo\_name) | Repository name in GitHub. Without the organization part. | `any` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_github_role_arn"></a> [github\_role\_arn](#output\_github\_role\_arn) | n/a |
| <a name="output_github_role_name"></a> [github\_role\_name](#output\_github\_role\_name) | n/a |
