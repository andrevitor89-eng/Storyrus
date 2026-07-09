import asyncio, os, re, json
from app.ai_clients.image_nano_banana import NanoBananaImageProvider
from app.ai_clients.text_anthropic import AnthropicTextProvider
from app.workers.ebook import build_pdf

OUT = "/app/_out"
os.makedirs(OUT, exist_ok=True)
photo = open("/app/_photo.jpg", "rb").read()
STYLE = "livro infantil, ilustracao em aquarela suave, cores quentes, tracos gentis"
NAME = "Theo"


async def main():
    img = NanoBananaImageProvider()
    txt = AnthropicTextProvider()
    log = {}

    # 1) personagem ilustrado (Gemini) a partir da foto
    char_ref = None
    try:
        ch = await img.generate_character(
            prompt=f"Bebe alegre chamado {NAME}, protagonista de uma historia infantil.",
            reference_images=[photo], style=STYLE,
        )
        char_ref = ch.image_bytes
        open(f"{OUT}/personagem.png", "wb").write(char_ref)
        log["personagem"] = f"ok {len(char_ref)} bytes"
    except Exception as e:
        log["personagem"] = f"ERRO: {e!r}"

    # 2) historia (Claude)
    story = ""
    try:
        st = await txt.generate_story(
            brief=f"Um bebe curioso chamado {NAME} que descobre um jardim magico cheio de amiguinhos e aprende sobre coragem e carinho.",
            style=STYLE, pages=4,
        )
        story = st.text
        open(f"{OUT}/historia.txt", "w").write(story)
        log["historia"] = f"ok {len(story)} chars"
    except Exception as e:
        log["historia"] = f"ERRO: {e!r}"

    parts = re.split(r"P[aá]gina\s*\d+\s*:", story)
    pages = [p.strip() for p in parts if p.strip()][:4]
    if not pages:
        pages = [f"Era uma vez um bebe curioso chamado {NAME}."]

    # 3) legendas curtas em PT correto (Claude)
    try:
        caps = await txt.summarize_pages(pages=pages, style=STYLE)
    except Exception as e:
        caps = list(pages)
        log["legendas"] = f"ERRO: {e!r}"
    if len(caps) < len(pages):
        caps = caps + pages[len(caps):]

    # 4) ilustracao por pagina (Gemini) usando o personagem como referencia
    page_objs = []
    for i, (pg, cap) in enumerate(zip(pages, caps), 1):
        imgbytes = None
        if char_ref:
            try:
                sc = await img.generate_scene(prompt=pg[:600], character_ref=char_ref, style=STYLE)
                imgbytes = sc.image_bytes
                open(f"{OUT}/pagina-{i}.png", "wb").write(imgbytes)
                log[f"cena{i}"] = f"ok {len(imgbytes)} bytes"
            except Exception as e:
                log[f"cena{i}"] = f"ERRO: {e!r}"
        page_objs.append({"text": cap, "image": imgbytes, "mime": "image/png"})

    # 5) e-book PDF
    try:
        pdf = build_pdf(f"A Aventura de {NAME}", page_objs)
        open(f"{OUT}/ebook.pdf", "wb").write(pdf)
        log["ebook"] = f"ok {len(pdf)} bytes"
    except Exception as e:
        log["ebook"] = f"ERRO: {e!r}"

    open(f"{OUT}/log.json", "w").write(json.dumps(log, ensure_ascii=False, indent=2))
    print(json.dumps(log, ensure_ascii=False))


asyncio.run(main())
