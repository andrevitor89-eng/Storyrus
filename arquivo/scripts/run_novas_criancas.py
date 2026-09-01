"""Gera avatar (antes/depois + personagem fotorrealista) e 1 livro tematico
para cada crianca nova (Matteo, Oliver, Sofia), a partir das fotos em
fotos-novas/. Roda standalone (sem Docker/DB), reaproveitando os mesmos
ai_clients e o mesmo montador de ebook (reportlab) do backend real.

IDEMPOTENTE: cada etapa checa se o arquivo de saida ja existe e pula (nao
regenera, nao gasta credito de novo) -- pode rodar varias vezes seguidas ate
completar tudo, mesmo que uma chamada seja interrompida no meio.

Saida em app_out/<nome>/:
  foto-<nome>.jpg          - foto original convertida
  avatar-<nome>.png/.jpg   - ilustracao "antes/depois" (estilo pintura)
  personagem-<nome>.jpg    - referencia fotorrealista (rosto identico) usada
                             para ilustrar as paginas do livro
  story-<nome>.json        - titulo + texto das paginas (gerado 1x pela IA)
  raw-<tema>-N.jpg          - cena N crua (usada no PDF)
  <tema>-N.jpg              - cena N com legenda (preview)
  livro-<nome>-<tema>.pdf   - ebook final (formato quadrado, capa com o nome)

Uso:
  python3 run_novas_criancas.py --dry-run           # so valida, sem API
  python3 run_novas_criancas.py                     # roda os 3
  python3 run_novas_criancas.py --child Matteo       # roda so 1 (resume)
"""
import argparse
import asyncio
import gc
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)  # app.config le ".env" relativo ao cwd -> precisa ser backend/

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from app.ai_clients.image_nano_banana import NanoBananaImageProvider  # noqa: E402
from app.ai_clients.text_anthropic import AnthropicTextProvider  # noqa: E402
from app.ai_clients.book_prompts import AVATAR_PROMPT, STYLE, build_scene_prompt  # noqa: E402
from app.workers.ebook import build_pdf  # noqa: E402

FOTOS_DIR = os.path.join(ROOT, "fotos-novas")
OUT = os.path.join(ROOT, "app_out")
PAGES = 6

CHAR_PROMPT = (
    "Retrato fotorrealista desta crianca como protagonista de um livro "
    "infantil, mantendo o rosto IDENTICO a foto, pele e cabelo naturais, "
    "fundo suave e agradavel."
)
CHAR_NEGATIVE = "desenho, cartoon, aquarela, rosto diferente, distorcao"

THEMES = {
    "mar": (
        "um mergulho magico no fundo do mar, com peixinhos e uma tartaruga amiga",
        "os animais marinhos e como eles respiram e se movem na agua: peixes "
        "usam guelras, golfinhos sao mamiferos e precisam subir para respirar, "
        "tartarugas nadam devagar mas sao super resistentes",
        "a chegada na praia -> o primeiro mergulho encantado -> conhecer um "
        "amigo do mar que ensina algo -> um pequeno susto (correnteza, gruta "
        "escura) superado com calma e curiosidade -> a grande descoberta no "
        "fundo do mar -> voltar para a praia contando o que aprendeu",
    ),
    "flor": (
        "uma floresta encantada cheia de bichinhos gentis e luzes de vagalume",
        "como as plantas crescem: sementes precisam de agua, sol e carinho "
        "para virar flores, e cada flor tem uma cor e um cheiro proprio",
        "a entrada na floresta ao entardecer -> encontrar uma clareira magica "
        "-> conhecer um bichinho que precisa de ajuda para florescer um "
        "jardim -> um pequeno obstaculo (flor murcha, caminho escuro) -> o "
        "jardim floresce no climax com a ajuda da crianca -> a festa das "
        "luzes de vagalume no final",
    ),
    "dino": (
        "um vale ensolarado de dinossauros doceis e amigaveis",
        "tipos de dinossauros e seus habitos: uns comiam plantas (herbivoros), "
        "outros eram gigantes gentis, e todos viviam ha muito muito tempo",
        "a chegada ao vale dos dinossauros -> conhecer um filhote de "
        "dinossauro curioso -> uma pequena aventura (atravessar um rio, achar "
        "um ovo perdido) -> resolver o desafio com coragem -> o reencontro "
        "feliz no climax -> a despedida com a licao de cuidar dos amigos",
    ),
}

# nome -> (arquivo foto, idade aproximada, tema)
CHILDREN = {
    "Matteo": ("matteo.png", 2, "mar"),
    "Oliver": ("oliver.png", 5, "dino"),
    "Sofia": ("sofia.png", 3, "flor"),
}


def _font(size: int):
    import glob
    for pat in ("/usr/local/lib/python*/site-packages/reportlab/fonts/Vera.ttf",
                "/usr/share/fonts/**/*.ttf"):
        hits = glob.glob(pat, recursive=True)
        if hits:
            try:
                return ImageFont.truetype(hits[0], size)
            except Exception:
                continue
    return None


def to_jpg(raw: bytes, path: str, maxw: int = 900) -> int:
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width > maxw:
        h = int(im.height * maxw / im.width)
        im = im.resize((maxw, h), Image.LANCZOS)
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


def compose_page(img_bytes: bytes, caption: str, path: str, w: int = 1180) -> int:
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


async def run_child(name: str, photo_file: str, age: int, theme: str,
                     img: NanoBananaImageProvider, txt: AnthropicTextProvider,
                     dry_run: bool) -> dict:
    log: dict = {}
    lname = name.lower()
    child_out = os.path.join(OUT, lname)
    os.makedirs(child_out, exist_ok=True)

    src = os.path.join(FOTOS_DIR, photo_file)
    if not os.path.exists(src):
        log["erro"] = f"foto nao encontrada: {src}"
        return log
    photo = open(src, "rb").read()

    foto_path = f"{child_out}/foto-{lname}.jpg"
    if os.path.exists(foto_path):
        log["foto"] = "ja existia (pulado)"
    else:
        try:
            b = to_jpg(photo, foto_path)
            log["foto"] = f"ok ({b} bytes)"
        except Exception as e:
            log["foto"] = f"ERRO {e!r}"

    if dry_run:
        log["modo"] = "dry-run: nenhuma chamada de API feita"
        return log

    # -------- avatar ilustrado (antes/depois) --------
    avatar_png = f"{child_out}/avatar-{lname}.png"
    if os.path.exists(avatar_png):
        log["avatar"] = "ja existia (pulado)"
    else:
        try:
            r = await img.generate_character(
                prompt=AVATAR_PROMPT,
                reference_images=[photo],
                style=STYLE,
            )
            raw = r.image_bytes
            try:
                rf = await img.refine_identity(photo=photo, illustration=raw, style="realistic")
                if rf and rf.image_bytes:
                    raw = rf.image_bytes
                    log["avatar_refinamento"] = "ok"
            except Exception as e:
                log["avatar_refinamento"] = f"pulado: {e!r}"
            open(avatar_png, "wb").write(raw)
            n = to_jpg(raw, f"{child_out}/avatar-{lname}.jpg")
            log["avatar"] = f"ok ({n} bytes)"
        except Exception as e:
            log["avatar"] = f"ERRO {e!r}"

    # -------- personagem fotorrealista (referencia p/ as cenas) --------
    char_path = f"{child_out}/personagem-{lname}.jpg"
    char_ref = None
    if os.path.exists(char_path):
        char_ref = open(char_path, "rb").read()
        log["personagem"] = "ja existia (pulado)"
    else:
        try:
            ch = await img.generate_realistic(
                photo=photo, prompt=CHAR_PROMPT, negative=CHAR_NEGATIVE, style="realistic",
            )
            char_ref = ch.image_bytes
            open(char_path, "wb").write(char_ref)
            log["personagem"] = "ok"
            gc.collect()
        except Exception as e:
            log["personagem"] = f"ERRO {e!r}"

    # -------- historia (1x, salva em json p/ nao gerar de novo) --------
    # Gerada independente do personagem (nao precisa da imagem pronta), assim
    # o texto fica disponivel mesmo se a etapa de imagem falhar/for bloqueada.
    story_json = f"{child_out}/story-{lname}.json"
    cenario, focus, sequence = THEMES[theme]
    if os.path.exists(story_json):
        data = json.loads(open(story_json).read())
        title, pages = data["title"], data["pages"]
        log["historia"] = f"ja existia (pulado) '{title}' {len(pages)}p"
    else:
        brief = (
            f"Invente uma historia infantil ORIGINAL e encantadora com {name} como "
            f"protagonista, no cenario: {cenario}. "
            f"APRENDIZADO (essencial): a historia deve ENSINAR de forma ludica — {focus}. "
            "Insira 2 ou 3 curiosidades REAIS, simples e adequadas a idade dentro da "
            "acao (nunca em tom de aula). SEQUENCIA LOGICA obrigatoria da jornada, "
            f"adaptada com criatividade: {sequence}. No final, {name} percebe com "
            "alegria o que aprendeu. Na PRIMEIRA linha escreva 'Titulo: <um titulo "
            "curto e encantador>' e so depois as paginas."
        )
        title = f"{name} e a Aventura no {theme.title()}"
        try:
            st = await txt.generate_story(brief=brief, style=STYLE, pages=PAGES, age=age)
            story = st.text
            mt = re.search(r"T[ií]tulo\s*:\s*(.+)", story)
            title = (mt.group(1).strip().strip('"') if mt else title)[:60]
            body = re.sub(r"^.*T[ií]tulo\s*:.*$", "", story, count=1, flags=re.M)
            parts = re.split(r"P[aá]gina\s*\d+\s*:", body)
            pages = [p.strip() for p in parts if p.strip()][:PAGES]
            open(story_json, "w").write(json.dumps({"title": title, "pages": pages}, ensure_ascii=False))
            log["historia"] = f"ok '{title}' {len(pages)}p"
        except Exception as e:
            log["historia"] = f"ERRO {e!r}"
            return log

    if char_ref is None:
        log["livro"] = "pendente: sem personagem de referencia (historia ja esta pronta)"
        return log

    # -------- cenas ilustradas (uma por pagina, com resume) --------
    page_objs = []
    for i, pg in enumerate(pages, 1):
        raw_path = f"{child_out}/raw-{theme}-{i}.jpg"
        if os.path.exists(raw_path):
            page_objs.append({"text": pg, "image": open(raw_path, "rb").read(), "mime": "image/jpeg"})
            log[f"pagina-{i}"] = "ja existia (pulado)"
            continue
        try:
            sc = await img.generate_scene(
                prompt=build_scene_prompt(
                    page=i,
                    text=pg.replace("\n", " ")[:900],
                    child_name=name,
                ),
                character_ref=char_ref,
                style=STYLE,
            )
            open(raw_path, "wb").write(sc.image_bytes)
            n = compose_page(sc.image_bytes, pg, f"{child_out}/{theme}-{i}.jpg")
            page_objs.append({"text": pg, "image": sc.image_bytes, "mime": "image/jpeg"})
            log[f"pagina-{i}"] = f"ok ({n} bytes)"
            del sc
            gc.collect()
        except Exception as e:
            log[f"pagina-{i}"] = f"ERRO {e!r}"

    # -------- PDF final (so quando todas as paginas existem) --------
    pdf_path = f"{child_out}/livro-{lname}-{theme}.pdf"
    if len(page_objs) < len(pages):
        log["pdf"] = f"pendente: faltam {len(pages) - len(page_objs)} pagina(s)"
    elif os.path.exists(pdf_path):
        log["pdf"] = "ja existia (pulado)"
    else:
        try:
            pdf = build_pdf(title, page_objs, portrait=char_ref, child_name=name, language="pt-BR")
            open(pdf_path, "wb").write(pdf)
            open(f"{child_out}/livro-{lname}-{theme}.txt", "w").write(
                f"{title}\n\n" + "\n\n".join(pages)
            )
            log["pdf"] = f"ok -> {pdf_path}"
        except Exception as e:
            log["pdf"] = f"ERRO {e!r}"

    return log


async def main(dry_run: bool, only_child: str | None):
    os.makedirs(OUT, exist_ok=True)
    img = NanoBananaImageProvider()
    txt = AnthropicTextProvider()
    full_log = {}
    items = CHILDREN.items() if not only_child else [
        (k, v) for k, v in CHILDREN.items() if k.lower() == only_child.lower()
    ]
    for name, (photo_file, age, theme) in items:
        print(f"=== {name} (tema: {theme}, idade assumida: {age}) ===", flush=True)
        full_log[name] = await run_child(name, photo_file, age, theme, img, txt, dry_run)
        print(json.dumps(full_log[name], ensure_ascii=False, indent=2), flush=True)
    log_path = f"{OUT}/log-geral.json"
    prev = json.loads(open(log_path).read()) if os.path.exists(log_path) else {}
    prev.update(full_log)
    open(log_path, "w").write(json.dumps(prev, ensure_ascii=False, indent=2))
    print("=== RESUMO ===")
    print(json.dumps(full_log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                     help="so valida fotos/imports, nao chama nenhuma API paga")
    ap.add_argument("--child", default=None, help="processa so 1 crianca (Matteo/Oliver/Sofia)")
    args = ap.parse_args()
    asyncio.run(main(args.dry_run, args.child))
