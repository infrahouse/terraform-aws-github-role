from textwrap import dedent

from os import path as osp, remove
import pytest
from pytest_infrahouse import terraform_apply

from tests.conftest import TERRAFORM_ROOT_DIR


@pytest.mark.parametrize(
    "aws_provider_version", ["~> 5.11", "~> 6.0"], ids=["aws-5", "aws-6"]
)
def test_module_aws_versions(
    aws_provider_version,
    boto3_session,
    keep_after,
    test_role_arn,
    aws_region,
):
    terraform_module_dir = osp.join(TERRAFORM_ROOT_DIR, "test_module")

    # Delete .terraform.lock.hcl to allow provider version changes
    lock_file_path = osp.join(terraform_module_dir, ".terraform.lock.hcl")
    try:
        remove(lock_file_path)
    except FileNotFoundError:
        pass

    # Update the AWS provider version in terraform.tf
    terraform_tf_path = osp.join(terraform_module_dir, "terraform.tf")

    with open(terraform_tf_path, "w") as fp:
        fp.write(
            dedent(
                f"""
                terraform {{
                  required_providers {{
                    aws = {{
                      source  = "hashicorp/aws"
                      version = "{aws_provider_version}"
                    }}
                  }}
                }}
                """
            )
        )

    with open(osp.join(terraform_module_dir, "terraform.tfvars"), "w") as fp:
        fp.write(
            dedent(
                f"""
                    region              = "{aws_region}"
                    """
            )
        )
        if test_role_arn:
            fp.write(
                dedent(
                    f"""
                    role_arn        = "{test_role_arn}"
                    """
                )
            )

    with terraform_apply(
        terraform_module_dir,
        destroy_after=not keep_after,
        json_output=True,
    ) as tf_output:
        role_arn = tf_output["role_arn"]["value"]
        role_name = tf_output["role_name"]["value"]
        assert role_arn

        # The module names the role after the repository unless role_name is given
        assert role_name == "ih-tf-test-github"

        # Verify the role actually exists in AWS
        iam = boto3_session.client("iam", region_name=aws_region)

        try:
            response = iam.get_role(RoleName=role_name)
            assert response["Role"]["Arn"] == role_arn
            assert response["Role"]["RoleName"] == role_name
            assert response["Role"]["MaxSessionDuration"] == 3600
        except iam.exceptions.NoSuchEntityException:
            pytest.fail(f"Role {role_name} was not found in AWS")

        # A GitHub Actions runner must be able to assume the role via OIDC,
        # with both the legacy and the immutable subject claim formats.
        statement = response["Role"]["AssumeRolePolicyDocument"]["Statement"][0]
        assert statement["Action"] == "sts:AssumeRoleWithWebIdentity"
        assert (
            "token.actions.githubusercontent.com" in statement["Principal"]["Federated"]
        )
        conditions = statement["Condition"]
        assert (
            conditions["StringEquals"]["token.actions.githubusercontent.com:aud"]
            == "sts.amazonaws.com"
        )
        assert sorted(
            conditions["StringLike"]["token.actions.githubusercontent.com:sub"]
        ) == sorted(
            [
                "repo:infrahouse/test:*",
                "repo:infrahouse@*/test@*:*",
            ]
        )
