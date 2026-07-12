"""Regenera os 4 livros de exemplo da landing (mesma foto, historias novas educativas).

Roda dentro do container da API. Saidas em /app/_out:
  personagem4.jpg, <tema>-1..6.jpg (ilustracao + legenda), livro4-<tema>.pdf/.txt
"""
import asyncio, gc, glob, io, json, os, re

from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.text_anthropic import AnthropicTextProvider
from app.workers.handlers import THEME_EDU
from app.workers.ebook import build_pdf
from PIL import Image, ImageDraw, ImageFont

OUT = "/app/_out"
os.makedirs(OUT, exist_ok=True)
photo = open("/app/_photo.jpg", "rb").read()

STYLE = ("estilo fotorrealista de livro infantil premium: a crianca deve parecer uma FOTO real, "
         "rosto identico a foto original, pele, cabelo e olhos naturais, iluminacao suave, "
         "cenario ilustrado agradavel ao fundo, alta qualidade, sem texto ou letras na imagem")
PAGES = 6

# Circo nao existe no THEME_EDU do backend: guia proprio.
CIRCO_EDU = (
    "as artes do circo e a coragem de se apresentar: malabarismo treina as maos, "
    "equilibrista usa os bracos abertos para se equilibrar, a lona do circo se chama tenda",
    "a chegada a tenda iluminada -> conhecer os artistas (cada um mostra sua arte) -> "
    "aprender um numero simples -> o friozinho na barriga antes do palco -> a apresentacao "
    "no climax -> aplausos e a licao de que treinar e ter coragem fazem a magia acontecer",
)

BOOKS = [
    ("mar", "underwater", "um mergulho magico no fundo do mar, com peixinhos e uma tartaruga amiga"),
    ("flor", "fantasy", "uma floresta encantada cheia de bichinhos gentis e luzes de vagalume"),
    ("dino", "dinosaurs", "um vale ensolarado de dinossauros doceis e amigaveis"),
    ("circo", None, "uma noite magica no circo das luzes, com baloes, tenda iluminada e estrelas"),
]


def _font(size: int):
    for pat in ("/usr/local/lib/python*/site-packages/reportlab/fonts/Vera.ttf",
                "/usr/share/fonts/**/*.ttf"):
        hits = glob.glob(pat, recursive=True)
        if hits:
            try:
                return ImageFont.truetype(hits[0], size)
            except Exception:
                continue
    return None


def compose_page(img_bytes: bytes, caption: str, path: str, w: int = 1180) -> int:
    """Ilustracao + faixa arredondada com a estrofe (estilo pagina de livro)."""
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width > w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    W, H = im.size
    font = _font(max(22, W // 38))
    lines = [ln.strip() for ln in caption.splitlines() if ln.strip()][:4]
    if font and lines:
        draw = ImageDraw.Draw(im, "RGBA")
        lh = int(font.size * 1.35)
        pad = int(font.size * 0.9)
        bh = lh * len(lines) + pad * 2
        y0 = H - bh - int(H * 0.035)
        x0, x1 = int(W * 0.06), int(W * 0.94)
        draw.rounded_rectangle([x0, y0, x1, y0 + bh], radius=pad, fill=(255, 253, 246, 235))
        y = y0 + pad
        for ln in lines:
            tw = draw.textlength(ln, font=font)
            draw.text(((W - tw) / 2, y), ln, font=font, fill=(45, 52, 70))
            y += lh
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


async def main():
    img = NanoBananaImageProvider()
    txt = AnthropicTextProvider()
    log = {}

    # 1) personagem realista (uma vez, mesma foto de sempre)
    char_ref = None
    try:
        ch = await img.generate_realistic(
            photo=photo,
            prompt=("Retrato fotorrealista desta crianca como protagonista de um livro infantil, "
                    "mantendo o rosto IDENTICO a foto, pele e cabelo naturais, fundo suave e agradavel."),
            negative="desenho, cartoon, aquarela, rosto diferente, distorcao",
            style="realistic",
        )
        char_ref = ch.image_bytes
        open(f"{OUT}/personagem4.jpg", "wb").write(char_ref)
        log["personagem"] = "ok"
        gc.collect()
    except Exception as e:
        log["personagem"] = f"ERRO: {e!r}"

    # 2) 4 livros com historias novas educativas
    for slug, theme_key, cenario in BOOKS:
        focus, sequence = (THEME_EDU["pt"][theme_key] if theme_key else CIRCO_EDU)
        brief = (
            f"Invente uma historia infantil ORIGINAL e encantadora com um bebe curioso como "
            f"protagonista, no cenario: {cenario}. Escolha um nome fofo. "
            f"APRENDIZADO (essencial): a historia deve ENSINAR de forma ludica — {focus}. "
            "Insira 2 ou 3 curiosidades REAIS, simples e adequadas a idade dentro da acao "
            "(nunca em tom de aula). SEQUENCIA LOGICA obrigatoria da jornada, adaptada com "
            f"criatividade: {sequence}. No final, o protagonista percebe com alegria o que aprendeu. "
            "Na PRIMEIRA linha escreva 'Titulo: <um titulo curto e encantador>' e so depois as paginas."
        )
        story = ""
        try:
            st = await txt.generate_story(brief=brief, style=STYLE, pages=PAGES)
            story = st.text
        except Exception as e:
            log[f"hist-{slug}"] = f"ERRO: {e!r}"
            continue

        mt = re.search(r"T[ií]tulo\s*:\s*(.+)", story)
        title = (mt.group(1).strip().strip('"') if mt else f"Aventura no {slug}")[:60]
        body = re.sub(r"^.*T[ií]tulo\s*:.*$", "", story, count=1, flags=re.M)
        parts = re.split(r"P[aá]gina\s*\d+\s*:", body)
        pages = [p.strip() for p in parts if p.strip()][:PAGES]
        log[f"hist-{slug}"] = f"ok '{title}' {len(pages)}p"

        page_objs = []
        for i, pg in enumerate(pages, 1):
            try:
                sc = await img.generate_scene(
                    prompt=(pg.replace("\n", " ")[:480] +
                            " Cena fotorrealista, crianca identica a referencia, sem texto/letras."),
                    character_ref=char_ref, style=STYLE,
                )
                n = compose_page(sc.image_bytes, pg, f"{OUT}/{slug}-{i}.jpg")
                page_objs.append({"text": pg, "image": sc.image_bytes, "mime": "image/jpeg"})
                log[f"{slug}-p{i}"] = f"ok {n}"
                del sc
                gc.collect()
            except Exception as e:
                log[f"{slug}-p{i}"] = f"ERRO: {e!r}"

        try:
            pdf = build_pdf(title, page_objs, portrait=char_ref)
            open(f"{OUT}/livro4-{slug}.pdf", "wb").write(pdf)
            open(f"{OUT}/livro4-{slug}.txt", "w").write(f"{title}\n\n" + "\n\n".join(pages))
        except Exception as e:
            log[f"pdf-{slug}"] = f"ERRO: {e!r}"

    open(f"{OUT}/log4.json", "w").write(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False))


asyncio.run(main())
