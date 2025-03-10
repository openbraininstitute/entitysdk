import pytest

from entitysdk import result as test_module
from entitysdk.exception import IteratorResultError


def test_iterator_result():
    data = []
    assert [v for v in test_module.IteratorResult(data)] == []
    assert list(test_module.IteratorResult(data)) == []
    assert list(iter(test_module.IteratorResult(data))) == []
    assert test_module.IteratorResult(data).first() is None

    with pytest.raises(IteratorResultError, match="Iterable is empty."):
        assert test_module.IteratorResult(data).one() == 1

    assert test_module.IteratorResult(data).one_or_none() is None
    assert test_module.IteratorResult(data).all() == []

    data = (1,)
    assert next(test_module.IteratorResult(data)) == 1
    assert [v for v in test_module.IteratorResult(data)] == [1]
    assert list(test_module.IteratorResult(data)) == [1]
    assert test_module.IteratorResult(data).first() == 1
    assert test_module.IteratorResult(data).one() == 1
    assert test_module.IteratorResult(data).one_or_none() == 1
    assert test_module.IteratorResult(data).all() == [1]

    data = (1, 2)

    assert [v for v in test_module.IteratorResult(data)] == [1, 2]
    assert list(test_module.IteratorResult(data)) == [1, 2]
    assert test_module.IteratorResult(data).first() == 1

    with pytest.raises(IteratorResultError, match="There are more than one items."):
        test_module.IteratorResult(data).one()
    with pytest.raises(IteratorResultError, match="There are more than one items."):
        test_module.IteratorResult(data).one_or_none()

    assert test_module.IteratorResult(data).all() == [1, 2]
