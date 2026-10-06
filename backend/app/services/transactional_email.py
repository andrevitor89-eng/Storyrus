"""E-mails transacionais via Resend.

Sem RESEND_API_KEY o envio é no-op e o link fica nos logs (dev devolve o token).
Em prod, falta de chave gera warning no boot e em cada skip.
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
_DEFAULT_FROM = "Story R Us <noreply@storyrus.ai>"


def email_configured() -> bool:
    """True quando há chave Resend para envio real."""
    return bool((settings.resend_api_key or "").strip())


def resolved_from_email() -> str:
    """From efetivo — env vazio no Render não pode zerar o remetente."""
    raw = (settings.transactional_from_email or "").strip()
    return raw or _DEFAULT_FROM


def warn_if_email_unconfigured() -> None:
    """Chamar no boot da API: em prod, e-mail sem chave = esqueci-senha/verify mudos."""
    if email_configured():
        logger.info(
            "transactional_email_ready from=%s",
            resolved_from_email(),
        )
        return
    if settings.app_env == "prod":
        logger.warning(
            "RESEND_API_KEY ausente: confirmação de cadastro e esqueci-senha "
            "não enviam e-mail (só logs). Defina no Render + domínio verificado no Resend."
        )
    else:
        logger.info("RESEND_API_KEY ausente: envio transacional desligado (dev ok)")


def build_verify_email_url(token: str, email: str | None = None) -> str:
    origin = (settings.public_web_origin or "https://storyrus.ai").rstrip("/")
    query: dict[str, str] = {"token": token}
    if email:
        query["email"] = email.strip()
    return f"{origin}/verificar-email?{urlencode(query)}"


def build_password_reset_url(token: str, email: str | None = None) -> str:
    origin = (settings.public_web_origin or "https://storyrus.ai").rstrip("/")
    query: dict[str, str] = {"token": token}
    if email:
        query["email"] = email.strip()
    return f"{origin}/redefinir-senha?{urlencode(query)}"


def send_email(*, to_email: str, subject: str, text: str, html: str) -> bool:
    api_key = (settings.resend_api_key or "").strip()
    if not api_key:
        level = logging.WARNING if settings.app_env == "prod" else logging.INFO
        logger.log(
            level,
            "transactional_email_skipped to=%s subject=%s reason=no_resend_api_key",
            to_email,
            subject,
        )
        return False
    from_email = resolved_from_email()
    try:
        resp = httpx.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "text": text,
                "html": html,
            },
            timeout=15.0,
        )
        if resp.status_code >= 300:
            logger.warning(
                "transactional_email_failed to=%s status=%s body=%s from=%s",
                to_email,
                resp.status_code,
                resp.text[:300],
                from_email,
            )
            return False
        logger.info(
            "transactional_email_sent to=%s subject=%s from=%s",
            to_email,
            subject,
            from_email,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("transactional_email_error to=%s err=%s", to_email, exc)
        return False


def send_verify_email(*, to_email: str, token: str) -> bool:
    url = build_verify_email_url(token, email=to_email)
    if not email_configured():
        logger.info("verify_email_link to=%s url=%s", to_email, url)
    subject = "Confirme seu e-mail — Story R Us"
    text = (
        "Bem-vindo ao Story R Us!\n\n"
        "Confirme seu e-mail para ativar a conta e criar livros:\n"
        f"{url}\n\n"
        f"O link vale por {settings.email_verify_ttl_min} minutos."
    )
    html = (
        "<p>Bem-vindo ao <strong>Story R Us</strong>!</p>"
        f'<p><a href="{url}">Clique aqui para confirmar seu e-mail</a> '
        f"e ativar a conta (válido por {settings.email_verify_ttl_min} minutos).</p>"
    )
    return send_email(to_email=to_email, subject=subject, text=text, html=html)


def send_password_reset_email(*, to_email: str, token: str) -> bool:
    url = build_password_reset_url(token, email=to_email)
    if not email_configured():
        logger.info("password_reset_link to=%s url=%s", to_email, url)
    subject = "Redefinir senha — Story R Us"
    text = (
        "Recebemos um pedido para redefinir a senha da sua conta Story R Us.\n\n"
        "Abra o link abaixo para escolher uma nova senha:\n"
        f"{url}\n\n"
        f"O link vale por {settings.password_reset_ttl_min} minutos. "
        "Se você não pediu isso, ignore este e-mail."
    )
    html = (
        "<p>Recebemos um pedido para redefinir a senha da sua conta "
        "<strong>Story R Us</strong>.</p>"
        f'<p><a href="{url}">Clique aqui para escolher uma nova senha</a> '
        f"(válido por {settings.password_reset_ttl_min} minutos).</p>"
        "<p>Se você não pediu isso, ignore este e-mail.</p>"
    )
    return send_email(to_email=to_email, subject=subject, text=text, html=html)
