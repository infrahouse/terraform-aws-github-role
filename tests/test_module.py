import json
from subprocess import run
from textwrap import dedent
from typing import List, Optional

from os import path as osp, remove
import pytest
from pytest_infrahouse import terraform_apply

from tests.conftest import TERRAFORM_ROOT_DIR

SUBJECT_CLAIM_KEY = "token.actions.githubusercontent.com:sub"


def prepare_test_module(
    aws_provider_version: str,
    aws_region: str,
    test_role_arn: Optional[str],
    subject_claims: Optional[List[str]] = None,
) -> str:
    """
    Write terraform.tf and terraform.tfvars of the test root module.

    :param aws_provider_version: Version constraint for the hashicorp/aws provider.
    :param aws_region: AWS region for the provider.
    :param test_role_arn: Role the provider assumes, or None to use the current credentials.
    :param subject_claims: Value for the module's subject_claims, or None to keep its default.
    :return: Path to the test root module.
    """
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
        fp.write(dedent(f"""
                terraform {{
                  required_providers {{
                    aws = {{
                      source  = "hashicorp/aws"
                      version = "{aws_provider_version}"
                    }}
                  }}
                }}
                """))

    with open(osp.join(terraform_module_dir, "terraform.tfvars"), "w") as fp:
        fp.write(dedent(f"""
                    region              = "{aws_region}"
                    """))
        if test_role_arn:
            fp.write(dedent(f"""
                    role_arn        = "{test_role_arn}"
                    """))
        if subject_claims is not None:
            fp.write(f"\nsubject_claims = {json.dumps(subject_claims)}\n")

    return terraform_module_dir


def get_role(boto3_session, aws_region: str, role_name: str) -> dict:
    """
    Look up the role in AWS.

    :param boto3_session: boto3 session with access to the test account.
    :param aws_region: AWS region for the IAM client.
    :param role_name: Name of the role.
    :return: The ``Role`` element of the GetRole response.
    """
    iam = boto3_session.client("iam", region_name=aws_region)
    try:
        return iam.get_role(RoleName=role_name)["Role"]
    except iam.exceptions.NoSuchEntityException:
        pytest.fail(f"Role {role_name} was not found in AWS")


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
    terraform_module_dir = prepare_test_module(
        aws_provider_version, aws_region, test_role_arn
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
        role = get_role(boto3_session, aws_region, role_name)
        assert role["Arn"] == role_arn
        assert role["RoleName"] == role_name
        assert role["MaxSessionDuration"] == 3600

        # A GitHub Actions runner must be able to assume the role via OIDC,
        # with both the legacy and the immutable subject claim formats.
        statement = role["AssumeRolePolicyDocument"]["Statement"][0]
        assert statement["Action"] == "sts:AssumeRoleWithWebIdentity"
        assert (
            "token.actions.githubusercontent.com" in statement["Principal"]["Federated"]
        )
        conditions = statement["Condition"]
        assert (
            conditions["StringEquals"]["token.actions.githubusercontent.com:aud"]
            == "sts.amazonaws.com"
        )
        # The default subject_claims = ["*"] lets any workflow in the repository assume the role.
        assert sorted(conditions["StringLike"][SUBJECT_CLAIM_KEY]) == sorted(
            [
                "repo:infrahouse/test:*",
                "repo:infrahouse@*/test@*:*",
            ]
        )


def test_subject_claims_narrowed(
    boto3_session,
    keep_after,
    test_role_arn,
    aws_region,
):
    """
    A narrowed subject_claims allows only the listed claims, each in both the legacy and the
    immutable repository-name format, and nothing repository-wide.
    """
    terraform_module_dir = prepare_test_module(
        "~> 6.0",
        aws_region,
        test_role_arn,
        subject_claims=["ref:refs/heads/main", "environment:production"],
    )

    with terraform_apply(
        terraform_module_dir,
        destroy_after=not keep_after,
        json_output=True,
    ) as tf_output:
        role = get_role(boto3_session, aws_region, tf_output["role_name"]["value"])
        statement = role["AssumeRolePolicyDocument"]["Statement"][0]
        assert sorted(
            statement["Condition"]["StringLike"][SUBJECT_CLAIM_KEY]
        ) == sorted(
            [
                "repo:infrahouse/test:ref:refs/heads/main",
                "repo:infrahouse@*/test@*:ref:refs/heads/main",
                "repo:infrahouse/test:environment:production",
                "repo:infrahouse@*/test@*:environment:production",
            ]
        )


def test_subject_claims_rejects_full_subject(
    test_role_arn,
    aws_region,
):
    """
    A claim that already carries the "repo:<org>/<repo>:" prefix would never match a token,
    so the plan must fail on validation instead of creating a role nobody can assume.
    """
    terraform_module_dir = prepare_test_module(
        "~> 6.0",
        aws_region,
        test_role_arn,
        subject_claims=["repo:infrahouse/test:ref:refs/heads/main"],
    )
    run(
        ["terraform", "init", "-input=false", "-no-color"],
        cwd=terraform_module_dir,
        check=True,
    )
    plan = run(
        ["terraform", "plan", "-input=false", "-no-color"],
        cwd=terraform_module_dir,
        capture_output=True,
        text=True,
    )
    assert plan.returncode != 0
    # Terraform wraps diagnostic text, so compare with whitespace collapsed.
    assert "subject_claims must be a non-empty list of claim suffixes" in " ".join(
        plan.stderr.split()
    )
