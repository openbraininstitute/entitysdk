from unittest.mock import Mock, patch

import pytest

from entitysdk.utils import execution as test_module


def test_execute_success_first_try():
    fn = Mock(return_value="ok")

    result = test_module.execute_with_retry(fn)

    assert result == "ok"
    fn.assert_called_once()


def test_execute_retries_then_succeeds():
    fn = Mock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])

    with patch("entitysdk.utils.execution.time.sleep") as sleep_mock:
        result = test_module.execute_with_retry(fn, max_retries=3, backoff_base=1)

    assert result == "success"
    assert fn.call_count == 3

    # Exponential backoff: 1 * 2^0, 1 * 2^1
    sleep_mock.assert_any_call(1)
    sleep_mock.assert_any_call(2)
    assert sleep_mock.call_count == 2


def test_execute_all_retries_fail():
    fn = Mock(side_effect=RuntimeError("boom"))

    with patch("entitysdk.utils.execution.time.sleep") as sleep_mock:
        with pytest.raises(RuntimeError, match="boom"):
            test_module.execute_with_retry(fn, max_retries=3, backoff_base=0.1)

    assert fn.call_count == 3
    assert sleep_mock.call_count == 3  # sleeps even on last failure


def test_invalid_max_retries():
    fn = Mock()

    with pytest.raises(ValueError, match="max_retries must be >= 0"):
        test_module.execute_with_retry(fn, max_retries=-1)


def test_backoff_values_exact():
    fn = Mock(side_effect=[Exception("x"), Exception("y"), "done"])

    with patch("entitysdk.utils.execution.time.sleep") as sleep_mock:
        test_module.execute_with_retry(fn, max_retries=3, backoff_base=0.5)

    expected_calls = [(0.5,), (1.0,)]
    actual_calls = sleep_mock.call_args_list[:2]

    assert [call.args for call in actual_calls] == expected_calls
