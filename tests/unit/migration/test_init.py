from entitysdk import migration as test_module


def test_public_api():
    expected = {
        "ApplySettings",
        "CommonSettings",
        "EntityKey",
        "ExecutionManifest",
        "ExecutionSummary",
        "OperationType",
        "RevertSettings",
        "SnapshotLabel",
        "init_client",
        "load_manifest",
        "run",
        "script_dir",
    }
    assert set(test_module.__all__) == expected
