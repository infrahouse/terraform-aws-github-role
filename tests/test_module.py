from base64 import b64decode

import pytest
from infrahouse_toolkit.terraform import terraform_apply

from tests.conftest import (
    LOG,
    TRACE_TERRAFORM,
    DESTROY_AFTER,
)


@pytest.mark.flaky(reruns=0, reruns_delay=30)
@pytest.mark.timeout(1800)
def test_module():
    terraform_dir = "test_data/test_module"

    with terraform_apply(
        terraform_dir,
        destroy_after=DESTROY_AFTER,
        json_output=True,
        enable_trace=TRACE_TERRAFORM,
    ) as tf_output:
        assert tf_output["role_arn"]["value"]
