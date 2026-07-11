"""TextProvider real: Claude (Anthropic Messages API)."""
from __future__ import annotations

import httpx

from app.ai_clients.base import ProviderError, TextResult
from app.config import settings

_API_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"
_MODEL = "claude-opus-4-8"

_SYSTEM = (
    "Você é um autor brasileiro de livros infantis. Escreva SEMPRE em português "
    "do Brasil impecável: ortografia, gramática, pontuação e ACENTUAÇÃO corretas "
    "(nunca omita acentos: coração, você, céu, mãozinha). Escreva uma história "
    "calorosa, coerente e adequada à faixa etária, dividida em páginas curtas. "
    "Mantenha o personagem principal consistente do início ao fim. Responda "
    "APENAS com o texto da história — sem sugestões de imagem, notas, títulos de "
    "seção ou comentários entre parênteses/asteriscos."
)


class AnthropicTextProvider:
    name = "claude"

    def __init__(self, api_key: str | None = None, timeout: float = 60.0):
        self._api_key = api_key or settings.anthropic_api_key
        self._timeout = timeout

    async def generate_story(self, *, brief: str, style: str, pages: int) -> TextResult:
        if not self._api_key:
            raise ProviderError("ANTHROPIC_API_KEY ausente", transient=False)

        user = (
            f"Estilo visual: {style}. Número de páginas: {pages}.\n"
            f"Brief do personagem/tema: {brief}\n\n"
            f"Devolva exatamente {pages} páginas, cada uma iniciada por 'Página N:'. "
            f"Texto em português do Brasil com acentuação correta, sem sugestões de imagem."
        )
        payload = {
            "model": _MODEL,
            "max_tokens": 4000,
            "system": _SYSTEM,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _VERSION,
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(_API_URL, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ProviderError(f"Falha de rede: {exc}", transient=True) from exc

        if resp.status_code in (429, 500, 502, 503, 504):
            raise ProviderError(
                f"Anthropic {resp.status_code}", transient=True, status_code=resp.status_code
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"Anthropic {resp.status_code}: {resp.text[:300]}",
                transient=False,
                status_code=resp.status_code,
            )

        data = resp.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        return TextResult(text=text, meta={"usage": usage, "model": _MODEL})

    async def summarize_pages(self, *, pages: list[str], style: str = "") -> list[str]:
        """Resume cada trecho da historia numa legenda curta (1 frase) por pagina.

        Retorna uma lista do mesmo tamanho de `pages`. O texto integral continua
        sendo usado para ILUSTRAR (contexto completo); a legenda e o que aparece
        impresso na pagina do e-book.
        """
        if not self._api_key:
            raise ProviderError("ANTHROPIC_API_KEY ausente", transient=False)
        if not pages:
            return []

        numbered = "\n\n".join(f"[{i + 1}] {p}" for i, p in enumerate(pages))
        system = (
            "Voce escreve legendas curtas para um livro infantil ilustrado, em "
            "PORTUGUES DO BRASIL correto. Para cada trecho recebido, escreva UMA frase "
            "curta, calorosa e adequada a criancas, que sera o texto impresso naquela "
            "pagina. REVISE e CORRIJA ortografia, gramatica, pontuacao e acentuacao — a "
            "legenda final deve estar perfeita em portugues, mesmo que o trecho original "
            "tenha erros. Responda APENAS com as legendas, uma por linha, na mesma ordem, "
            "sem numeracao e sem aspas."
        )
        user = f"Gere uma legenda por trecho, na ordem ({len(pages)} trechos):\n\n{numbered}"
        payload = {
            "model": _MODEL,
            "max_tokens": 1500,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _VERSION,
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(_API_URL, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ProviderError(f"Falha de rede: {exc}", transient=True) from exc
        if resp.status_code in (429, 500, 502, 503, 504):
            raise ProviderError(f"Anthropic {resp.status_code}", transient=True)
        if resp.status_code >= 400:
            raise ProviderError(f"Anthropic {resp.status_code}: {resp.text[:200]}", transient=False)

        data = resp.json()
        text = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )
        lines = [ln.strip(" -•\t").strip() for ln in text.splitlines() if ln.strip()]
        return lines
