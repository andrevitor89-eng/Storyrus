import asyncio, os, re, json, io, gc
from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.text_anthropic import AnthropicTextProvider
from app.workers.ebook import build_pdf

OUT = "/app/_out"
os.makedirs(OUT, exist_ok=True)
photo = open("/app/_photo.jpg", "rb").read()
STYLE = "livro infantil, ilustracao em aquarela suave, cores quentes, tracos gentis, sem texto na imagem"
PAGES = 3


def small(b, w=1180):
    """Compacta a imagem (JPEG) para reduzir memoria e tamanho do PDF."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(b)).convert("RGB")
        if im.width > w:
            im = im.resize((w, int(im.height * w / im.width)))
        o = io.BytesIO()
        im.save(o, "JPEG", quality=82, optimize=True)
        return o.getvalue(), "image/jpeg"
    except Exception:
        return b, "image/png"


async def main():
    img = NanoBananaImageProvider()
    txt = AnthropicTextProvider()
    log = {}

    char_ref = None
    cover_bytes = None
    try:
        ch = await img.generate_character(
            prompt="Menino alegre e curioso, protagonista de uma historia infantil.",
            reference_images=[photo], style=STYLE,
        )
        char_ref = ch.image_bytes
        cover_bytes, _ = small(char_ref)
        open(f"{OUT}/personagem.jpg", "wb").write(cover_bytes)
        log["personagem"] = f"ok {len(cover_bytes)}"
        gc.collect()
    except Exception as e:
        log["personagem"] = f"ERRO: {e!r}"

    brief = (
        "Invente uma historia infantil original, encantadora e coerente, com um menino "
        "alegre e curioso como protagonista. Escolha voce mesmo o nome do menino e um tema "
        "magico. IMPORTANTE: na PRIMEIRA linha escreva 'Titulo: <um titulo curto>' e so depois as paginas."
    )
    story = ""
    try:
        st = await txt.generate_story(brief=brief, style=STYLE, pages=PAGES)
        story = st.text
        open(f"{OUT}/historia.txt", "w").write(story)
        log["historia"] = f"ok {len(story)}"
    except Exception as e:
        log["historia"] = f"ERRO: {e!r}"

    mt = re.search(r"T[ií]tulo\s*:\s*(.+)", story)
    title = (mt.group(1).strip().strip('"') if mt else "Uma Aventura Encantada")[:60]
    body = re.sub(r"^.*T[ií]tulo\s*:.*$", "", story, count=1, flags=re.M)
    parts = re.split(r"P[aá]gina\s*\d+\s*:", body)
    pages = [p.strip() for p in parts if p.strip()][:PAGES]
    if not pages:
        pages = ["Era uma vez um menino curioso e cheio de alegria."]

    try:
        caps = await txt.summarize_pages(pages=pages, style=STYLE)
    except Exception as e:
        caps = list(pages)
        log["legendas"] = f"ERRO: {e!r}"
    if len(caps) < len(pages):
        caps = caps + pages[len(caps):]

    page_objs = []
    for i, (pg, cap) in enumerate(zip(pages, caps), 1):
        ib = None
        mime = "image/png"
        if char_ref:
            try:
                sc = await img.generate_scene(
                    prompt=pg[:500] + " Nao inclua nenhum texto, letra ou palavra na imagem.",
                    character_ref=char_ref, style=STYLE,
                )
                ib, mime = small(sc.image_bytes)
                open(f"{OUT}/pagina-{i}.jpg", "wb").write(ib)
                log[f"cena{i}"] = f"ok {len(ib)}"
                del sc; gc.collect()
            except Exception as e:
                log[f"cena{i}"] = f"ERRO: {e!r}"
        page_objs.append({"text": cap, "image": ib, "mime": mime})

    try:
        pdf = build_pdf(title, page_objs, cover=cover_bytes)
        open(f"{OUT}/ebook.pdf", "wb").write(pdf)
        log["ebook"] = f"ok {len(pdf)}"
        log["titulo"] = title
    except Exception as e:
        log["ebook"] = f"ERRO: {e!r}"

    open(f"{OUT}/log.json", "w").write(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False))


asyncio.run(main())
