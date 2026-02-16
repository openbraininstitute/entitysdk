from unittest.mock import Mock, patch

import pytest

from entitysdk import multipart_upload as test_module


def test_execute_with_retry_retries_on_exception():
    # Mock function that fails first two times, then succeeds
    mock_fn = Mock(
        side_effect=[
            test_module.RETRIABLE_EXCEPTIONS[0]("fail 1"),
            test_module.RETRIABLE_EXCEPTIONS[0]("fail 2"),
            "success",
        ]
    )

    # Patch time.sleep to avoid slowing down the test
    with patch("entitysdk.utils.execution.time.sleep", return_value=None) as mock_sleep:
        result = test_module.execute_with_retry(
            mock_fn, max_retries=3, backoff_base=0.1, retry_on=test_module.RETRIABLE_EXCEPTIONS
        )

    # The function should eventually return "success"
    assert result == "success"

    # The mock function should have been called 3 times
    assert mock_fn.call_count == 3

    # time.sleep should have been called twice (between retries)
    assert mock_sleep.call_count == 2


def test_execute_with_retry_raises_after_max_retries():
    # Function that always fails
    mock_fn = Mock(side_effect=test_module.RETRIABLE_EXCEPTIONS[0]("always fail"))

    with patch("entitysdk.utils.execution.time.sleep", return_value=None):
        with pytest.raises(test_module.RETRIABLE_EXCEPTIONS[0], match="always fail"):
            test_module.execute_with_retry(
                mock_fn, max_retries=3, backoff_base=0.1, retry_on=test_module.RETRIABLE_EXCEPTIONS
            )

    # It should try 3 times
    assert mock_fn.call_count == 3
