"""Tabela de preço e conversão usage -> USD.

Valores default vêm de Settings (env). Sem rede: só aritmética local.
"""
from __future__ import annotations

from typing import Any

from app.config import settings


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def image_cost(usage: dict | None = None) -> float:
    """Custo de uma geração Gemini (Nano Banana).

    Se a API devolver usageMetadata com tokens, usa as taxas por milhão.
    Senão, cobra o preço fixo por imagem.
    """
    usage = usage or {}
    prompt = _f(
        usage.get("promptTokenCount", usage.get("prompt_token_count"))
    )
    candidates = _f(
        usage.get("candidatesTokenCount", usage.get("candidates_token_count"))
    )
    if prompt or candidates:
        inp = prompt / 1_000_000 * settings.price_gemini_input_per_mtok
        out = candidates / 1_000_000 * settings.price_gemini_output_per_mtok
        return round(inp + out, 6)
    return round(settings.price_gemini_image_usd, 6)


def text_cost(usage: dict | None = None) -> float:
    """Custo Claude a partir do bloco `usage` da Messages API."""
    usage = usage or {}
    inp = _f(usage.get("input_tokens", usage.get("inputTokens")))
    out = _f(usage.get("output_tokens", usage.get("outputTokens")))
    if not inp and not out:
        return 0.0
    total = (
        inp / 1_000_000 * settings.price_claude_input_per_mtok
        + out / 1_000_000 * settings.price_claude_output_per_mtok
    )
    return round(total, 6)


def video_cost(duration_s: float | None) -> float:
    """Custo Kling: segundos faturáveis × preço por segundo."""
    seconds = max(_f(duration_s), 0.0)
    return round(seconds * settings.price_kling_per_second_usd, 6)


def add_usd(*values: float | None) -> float:
    """Soma custos parciais (None = 0)."""
    return round(sum(_f(v) for v in values), 6)
