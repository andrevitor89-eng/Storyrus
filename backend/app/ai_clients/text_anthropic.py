"""TextProvider real: Claude (Anthropic Messages API). Versos rimados por pagina."""
from __future__ import annotations

import httpx

from app.ai_clients.base import ProviderError, TextResult
from app.config import settings

_API_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"
_MODEL = "claude-opus-4-8"

_SYSTEM_PT = (
    "Você é um autor de livros infantis personalizados premium (no estilo de "
    "WonderWraps/TellMyTale). Escreva SEMPRE em português do Brasil impecável: "
    "ortografia, gramática, pontuação e ACENTUAÇÃO corretas (nunca omita acentos: "
    "coração, você, céu, mãozinha). Cada página é uma ESTROFE CURTA de 2 a 4 "
    "versos RIMADOS (rima AABB ou ABCB), calorosa, musical e adequada a crianças "
    "pequenas — no máximo ~40 palavras por página. Cada página descreve UMA cena "
    "visual clara (lugar + ação do protagonista). Mantenha o personagem principal "
    "consistente do início ao fim e a história com começo, meio e fim. Responda "
    "APENAS com o texto pedido — sem sugestões de imagem, notas ou comentários."
)
_SYSTEM_EN = (
    "You are an author of premium personalized children's books (in the style of "
    "WonderWraps/TellMyTale). Write ALWAYS in flawless English. Each page is a "
    "SHORT STANZA of 2 to 4 RHYMING lines (AABB or ABCB), warm, musical and "
    "suitable for young children — at most ~40 words per page. Each page depicts "
    "ONE clear visual scene (place + the hero's action). Keep the main character "
    "consistent throughout, with a clear beginning, middle and end. Reply ONLY "
    "with the requested text — no image suggestions, notes or comments."
)


def _lang(language: str | None) -> str:
    return "en" if (language or "").lower().startswith("en") else "pt-BR"


class AnthropicTextProvider:
    name = "claude"

    def __init__(self, api_key: str | None = None, timeout: float = 60.0):
        self._api_key = api_key or settings.anthropic_api_key
        self._timeout = timeout

    async def generate_story(
        self, *, brief: str, style: str, pages: int, language: str = "pt-BR"
    ) -> TextResult:
        if not self._api_key:
            raise ProviderError("ANTHROPIC_API_KEY ausente", transient=False)

        lang = _lang(language)
        if lang == "en":
            system = _SYSTEM_EN
            user = (
                f"Visual style: {style}. Number of pages: {pages}.\n"
                f"Character/theme brief: {brief}\n\n"
                "Return EXACTLY in this format:\n"
                f"Line 1 => 'Título: <book title featuring the hero's name, e.g. "
                f"\"NAME and the Great Adventure\">'.\n"
                f"Then exactly {pages} pages, each starting with 'Página N:' followed by "
                "the stanza (2-4 short rhyming lines). No image suggestions."
            )
        else:
            system = _SYSTEM_PT
            user = (
                f"Estilo visual: {style}. Número de páginas: {pages}.\n"
                f"Brief do personagem/tema: {brief}\n\n"
                "Devolva EXATAMENTE neste formato:\n"
                "Linha 1 => 'Título: <título do livro com o nome do protagonista, ex.: "
                "\"NOME e a Grande Aventura\">'.\n"
                f"Depois exatamente {pages} páginas, cada uma iniciada por 'Página N:' "
                "seguida da estrofe (2 a 4 versos curtos rimados). Português do Brasil "
                "com acentuação correta, sem sugestões de imagem."
            )
        payload = {
            "model": _MODEL,
            "max_tokens": 4000,
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

    async def summarize_pages(
        self, *, pages: list[str], style: str = "", language: str = "pt-BR"
    ) -> list[str]:
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
        if _lang(language) == "en":
            system = (
                "You write short captions for an illustrated children's book, in correct "
                "ENGLISH. For each excerpt, write ONE short, warm, child-friendly sentence "
                "that will be printed on that page. PROOFREAD spelling, grammar and "
                "punctuation. Reply ONLY with the captions, one per line, in the same "
                "order, without numbering or quotes."
            )
            user = f"One caption per excerpt, in order ({len(pages)} excerpts):\n\n{numbered}"
        else:
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
