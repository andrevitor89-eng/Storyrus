"""TextProvider real: Claude (Anthropic Messages API). Versos rimados por pagina."""
from __future__ import annotations

import httpx

from app.ai_clients.base import ProviderError, TextResult
from app.config import settings

_API_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"
_MODEL = "claude-opus-4-8"

_SYSTEM_PT = (
    "Você é um autor premiado de livros infantis personalizados (nível "
    "WonderWraps/TellMyTale). Escreva SEMPRE em português do Brasil impecável, com "
    "ortografia, gramática, pontuação e ACENTUAÇÃO corretas (nunca omita acentos: "
    "coração, você, céu, mãozinha).\n\n"
    "HISTÓRIA (o mais importante): antes de escrever, planeje mentalmente um ENREDO "
    "COERENTE com começo, meio e fim — um cenário claro, um pequeno OBJETIVO ou "
    "problema do protagonista, uma jornada com 1 ou 2 obstáculos e amiguinhos que "
    "ajudam, um clímax gentil e um final acolhedor com uma lição sutil (coragem, "
    "amizade, gentileza). Cada página AVANÇA a história de forma lógica e se conecta "
    "à anterior — nunca cenas soltas, aleatórias ou sem nexo. O protagonista é o "
    "mesmo do início ao fim, com o mesmo nome. Seja concreto e sensorial (lugares, "
    "cores, sons), adequado a crianças de 3 a 7 anos, com ternura e sem medo.\n\n"
    "CRIATIVIDADE E ENCANTAMENTO: abra a página 1 com um GANCHO irresistível que dê "
    "vontade de virar a página. Crie um momento de DESCOBERTA ou uma pequena SURPRESA "
    "no meio, aumente a emoção e a tensão gentil até um CLÍMAX triunfante, e termine "
    "com um final memorável e afetuoso que dê um friozinho gostoso na barriga. Use "
    "imagens vívidas e inesperadas, palavras sonoras (plim!, zup!, splash!), um toque "
    "de humor ou magia, vocabulário rico e ideias ORIGINAIS — nada de clichês nem "
    "histórias repetidas. Cada livro deve ser único, emocionante e inesquecível.\n\n"
    "FORMA: cada página é uma ESTROFE CURTA de 2 a 4 versos RIMADOS (AABB ou ABCB), "
    "musical, no máximo ~40 palavras, descrevendo UMA cena visual clara (lugar + "
    "ação do protagonista). O SENTIDO vem SEMPRE primeiro: a rima nunca pode tornar "
    "a frase confusa ou sem sentido; se precisar escolher, prefira clareza e beleza "
    "à rima forçada.\n\n"
    "Responda APENAS com o texto pedido — sem notas, comentários ou sugestões de imagem."
)
_SYSTEM_EN = (
    "You are an award-winning author of premium personalized children's books "
    "(WonderWraps/TellMyTale level). Write ALWAYS in flawless English.\n\n"
    "STORY (most important): before writing, mentally plan a COHERENT plot with a "
    "beginning, middle and end — a clear setting, a small GOAL or problem for the "
    "hero, a journey with 1 or 2 obstacles and friends who help, a gentle climax and "
    "a warm ending with a subtle lesson (courage, friendship, kindness). Each page "
    "ADVANCES the story logically and connects to the previous one — never random, "
    "disconnected or nonsensical scenes. The hero stays the same throughout, with the "
    "same name. Be concrete and sensory (places, colors, sounds), suitable for ages "
    "3-7, warm and never scary.\n\n"
    "CREATIVITY AND WONDER: open page 1 with an irresistible HOOK that makes the "
    "reader want to turn the page. Add a moment of DISCOVERY or a small SURPRISE in "
    "the middle, build emotion and gentle tension to a triumphant CLIMAX, and end "
    "with a memorable, heart-warming finish that gives a delightful tingle. Use vivid, "
    "unexpected imagery, playful sound words (plink!, whoosh!, splash!), a touch of "
    "humor or magic, rich vocabulary and ORIGINAL ideas — no clichés or repeated "
    "plots. Every book must be unique, exciting and unforgettable.\n\n"
    "FORM: each page is a SHORT STANZA of 2 to 4 RHYMING lines (AABB or ABCB), "
    "musical, at most ~40 words, depicting ONE clear visual scene (place + the hero's "
    "action). MEANING always comes first: rhyme must never make a line confusing or "
    "nonsensical; if you must choose, prefer clarity and beauty over forced rhyme.\n\n"
    "Reply ONLY with the requested text — no notes, comments or image suggestions."
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
                "First, silently plan an original, coherent plot within the theme: a goal "
                "or small problem, a journey with an obstacle and friends who help, a gentle "
                "climax and a warm resolution with a subtle lesson. Then structure it across "
                f"the {pages} pages: page 1 introduces the hero and the world; the middle "
                "pages develop the adventure and the challenge; the last page gives a warm, "
                "satisfying ending. Every page must follow logically from the previous one.\n\n"
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
                "Primeiro, planeje em silêncio um enredo ORIGINAL e coerente dentro do "
                "tema: um objetivo ou pequeno problema, uma jornada com um obstáculo e "
                "amiguinhos que ajudam, um clímax gentil e um desfecho caloroso com uma "
                "lição sutil. Depois estruture nas "
                f"{pages} páginas: a página 1 apresenta o protagonista e o mundo; as "
                "páginas do meio desenvolvem a aventura e o desafio; a última traz um "
                "final acolhedor e satisfatório. Cada página deve seguir logicamente da "
                "anterior, sem cenas soltas.\n\n"
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
