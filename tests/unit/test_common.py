import pytest

from entitysdk import common as test_module
from entitysdk.exception import EntitySDKError
from entitysdk.types import DeploymentEnvironment

VLAB_ID = "ff888f05-f314-4702-8a92-b86f754270bb"
PROJ_ID = "f373e771-3a2f-4f45-ab59-0955efd7b1f4"


@pytest.mark.parametrize(
    ("url", "expected_context", "expected_env"),
    [
        (
            f"https://staging.openbraininstitute.org/app/virtual-lab/{VLAB_ID}/{PROJ_ID}",
            test_module.ProjectContext(
                virtual_lab_id=VLAB_ID,
                project_id=PROJ_ID,
            ),
            DeploymentEnvironment.staging,
        ),
        (
            f"https://www.openbraininstitute.org/app/virtual-lab/{VLAB_ID}/{PROJ_ID}",
            test_module.ProjectContext(
                virtual_lab_id=VLAB_ID,
                project_id=PROJ_ID,
            ),
            DeploymentEnvironment.production,
        ),
    ],
)
def test_project_context_env_from_vlab_url(url, expected_context, expected_env):
    context, env = test_module.project_context_env_from_vlab_url(url)
    assert context == expected_context
    assert env == expected_env


@pytest.mark.parametrize(
    ("url", "expected_error", "expected_msg"),
    [
        ("asdf", EntitySDKError, "Badly formed vlab url"),
        ("https://", EntitySDKError, "Badly formed vlab url"),
        ("https://openbraininstitute.org", EntitySDKError, "Badly formed vlab url"),
        ("https://staging.openbraininstitute.org", EntitySDKError, "Badly formed vlab url"),
        (
            "https://staging.openbraininstitute.org/app/virtual-lab/foo",
            EntitySDKError,
            "Badly formed vlab url",
        ),
        (
            "https://staging.openbraininstitute.org/app/virtual-lab/foo/bar",
            EntitySDKError,
            "Badly formed vlab url",
        ),
        (
            f"https://dev.openbraininstitute.org/app/virtual-lab/{VLAB_ID}/{PROJ_ID}",
            EntitySDKError,
            "Badly formed vlab url",
        ),
        (
            f"https://dev.openbraininstitute.org/app/virtual-lab/foo/{PROJ_ID}",
            EntitySDKError,
            "Badly formed vlab url",
        ),
        (
            f"https://dev.openbraininstitute.org/app/virtual-lab/{VLAB_ID}/bar",
            EntitySDKError,
            "Badly formed vlab url",
        ),
    ],
)
def test_project_context_env_from_vlab_url__raises(url, expected_error, expected_msg):
    with pytest.raises(expected_error, match=expected_msg):
        test_module.project_context_env_from_vlab_url(url)
