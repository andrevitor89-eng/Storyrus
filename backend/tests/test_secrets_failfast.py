"""STO-8: secrets fail-fast quando APP_ENV != dev."""
import pytest
from pydantic import ValidationError

from app.config import Settings


def test_dev_allows_default_secrets():
    s = Settings(
        app_env="dev",
        jwt_secret="change-me-in-prod",
        webhook_signing_secret="change-me-webhook",
    )
    assert s.app_env == "dev"


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_non_dev_rejects_default_jwt(env):
    with pytest.raises(ValidationError) as exc:
        Settings(
            app_env=env,
            jwt_secret="change-me-in-prod",
            webhook_signing_secret="a-strong-webhook-secret-value",
        )
    assert "JWT_SECRET" in str(exc.value)


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_non_dev_rejects_default_webhook(env):
    with pytest.raises(ValidationError) as exc:
        Settings(
            app_env=env,
            jwt_secret="a-strong-jwt-secret-value",
            webhook_signing_secret="change-me-webhook",
        )
    assert "WEBHOOK_SIGNING_SECRET" in str(exc.value)


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_non_dev_rejects_unsafe_storage_keys(env):
    with pytest.raises(ValidationError) as exc:
        Settings(
            app_env=env,
            jwt_secret="a-strong-jwt-secret-value",
            webhook_signing_secret="a-strong-webhook-secret-value",
            storage_access_key="change-me",
            storage_secret_key="ok-secret",
        )
    assert "STORAGE_ACCESS_KEY" in str(exc.value)


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_non_dev_accepts_strong_secrets(env):
    s = Settings(
        app_env=env,
        jwt_secret="a-strong-jwt-secret-value",
        webhook_signing_secret="a-strong-webhook-secret-value",
        storage_access_key=None,
        storage_secret_key=None,
    )
    assert s.app_env == env
