import asyncio, os, re, json, io, gc
from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.text_anthropic import AnthropicTextProvider
from app.workers.ebook import build_pdf

OUT = "/app/_out"
os.makedirs(OUT, exist_ok=True)
photo = open("/app/_photo.jpg", "rb").read()
# estilo BEM realista (quase foto), rosto fiel ao bebe real
STYLE = ("estilo fotorrealista de livro infantil premium: a crianca deve parecer uma FOTO real, "
         "rosto identico a foto original, pele, cabelo e olhos naturais, iluminacao suave, "
         "cenario ilustrado agradavel ao fundo, alta qualidade, sem texto ou letras na imagem")
PAGES = 3
THEMES = [
    "uma aventura no espaco, entre estrelas, planetas e um foguete de brinquedo",
    "um mergulho magico no fundo do mar, com peixinhos e uma tartaruga amiga",
    "uma floresta encantada cheia de bichinhos gentis e luzes de vagalume",
    "um mundo de dinossauros dociles num vale cheio de flores",
    "uma noite magica no circo das luzes, com balões e estrelas",
]


def small(b, w=1180):
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(b)).convert("RGB")
        if im.width > w:
            im = im.resize((w, int(im.height * w / im.width)))
        o = io.BytesIO()
        im.save(o, "JPEG", quality=88, optimize=True)
        return o.getvalue(), "image/jpeg"
    except Exception:
        return b, "image/png"


async def main():
    img = NanoBananaImageProvider()
    txt = AnthropicTextProvider()
    log = {}

    # 1) personagem realista (uma vez, reutilizado nos 5 livros)
    char_ref = None
    cover = None
    try:
        ch = await img.generate_realistic(
            photo=photo,
            prompt=("Retrato fotorrealista desta crianca como protagonista de um livro infantil, "
                    "mantendo o rosto IDENTICO a foto, pele e cabelo naturais, fundo suave e agradavel."),
            negative="desenho, cartoon, aquarela, rosto diferente, distorcao",
            style="realistic",
        )
        char_ref = ch.image_bytes
        cover, _ = small(char_ref)
        open(f"{OUT}/personagem.jpg", "wb").write(cover)
        log["personagem"] = f"ok {len(cover)}"
        gc.collect()
    except Exception as e:
        log["personagem"] = f"ERRO: {e!r}"

    # 2) 5 livros com temas diferentes
    for bi, theme in enumerate(THEMES, 1):
        story = ""
        try:
            brief = (f"Invente uma historia infantil original, curta e encantadora, com um bebe/crianca "
                     f"curiosa como protagonista, no tema: {theme}. Escolha um nome fofo. Na PRIMEIRA "
                     f"linha escreva 'Titulo: <um titulo curto e encantador>' e so depois as paginas.")
            st = await txt.generate_story(brief=brief, style=STYLE, pages=PAGES)
            story = st.text
        except Exception as e:
            log[f"hist{bi}"] = f"ERRO: {e!r}"

        mt = re.search(r"T[ií]tulo\s*:\s*(.+)", story)
        title = (mt.group(1).strip().strip('"') if mt else f"Aventura {bi}")[:60]
        body = re.sub(r"^.*T[ií]tulo\s*:.*$", "", story, count=1, flags=re.M)
        parts = re.split(r"P[aá]gina\s*\d+\s*:", body)
        pages = [p.strip() for p in parts if p.strip()][:PAGES]
        if not pages:
            pages = ["Era uma vez uma crianca curiosa cheia de alegria."]

        try:
            caps = await txt.summarize_pages(pages=pages, style=STYLE)
        except Exception:
            caps = list(pages)
        if len(caps) < len(pages):
            caps = caps + pages[len(caps):]

        page_objs = []
        for i, (pg, cap) in enumerate(zip(pages, caps), 1):
            ib = None
            mime = "image/png"
            if char_ref:
                try:
                    sc = await img.generate_scene(
                        prompt=pg[:480] + " Cena fotorrealista, crianca identica a referencia, sem texto/letras.",
                        character_ref=char_ref, style=STYLE,
                    )
                    ib, mime = small(sc.image_bytes)
                    open(f"{OUT}/l{bi}-p{i}.jpg", "wb").write(ib)
                    del sc
                    gc.collect()
                except Exception as e:
                    log[f"b{bi}c{i}"] = f"ERRO: {e!r}"
            page_objs.append({"text": cap, "image": ib, "mime": mime})

        try:
            pdf = build_pdf(title, page_objs, cover=cover)
            open(f"{OUT}/livro-{bi}.pdf", "wb").write(pdf)
            open(f"{OUT}/livro-{bi}.txt", "w").write(f"{title}\n\n" + "\n\n".join(pages))
            log[f"livro{bi}"] = f"ok '{title}' {len(pdf)}b"
        except Exception as e:
            log[f"livro{bi}"] = f"ERRO: {e!r}"

    open(f"{OUT}/log.json", "w").write(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False))


asyncio.run(main())
