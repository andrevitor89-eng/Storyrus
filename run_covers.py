import asyncio, io, os
from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from PIL import Image

OUT = "/app/_out"
os.makedirs(OUT, exist_ok=True)

BASE = (
    "CAPA de livro infantil com qualidade de BEST-SELLER premium, pintura digital rica e "
    "vibrante, iluminacao cinematografica quente, profundidade e atmosfera magica. "
    "Formato RETRATO vertical (proporcao 3:4), a arte preenche TODO o quadro, sem bordas "
    "brancas, sem margens vazias. "
    "TITULO '{titulo}' no terco superior, em letras grandes, arredondadas e bem legiveis, "
    "com acabamento decorativo no estilo do tema: {letras}. Grafia EXATA, letra por letra: "
    "'{titulo}' — nao invente nem troque letras. "
    "O protagonista e a crianca da IMAGEM DE REFERENCIA — mesmo rosto, cabelo, tom de pele "
    "e idade — em POSE DINAMICA e cheia de vida, interagindo com a cena (nunca parada "
    "posando para a camera): {cena}. "
    "Composicao de capa profissional: titulo no topo, acao no centro, cenario envolvente "
    "com detalhes encantadores. Sem nenhum outro texto, sem autor, sem moldura, sem marca d'agua."
)

# (arquivo, titulo, letras tematicas, referencia, cena)
CENA_FLORESTA = (
    "a menina corre descalca por uma trilha magica ao entardecer, cercada por vaga-lumes "
    "brilhantes, com uma corca, uma raposa e um coelhinho correndo junto dela, arvores "
    "gigantes com luzinhas e cogumelos coloridos. O titulo esta TODO EM MAIUSCULAS, em duas "
    "linhas: linha 1 'FLORESTA' e linha 2 'ENCANTADA'. A palavra da linha 2 tem exatamente "
    "estas 9 letras, nesta ordem: E N C A N T A D A. PROIBIDO usar a letra H — a palavra "
    "correta em portugues e 'ENCANTADA' (sem H apos o C), nunca 'ENCHANTADA' ou 'ENCHANTED'. "
    "Copie letra por letra"
)

JOBS = [
    ("capa-floresta", "FLORESTA ENCANTADA",
     "letras verdes com folhinhas, flores e pontos de luz de vaga-lume",
     "/app/_ref-floresta.jpg", CENA_FLORESTA),
    ("capa-floresta2", "FLORESTA ENCANTADA",
     "letras verdes iluminadas com musgo, folhinhas e vaga-lumes",
     "/app/_ref-floresta.jpg", CENA_FLORESTA),
]


def to_jpg(raw: bytes, path: str, maxw: int = 900):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width > maxw:
        h = int(im.height * maxw / im.width)
        im = im.resize((maxw, h), Image.LANCZOS)
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


async def main():
    img = NanoBananaImageProvider()
    for base, titulo, letras, ref_path, cena in JOBS:
        try:
            ref = open(ref_path, "rb").read()
            prompt = BASE.format(titulo=titulo, letras=letras, cena=cena)
            r = await img.generate_scene(prompt=prompt, character_ref=ref,
                                         style="pintura digital de livro infantil premium")
            n = to_jpg(r.image_bytes, f"{OUT}/{base}.jpg")
            print(f"{base}: OK jpg={n}", flush=True)
        except Exception as e:
            print(f"{base}: ERRO {e!r}", flush=True)


asyncio.run(main())
