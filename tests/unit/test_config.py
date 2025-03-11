from entitysdk import config as test_module


def test_settings_without_env(monkeypatch):
    monkeypatch.delenv("ENTITYSDK_PAGE_SIZE", raising=False)
    settings = test_module.Settings()
    assert settings.page_size is None


def test_settings_with_env(monkeypatch):
    monkeypatch.setenv("ENTITYSDK_PAGE_SIZE", "123")
    settings = test_module.Settings()
    assert settings.page_size == 123
