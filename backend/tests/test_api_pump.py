"""A API em prod consome a fila quando o worker free está dormindo."""

from app.config import Settings


def test_job_pump_ligado_em_prod_e_desligado_em_dev():
    dev = Settings(app_env="dev")
    prod = Settings(
        app_env="prod",
        jwt_secret="a-real-prod-secret-value",
        webhook_signing_secret="another-real-prod-secret",
        openai_api_key="sk-test",
    )
    assert dev.job_pump_enabled() is False
    assert prod.job_pump_enabled() is True


def test_job_pump_respeita_override():
    forced_off = Settings(
        app_env="prod",
        api_job_pump=False,
        jwt_secret="a-real-prod-secret-value",
        webhook_signing_secret="another-real-prod-secret",
        openai_api_key="sk-test",
    )
    forced_on = Settings(app_env="dev", api_job_pump=True)
    assert forced_off.job_pump_enabled() is False
    assert forced_on.job_pump_enabled() is True
