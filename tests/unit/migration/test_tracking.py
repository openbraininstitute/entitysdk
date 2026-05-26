import uuid

import pytest

from entitysdk import models
from entitysdk.migration import tracking as test_module


def test_identifiable_key_str():
    key = test_module.IdentifiableKey(type=models.CellMorphology, id=uuid.UUID(int=1))
    assert str(key) == f"CellMorphology::{uuid.UUID(int=1)}"


def test_identifiable_key_from_string():
    uid = uuid.uuid4()
    key = test_module.IdentifiableKey.from_string(f"CellMorphology::{uid}")
    assert key.type == models.CellMorphology
    assert key.id == uid


def test_identifiable_key_from_string_raises_when_unknown():
    uid = uuid.uuid4()
    with pytest.raises(ValueError, match="Unknown entity type"):
        test_module.IdentifiableKey.from_string(f"Unknown::{uid}")


def test_identifiable_key_from_string_raises_when_not_identifiable(monkeypatch):
    uid = uuid.uuid4()
    monkeypatch.setattr(models, "NotIdentifiable", object, raising=False)
    with pytest.raises(ValueError, match="Invalid entity type"):
        test_module.IdentifiableKey.from_string(f"NotIdentifiable::{uid}")


def test_identifiable_key_roundtrip():
    key = test_module.IdentifiableKey(type=models.Circuit, id=uuid.uuid4())
    assert test_module.IdentifiableKey.from_string(str(key)) == key


def test_identifiable_key_named_tuple_fields():
    uid = uuid.uuid4()
    key = test_module.IdentifiableKey(type=models.CellMorphology, id=uid)
    assert key.type == models.CellMorphology
    assert key.id == uid


def test_operation_type_values():
    assert set(test_module.OperationType) == {"created", "updated", "deleted", "skipped", "failed"}


def test_snapshot_label_values():
    assert set(test_module.SnapshotLabel) == {"before", "after"}


def test_execution_summary_default_operations():
    summary = test_module.ExecutionSummary()
    for op in test_module.OperationType:
        assert op in summary.operations
        assert summary.operations[op] == []


def test_execution_summary_record_operation():
    summary = test_module.ExecutionSummary()
    key = test_module.IdentifiableKey(type=models.CellMorphology, id=uuid.uuid4())
    summary.record_operation(key, test_module.OperationType.created)
    assert str(key) in summary.operations[test_module.OperationType.created]


def test_execution_summary_record_operation_new_type():
    summary = test_module.ExecutionSummary()
    summary.operations.clear()
    key = test_module.IdentifiableKey(type=models.CellMorphology, id=uuid.uuid4())
    summary.record_operation(key, test_module.OperationType.updated)
    assert str(key) in summary.operations[test_module.OperationType.updated]


def test_execution_summary_record_snapshot():
    summary = test_module.ExecutionSummary()
    key = test_module.IdentifiableKey(type=models.CellMorphology, id=uuid.uuid4())
    summary.record_snapshot(key, test_module.SnapshotLabel.before, {"name": "old"})
    summary.record_snapshot(key, test_module.SnapshotLabel.after, {"name": "new"})
    entry = summary.snapshots[str(key)]
    assert entry[test_module.SnapshotLabel.before] == {"name": "old"}
    assert entry[test_module.SnapshotLabel.after] == {"name": "new"}


def test_execution_summary_log_summary(caplog):
    summary = test_module.ExecutionSummary()
    key = test_module.IdentifiableKey(type=models.CellMorphology, id=uuid.uuid4())
    summary.record_operation(key, test_module.OperationType.created)
    summary.record_operation(key, test_module.OperationType.skipped)
    with caplog.at_level("INFO"):
        summary.log_summary()
    assert "1 created" in caplog.text
    assert "1 skipped" in caplog.text
