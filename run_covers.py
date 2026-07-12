import asyncio, io, os
from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from PIL import Image

OUT = "/app/_out"
os.makedirs(OUT, exist_ok=True)

BASE = (
    "CAPA de livro infantil premium em pintura digital suave e vibrante, formato RETRATO "
    "(vertical, proporcao 3:4, como uma capa de livro real). O TITULO '{titulo}' deve aparecer "
    "escrito na capa, no terco superior, em letras grandes, arredondadas, ludicas e bem "
    "legiveis (escreva EXATAMENTE '{titulo}', sem erros de grafia). O protagonista e a crianca "
    "da IMAGEM DE REFERENCIA — mantenha o mesmo rosto, cabelo, tom de pele e idade — em "
    "destaque no centro da capa, feliz, {cena}. Composicao classica de capa: titulo no topo, "
    "personagem no centro, cenario envolvente ao redor. Sem nenhum outro texto, sem nome de "
    "autor, sem moldura, sem bordas, sem marca d'agua."
)

# (arquivo de saida, titulo na capa, referencia de personagem, cena)
JOBS = [
    ("capa-dino", "MUNDO DOS DINOSSAUROS", "/app/_ref-dino.jpg",
     "num vale pre-historico ensolarado, ao lado de filhotes de dinossauros doceis e simpaticos. "
     "O titulo esta TODO EM MAIUSCULAS, em duas linhas: linha 1 'MUNDO DOS' e linha 2 "
     "'DINOSSAUROS'. A palavra da linha 2 tem exatamente estas 11 letras, nesta ordem: "
     "D I N O S S A U R O S. Copie letra por letra, nao troque nem invente letras"),
    ("capa-dino2", "Mundo dos Dinossauros", "/app/_ref-dino.jpg",
     "num vale pre-historico ensolarado, ao lado de filhotes de dinossauros doceis e simpaticos. "
     "O titulo esta em duas linhas: linha 1 'Mundo dos' e linha 2 'Dinossauros'. "
     "A palavra 'Dinossauros' e soletrada assim: D-i-n-o-s-s-a-u-r-o-s (dois S no meio, "
     "termina em 'auros'). Verifique a grafia antes de desenhar, letra por letra"),
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
    for base, titulo, ref_path, cena in JOBS:
        try:
            ref = open(ref_path, "rb").read()
            prompt = BASE.format(titulo=titulo, cena=cena)
            r = await img.generate_scene(prompt=prompt, character_ref=ref,
                                         style="pintura digital de livro infantil premium")
            n = to_jpg(r.image_bytes, f"{OUT}/{base}.jpg")
            print(f"{base}: OK jpg={n}", flush=True)
        except Exception as e:
            print(f"{base}: ERRO {e!r}", flush=True)


asyncio.run(main())
