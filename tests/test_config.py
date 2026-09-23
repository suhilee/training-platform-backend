from app.core.config import Settings


def test_environment_variable_overrides_default(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "test")

    settings = Settings()

    assert settings.app_environment == "test"
