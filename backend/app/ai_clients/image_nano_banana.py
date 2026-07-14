"""ImageProvider real: Nano Banana (Gemini 2.5 Flash Image).

Modelo: gemini-2.5-flash-image via Gemini API (generativelanguage).
A consistencia de personagem vem de reutilizar a referencia (character_ref)
como imagem de entrada em todas as cenas.
"""
from __future__ import annotations

import base64

import httpx

from app.ai_clients.base import ImageResult, ProviderError
from app.config import settings

_MODEL = "gemini-2.5-flash-image"
_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _inline(image: bytes, mime: str = "image/png") -> dict:
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode()}}


class NanoBananaImageProvider:
    name = "nano-banana"

    def __init__(self, api_key: str | None = None, timeout: float = 120.0):
        self._api_key = api_key or settings.gemini_api_key
        self._timeout = timeout

    async def _generate(self, parts: list[dict]) -> ImageResult:
        if not self._api_key:
            raise ProviderError("GEMINI_API_KEY ausente", transient=False)

        url = f"{_BASE}/models/{_MODEL}:generateContent"
        headers = {"x-goog-api-key": self._api_key, "content-type": "application/json"}
        payload = {"contents": [{"role": "user", "parts": parts}]}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise ProviderError(f"Falha de rede: {exc}", transient=True) from exc

        if resp.status_code in (429, 500, 502, 503, 504):
            raise ProviderError(
                f"Gemini {resp.status_code}", transient=True, status_code=resp.status_code
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"Gemini {resp.status_code}: {resp.text[:300]}",
                transient=False,
                status_code=resp.status_code,
            )

        data = resp.json()
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                inline = part.get("inline_data") or part.get("inlineData")
                if inline and inline.get("data"):
                    mime = inline.get("mime_type") or inline.get("mimeType", "image/png")
                    return ImageResult(
                        image_bytes=base64.b64decode(inline["data"]),
                        mime_type=mime,
                        meta={"model": _MODEL},
                    )
        raise ProviderError("Resposta sem imagem", transient=False)

    async def generate_character(
        self, *, prompt: str, reference_images: list[bytes], style: str
    ) -> ImageResult:
        parts: list[dict] = [
            {
                "text": (
                    f"Crie um personagem ilustrado no estilo '{style}' a partir das fotos de "
                    "referencia. TRAVE A IDENTIDADE da crianca: mantenha exatamente o mesmo "
                    "formato de rosto, a mesma cor e formato dos olhos, o mesmo nariz, boca e "
                    "sobrancelhas, a mesma cor/textura/comprimento do cabelo (incluindo franja e "
                    "risca), o mesmo tom de pele e a mesma idade aparente, de modo que a crianca "
                    "permaneca 100% reconhecivel ao lado da foto. Use a mesma roupa das fotos. "
                    "Nao invente tracos, nao 'embeleze', nao mude a etnia nem a idade. "
                    "Sem texto, sem moldura, sem marca d'agua. "
                    f"{prompt}"
                )
            }
        ]
        parts.extend(_inline(img, "image/jpeg") for img in reference_images)
        return await self._generate(parts)

    async def refine_scene(
        self, *, character_ref: bytes, scene: bytes, style: str = "realistic"
    ) -> ImageResult:
        """Segundo passe de cena: corrige o protagonista para bater com o personagem-base,
        sem alterar cenario, pose ou composicao da cena."""
        parts: list[dict] = [
            {
                "text": (
                    "Voce recebe DUAS imagens: (1) o PERSONAGEM de referencia e (2) uma "
                    "ILUSTRACAO de cena de um livro infantil. Sua unica tarefa e corrigir a "
                    "identidade: redesenhe o protagonista da cena para ficar IDENTICO ao "
                    "personagem de referencia, copiando traco a traco: formato do rosto e "
                    "bochechas; olhos (cor, formato, tamanho, espacamento); sobrancelhas; "
                    "nariz; boca e sorriso; cabelo (cor exata, textura, comprimento, franja, "
                    "risca); tom de pele; idade aparente; e a MESMA ROUPA da referencia, peca "
                    "por peca, com as mesmas cores. Se qualquer um desses itens estiver "
                    "diferente na cena, substitua-o pelo da referencia — a referencia SEMPRE "
                    "vence. NAO mude o cenario, a composicao, o enquadramento, a iluminacao, "
                    "a pose nem a acao da cena. Mantenha o mesmo estilo de ilustracao. "
                    "Devolva apenas a cena corrigida."
                )
            },
            _inline(character_ref, "image/png"),
            _inline(scene, "image/png"),
        ]
        return await self._generate(parts)

    async def refine_identity(
        self, *, photo: bytes, illustration: bytes, style: str = "realistic"
    ) -> ImageResult:
        """Segundo passe: corrige a ILUSTRACAO para ficar fiel a FOTO real da crianca."""
        parts: list[dict] = [
            {
                "text": (
                    "Voce recebe DUAS imagens: (1) a FOTO real de uma crianca e (2) uma "
                    "ILUSTRACAO dela. Ajuste a ILUSTRACAO para que o ROSTO fique o mais fiel "
                    "possivel a FOTO: mesmo formato de rosto e bochechas, mesmos olhos (cor, "
                    "formato e espacamento), mesmo nariz, mesma boca e sorriso, mesmas "
                    "sobrancelhas, mesmo cabelo (cor, textura, comprimento, franja e risca), "
                    "mesmo tom de pele e a mesma idade. Preserve o estilo de ilustracao de livro "
                    "infantil (pintura digital suave), a mesma roupa, a mesma pose e o mesmo "
                    "fundo. Nao torne a imagem uma foto. Devolva apenas a ilustracao corrigida."
                )
            },
            _inline(photo, "image/jpeg"),
            _inline(illustration, "image/png"),
        ]
        return await self._generate(parts)

    async def generate_realistic(
        self, *, photo: bytes, prompt: str, negative: str = "", style: str = "realistic"
    ) -> ImageResult:
        text = prompt
        if negative:
            text += f"\n\nNegative prompt (evite/avoid): {negative}"
        parts: list[dict] = [{"text": text}, _inline(photo, "image/jpeg")]
        return await self._generate(parts)

    async def generate_scene(
        self, *, prompt: str, character_ref: bytes, style: str
    ) -> ImageResult:
        parts = [
            {
                "text": (
                    "REGRA CRITICA DE IDENTIDADE (prioridade maxima, acima de qualquer outra "
                    "instrucao): a imagem anexada e a UNICA fonte de verdade para a aparencia "
                    "do protagonista. Voce NAO esta criando um personagem novo — voce esta "
                    "REDESENHANDO EXATAMENTE A MESMA CRIANCA da imagem de referencia em uma "
                    "nova cena. Copie da referencia, traco a traco: formato do rosto e das "
                    "bochechas; olhos (cor, formato, tamanho, espacamento); sobrancelhas; "
                    "nariz; boca e sorriso; cabelo (cor exata, textura, comprimento, franja, "
                    "risca, penteado); tom de pele; idade aparente; proporcoes do corpo; e a "
                    "MESMA ROUPA da referencia, peca por peca, com as mesmas cores. "
                    "Colocada lado a lado com a referencia, a crianca desta cena deve parecer "
                    "dois quadros do mesmo filme. "
                    "PROIBIDO: inventar outra crianca parecida; mudar cabelo, roupa, idade, "
                    "etnia ou tom de pele; 'embelezar' ou estilizar o rosto de forma diferente "
                    "da referencia; adicionar acessorios que nao existem na referencia. "
                    "O que PODE mudar: apenas pose, expressao, acao, enquadramento e cenario, "
                    "conforme a cena descrita. "
                    f"Ilustre no estilo '{style}', identico ao estilo da referencia. "
                    f"Cena: {prompt}"
                )
            },
            _inline(character_ref, "image/png"),
        ]
        return await self._generate(parts)
