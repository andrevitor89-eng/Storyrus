"""Versao para rodar DENTRO do container da API (mesmo padrao de run_ba.py /
run_books4.py): gera avatar (antes/depois) e 1 livro tematico para Matteo,
Oliver e Sofia. O avatar e' o MODELO PRINCIPAL: trava a identidade usada em
todas as cenas do livro e no retrato do PDF (nao ha referencia "personagem"
separada).

IDEMPOTENTE: cada etapa checa se o arquivo de saida ja existe e pula -- pode
rodar de novo sem regenerar (e sem gastar credito) o que ja foi feito.

Espera as fotos em /app/_fotos/{matteo,oliver,sofia}.png (o .bat copia antes
de rodar). Saida em /app/_out/<nome>/ (o .bat copia de volta pro Windows
depois).
"""
import asyncio
import gc
import io
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.text_anthropic import AnthropicTextProvider
from app.ai_clients.book_prompts import AVATAR_PROMPT, STYLE, build_scene_prompt
from app.workers.ebook import build_pdf

FOTOS_DIR = "/app/_fotos"
OUT = "/app/_out"
PAGES = 6

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
        y0 = H - (lh * len(lines) + pad * 2) - int(H * 0.035)
        y = y0 + pad
        for ln in lines:
            tw = draw.textlength(ln, font=font)
            x = (W - tw) / 2
            draw.text((x + 1.5, y + 1.5), ln, font=font, fill=(10, 14, 24, 160))
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                draw.text((x + dx, y + dy), ln, font=font, fill=(20, 24, 36))
            draw.text((x, y), ln, font=font, fill=(255, 255, 255))
            y += lh
    im.save(path, "JPEG", quality=88, optimize=True)
    return os.path.getsize(path)


async def run_child(name: str, photo_file: str, age: int, theme: str,
                     img: NanoBananaImageProvider, txt: AnthropicTextProvider) -> dict:
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

    # -------- avatar ilustrado (antes/depois) -- MODELO PRINCIPAL --------
    # (sem referencia "personagem" separada: o avatar trava a identidade usada
    # em todas as cenas e no retrato do PDF)
    avatar_png = f"{child_out}/avatar-{lname}.png"
    char_ref = None
    if os.path.exists(avatar_png):
        char_ref = open(avatar_png, "rb").read()
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
            char_ref = raw
            log["avatar"] = f"ok ({n} bytes)"
        except Exception as e:
            log["avatar"] = f"ERRO {e!r}"

    # -------- historia (1x, salva em json p/ nao gerar de novo) --------
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
        log["livro"] = "pendente: sem avatar de referencia (historia ja esta pronta)"
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
            try:
                rf = await img.refine_scene(character_ref=char_ref, scene=sc.image_bytes, style="realistic")
                if rf and rf.image_bytes:
                    sc.image_bytes = rf.image_bytes
                    log[f"pagina-{i}-refinamento"] = "ok"
            except Exception as e:
                log[f"pagina-{i}-refinamento"] = f"pulado: {e!r}"
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
            pdf = build_pdf(title, page_objs, portrait=char_ref, child_name=name, language="pt-BR",
                             preview_pages=None)
            open(pdf_path, "wb").write(pdf)
            open(f"{child_out}/livro-{lname}-{theme}.txt", "w").write(
                f"{title}\n\n" + "\n\n".join(pages)
            )
            log["pdf"] = f"ok -> {pdf_path}"
        except Exception as e:
            log["pdf"] = f"ERRO {e!r}"

    return log


async def main():
    os.makedirs(OUT, exist_ok=True)
    img = NanoBananaImageProvider()
    txt = AnthropicTextProvider()
    full_log = {}
    for name, (photo_file, age, theme) in CHILDREN.items():
        print(f"=== {name} (tema: {theme}, idade assumida: {age}) ===", flush=True)
        full_log[name] = await run_child(name, photo_file, age, theme, img, txt)
        print(json.dumps(full_log[name], ensure_ascii=False, indent=2), flush=True)
    open(f"{OUT}/log-geral.json", "w").write(json.dumps(full_log, ensure_ascii=False, indent=2))
    print("=== RESUMO ===")
    print(json.dumps(full_log, ensure_ascii=False, indent=2))


asyncio.run(main())
