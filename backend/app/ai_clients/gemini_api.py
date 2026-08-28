"""Detalhes compartilhados de HTTP da Gemini API (URL base, TLS, MIME, inline).

Existe para que provider de imagem e deteccao de rosto nao dupliquem a regra de
TLS: duas copias divergiriam e a maquina com antivirus reassinando o trafego
voltaria a falhar em uma delas.
"""
from __future__ import annotations

import base64
import ssl

from app.config import settings

BASE = "https://generativelanguage.googleapis.com/v1beta"
TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})


def ssl_verify() -> bool | ssl.SSLContext:
    """Traduz `GEMINI_SSL_VERIFY` no parametro `verify` do httpx.

    `system` usa a loja de certificados do SO em vez do bundle do certifi que o
    httpx fixa. E o que faz o TLS validar atras de antivirus/proxy que reassinam
    o trafego (ex.: AVG Web/Mail Shield), sem desligar a verificacao.

    Vem de `settings` (nao de `os.getenv`) para que valha tanto no `.env` — que o
    pydantic-settings le mas nao exporta para o ambiente — quanto na variavel de
    ambiente que os scripts definem antes de importar a config.
    """
    raw = (settings.gemini_ssl_verify or "true").strip().lower()
    if raw in ("0", "false", "no"):
        return False
    if raw == "system":
        return ssl.create_default_context()
    return True


def detect_mime(image: bytes) -> str:
    """Detecta MIME real pelos magic bytes (evita rotular PNG como JPEG)."""
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(image) >= 3 and image[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(image) >= 12 and image[:4] == b"RIFF" and image[8:12] == b"WEBP":
        return "image/webp"
    if image.startswith(b"GIF87a") or image.startswith(b"GIF89a"):
        return "image/gif"
    return "image/jpeg"


def inline_part(image: bytes, mime: str | None = None) -> dict:
    return {
        "inline_data": {
            "mime_type": mime or detect_mime(image),
            "data": base64.b64encode(image).decode(),
        }
    }


def api_message(resp) -> str:
    """`error.message` do Gemini, quando vier; senao um trecho do corpo cru."""
    try:
        message = (resp.json().get("error") or {}).get("message")
    except Exception:  # noqa: BLE001 - corpo pode nao ser JSON
        message = None
    if message:
        return str(message)[:200]
    return (getattr(resp, "text", "") or "").strip().replace("\n", " ")[:200]
