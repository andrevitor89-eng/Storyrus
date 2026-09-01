"""Montagem do ebook como livro infantil ilustrado premium (estilo WonderWraps).

build_pdf gera um PDF QUADRADO (formato dos livros personalizados impressos) com:
  1. capa — jaqueta wraparound 2:1 (frente = metade direita com titulo vetorial)
     ou quadrado com faixa dourada;
  2. pagina-poema de abertura ("Para todos os pequenos aventureiros...");
  3. pagina "Feito especialmente para {NOME}" com retrato do personagem em moldura;
  4. dedicatoria opcional dos pais;
  5. paginas da historia em sangria total (estrofe ja composta na arte);
  6. contracapa — metade esquerda da jaqueta, ou poema + selo;
  7. pagina final "Obrigado".
Usa reportlab (puro Python, sem deps de sistema).
Fonte: Andika / Megifera Indica.
"""  # layout v4 — texto composto na arte; titulo da capa no PDF
from __future__ import annotations

import base64
import html
import io
import logging
import math
import os
import unicodedata
from pathlib import Path

logger = logging.getLogger("ebook")

# ------------------------------------------------------------------- fontes
# Fonte oficial do ebook: Megifera Indica (Risma Type).
# Os TTFs sao gerados no build por backend/scripts/fetch_fonts.py.
_FALLBACK_FONTS = {"body": "Times-Bold", "italic": "Times-Italic", "brand": "Helvetica-Bold"}
_fonts_cache: dict | None = None


def _fonts_dir() -> Path | None:
    candidates = [
        os.environ.get("EBOOK_FONTS_DIR"),
        Path(__file__).resolve().parents[1] / "assets" / "fonts",
        Path("app/assets/fonts"),
    ]
    for cand in candidates:
        if cand and Path(cand).is_dir():
            return Path(cand)
    return None


def _fonts() -> dict:
    """Registra a Megifera Indica no reportlab (uma unica vez) e devolve o mapa."""
    global _fonts_cache
    if _fonts_cache is not None:
        return _fonts_cache
    fonts = dict(_FALLBACK_FONTS)
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        base = _fonts_dir()
        regular = base / "MegiferaIndica-Regular.ttf" if base else None
        if regular and regular.exists():
            pdfmetrics.registerFont(TTFont("Indica", str(regular)))
            fonts["body"] = fonts["brand"] = "Indica"
            fonts["italic"] = "Indica"  # Indica regular usado como italic tambem
            logger.info("Fonte do ebook: Megifera Indica (%s)", base)
        else:
            logger.warning("MegiferaIndica-Regular.ttf nao encontrada; usando fontes fallback. "
                           "Rode backend/scripts/fetch_fonts.py para gerar.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao registrar Indica (%s); usando fontes fallback", exc)
    _fonts_cache = fonts
    return fonts

CREAM = (1.0, 0.972, 0.936)
SKY = (0.878, 0.933, 1.0)
NAVY = (0.106, 0.184, 0.373)
GOLD = (0.956, 0.718, 0.251)
CORAL = (0.937, 0.561, 0.294)
LEAF = (0.494, 0.633, 0.420)
INK = (0.20, 0.23, 0.28)

# Textos fixos por idioma (padrão dos livros de referência).
STRINGS = {
    "pt-BR": {
        "opening": (
            "Para todos os pequenos aventureiros,\n"
            "que seus coracoes sejam valentes,\n"
            "e que seus sonhos os levem a lugares\n"
            "incriveis e surpreendentes."
        ),
        "made_for": "Feito especialmente para",
        "blessing": (
            "Que a sua vida seja cheia de\n"
            "coragem, carinho e alegria!\n"
            "Que o seu sempre te leve\n"
            "a amar, proteger e explorar\n"
            "as maravilhas do mundo."
        ),
        "closing": (
            "De florestas a oceanos, e ceus a brilhar,\n"
            "esta grande aventura foi movida pelo amar.\n"
            "Para cada pequeno sonhador de coracao valente,\n"
            "o mundo e seu amigo — siga sonhando em frente."
        ),
        "closing_named": (
            "De florestas a oceanos, e ceus a brilhar,\n"
            "a aventura de {name} foi movida pelo amar.\n"
            "Para cada pequeno sonhador de coracao valente,\n"
            "o mundo e seu amigo — siga sonhando em frente."
        ),
        "thanks": "Obrigado",
        "with_love": "com amor",
        "tagline": "um livro personalizado",
        "preview_title": "Este e um preview",
        "preview_msg": (
            "Este PDF contem apenas {shown} das {total} paginas da historia.\n"
            "Para ter o livro completo, finalize a compra."
        ),
    },
    "en": {
        "opening": (
            "To all the little adventurers,\n"
            "may your hearts be brave,\n"
            "and your dreams take you places,\n"
            "wild and wonderfully paved."
        ),
        "made_for": "Created especially for",
        "blessing": (
            "May your life be filled\n"
            "with courage, kindness, and joy!\n"
            "May your heart always lead you\n"
            "to protect, love, and explore\n"
            "the wonders of the world."
        ),
        "closing": (
            "From forests to oceans, and skies up above,\n"
            "this great adventure was powered by love.\n"
            "For every young dreamer, whose heart beats strong,\n"
            "the world is your friend, so dream and belong."
        ),
        "closing_named": (
            "From forests to oceans, and skies up above,\n"
            "{name}'s great adventure was powered by love.\n"
            "For every young dreamer, whose heart beats strong,\n"
            "the world is your friend, so dream and belong."
        ),
        "thanks": "Thank you",
        "with_love": "with love",
        "tagline": "a personalized book",
        "preview_title": "This is a preview",
        "preview_msg": (
            "This PDF contains only {shown} of {total} story pages.\n"
            "To get the complete book, please complete your purchase."
        ),
    },
}


def _strings(language: str | None) -> dict:
    return STRINGS["en"] if (language or "").lower().startswith("en") else STRINGS["pt-BR"]


def _win(s: str) -> str:
    """Garante texto renderizavel pelas fontes padrao do PDF (WinAnsi/cp1252).

    Acentos do portugues (a-til, cedilha etc.) SAO suportados e preservados;
    apenas caracteres fora do cp1252 (emoji, simbolos raros) sao aproximados.
    """
    out: list[str] = []
    for ch in s or "":
        try:
            ch.encode("cp1252")
            out.append(ch)
        except UnicodeEncodeError:
            out.append(unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode())
    return "".join(out)


def _img_tag(image_bytes: bytes | None, mime: str = "image/png") -> str:
    if not image_bytes:
        return ""
    b64 = base64.b64encode(image_bytes).decode()
    return f'<img class="page-img" src="data:{mime};base64,{b64}"/>'


def build_html(title: str, pages: list[dict]) -> str:
    blocks = [
        f'<section class="page">{_img_tag(p.get("image"), p.get("mime", "image/png"))}'
        f'<p>{html.escape(p.get("text", ""))}</p></section>'
        for p in pages
    ]
    return (
        '<!doctype html><meta charset="utf-8"><title>' + html.escape(title) + "</title>"
        "<style>body{font-family:'Segoe UI',sans-serif}</style>"
        "<h1>" + html.escape(title) + "</h1>" + "".join(blocks)
    )


def render_pdf(html_str: str) -> tuple[bytes, str]:
    try:
        from weasyprint import HTML  # type: ignore

        return HTML(string=html_str).write_pdf(), "application/pdf"
    except Exception as exc:  # noqa: BLE001
        logger.warning("WeasyPrint indisponivel (%s); entregando HTML", exc)
        return html_str.encode("utf-8"), "text/html"


WRAPAROUND_MIN_RATIO = 1.6
BRAND_SITE = "storyrus.ai"
BRAND_EMAIL = "Storyrus@outlook.com"
BRAND_INSTA = "@storyrusbr"


def crop_spread_2x1(image_bytes: bytes) -> bytes:
    """Recorta uma paisagem (ex. 16:9) para 2:1 exato, centro na vertical ou horizontal."""
    from PIL import Image

    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = im.size
    if w <= 0 or h <= 0:
        raise ValueError("imagem de capa vazia")
    ratio = w / h
    if abs(ratio - 2.0) >= 0.01:
        if ratio < 2.0:
            target_h = max(1, round(w / 2))
            top = max(0, (h - target_h) // 2)
            im = im.crop((0, top, w, min(h, top + target_h)))
        else:
            target_w = max(1, round(h * 2))
            left = max(0, (w - target_w) // 2)
            im = im.crop((left, 0, min(w, left + target_w), h))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def is_wraparound_cover(image_bytes: bytes | None) -> bool:
    """True se a arte e larga o bastante para frente+verso (16:9 ou 2:1)."""
    if not image_bytes:
        return False
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(image_bytes))
        w, h = im.size
        return h > 0 and (w / h) >= WRAPAROUND_MIN_RATIO
    except Exception:  # noqa: BLE001
        return False


def _name_page_parts(text: str) -> tuple[str, str, str, list[str]]:
    """Compat: acróstico da página de nome (usado nos testes e no compositor)."""
    from app.workers.page_compose import name_page_parts

    return name_page_parts(text)


def build_pdf(
    title: str,
    pages: list[dict],
    cover: bytes | None = None,
    dedication: str | None = None,
    portrait: bytes | None = None,
    child_name: str | None = None,
    language: str | None = "pt-BR",
    extra_characters: list[dict] | None = None,
    preview_pages: int | None = 3,
) -> bytes:
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas

    tr = _strings(language)
    name = (child_name or "").strip()
    F = _fonts()  # Raleway Light 300 (fallback: fontes base do PDF)

    # Formato QUADRADO, como os livros personalizados impressos (~21,6 x 21,6 cm).
    W = H = 612.0
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))

    # ------------------------------------------------------------------ utils
    def bg(color):
        c.setFillColorRGB(*color)
        c.rect(0, 0, W, H, fill=1, stroke=0)

    def reader(b):
        try:
            return ImageReader(io.BytesIO(b)) if b else None
        except Exception:  # noqa: BLE001
            return None

    def full_bleed(ir):
        """Imagem cobrindo a pagina inteira (sangria), cortando o excesso."""
        iw, ih = ir.getSize()
        s = max(W / iw, H / ih)
        dw, dh = iw * s, ih * s
        c.drawImage(ir, (W - dw) / 2, (H - dh) / 2, dw, dh,
                    preserveAspectRatio=False, mask="auto")

    def bleed_spread_half(ir, side: str):
        """Mostra a metade esquerda (verso) ou direita (frente) de uma jaqueta 2:1."""
        iw, ih = ir.getSize()
        half_w = max(iw / 2.0, 1.0)
        s = max(W / half_w, H / ih)
        dw, dh = iw * s, ih * s
        x = (W - dw) if side == "right" else 0.0
        y = (H - dh) / 2.0
        c.saveState()
        clip = c.beginPath()
        clip.rect(0, 0, W, H)
        c.clipPath(clip, stroke=0, fill=0)
        c.drawImage(ir, x, y, dw, dh, preserveAspectRatio=False, mask="auto")
        c.restoreState()

    def star(cx, cy, r, color=GOLD, alpha=1.0):
        c.setFillAlpha(alpha)
        c.setFillColorRGB(*color)
        p = c.beginPath()
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            (p.moveTo if i == 0 else p.lineTo)(cx + rr * math.cos(ang), cy + rr * math.sin(ang))
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.setFillAlpha(1)

    def flower(cx, cy, r, color=CORAL):
        """Florzinha decorativa simples (5 petalas + miolo)."""
        c.setFillColorRGB(*color)
        for i in range(5):
            ang = i * 2 * math.pi / 5 + math.pi / 2
            c.circle(cx + r * 0.8 * math.cos(ang), cy + r * 0.8 * math.sin(ang), r * 0.55,
                     fill=1, stroke=0)
        c.setFillColorRGB(*GOLD)
        c.circle(cx, cy, r * 0.42, fill=1, stroke=0)

    def leaf(cx, cy, r, ang, color=LEAF):
        c.saveState()
        c.translate(cx, cy)
        c.rotate(ang)
        c.setFillColorRGB(*color)
        p = c.beginPath()
        p.moveTo(0, 0)
        p.curveTo(r * 0.6, r * 0.45, r * 1.4, r * 0.35, r * 2.0, 0)
        p.curveTo(r * 1.4, -r * 0.35, r * 0.6, -r * 0.45, 0, 0)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.restoreState()

    def corner_flourish(cx, cy, flip_x, flip_y):
        """Ramo floral de canto (paginas cerimoniais), estilo das referencias."""
        c.saveState()
        c.translate(cx, cy)
        c.scale(flip_x, flip_y)
        c.setStrokeColorRGB(*LEAF)
        c.setLineWidth(2.2)
        p = c.beginPath()
        p.moveTo(6, 84)
        p.curveTo(10, 44, 26, 20, 78, 8)
        c.drawPath(p, fill=0, stroke=1)
        leaf(14, 62, 8, 20)
        leaf(24, 40, 9, 35)
        leaf(46, 20, 9, 10)
        flower(10, 86, 7)
        flower(72, 10, 6, GOLD)
        c.restoreState()

    def split_lines(text, font, size, max_w):
        """Respeita quebras de linha do texto (versos) e re-quebra o que exceder."""
        lines: list[str] = []
        for raw in (_win(text or "")).splitlines():
            raw = raw.strip()
            if not raw:
                continue
            lines.extend(simpleSplit(raw, font, size, max_w))
        return lines

    def overlay(text, font, size, leading, side, bottom=None, top=None, center_x=None):
        """Texto mesclado na arte: sombra suave + contorno escuro, SEM bloco branco.

        Preserva os versos (quebras de linha). Ancora pela base (bottom) ou topo (top).
        Retorna a altura ocupada.
        """
        cx = center_x if center_x is not None else W / 2
        lines = split_lines(text, font, size, W - 2 * side)
        if not lines:
            return 0
        h = len(lines) * leading
        ytop = (H - top - size) if top is not None else (bottom + h - leading)
        shadow = (0.06, 0.10, 0.20)
        # 1) sombra deslocada (legibilidade sobre qualquer arte)
        c.saveState()
        c.setFillColorRGB(*shadow)
        c.setFillAlpha(0.55)
        c.setFont(font, size)
        y = ytop
        for ln in lines:
            c.drawCentredString(cx + 1.4, y - 1.6, ln)
            y -= leading
        c.restoreState()
        # 2) texto branco com contorno fino escuro (fill + stroke)
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColorRGB(*shadow)
        c.setLineWidth(max(0.8, size / 18.0))
        y = ytop
        for ln in lines:
            t = c.beginText(cx - c.stringWidth(ln, font, size) / 2, y)
            t.setTextRenderMode(2)
            t.setFont(font, size)
            t.textOut(ln)
            c.drawText(t)
            y -= leading
        return h

    def brand_badge(y=34):
        c.setFillAlpha(0.92)
        c.setFillColorRGB(*NAVY)
        c.roundRect(W / 2 - 112, y, 224, 40, 20, fill=1, stroke=0)
        c.setFillAlpha(1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(F["brand"], 13)
        c.drawCentredString(W / 2, y + 22, "Story R Us")
        c.setFillColorRGB(*GOLD)
        c.setFont(F["italic"], 10.5)
        c.drawCentredString(W / 2, y + 8, _win(tr["tagline"]))

    def poem_panel(text, y_center, panel_w=W * 0.78, font=F["italic"], size=15.5,
                   leading=24, framed=True):
        """Poema centralizado num painel claro com moldura fina (estilo referencia)."""
        lines = split_lines(text, font, size, panel_w - 60)
        ph = len(lines) * leading + 56
        x0, y0 = (W - panel_w) / 2, y_center - ph / 2
        if framed:
            c.setFillColorRGB(1, 1, 1)
            c.setFillAlpha(0.88)
            c.roundRect(x0, y0, panel_w, ph, 14, fill=1, stroke=0)
            c.setFillAlpha(1)
            c.setStrokeColorRGB(*GOLD)
            c.setLineWidth(1.6)
            c.roundRect(x0 + 7, y0 + 7, panel_w - 14, ph - 14, 10, fill=0, stroke=1)
        c.setFillColorRGB(*INK)
        c.setFont(font, size)
        y = y0 + ph - 40
        for ln in lines:
            c.drawCentredString(W / 2, y, ln)
            y -= leading
        return y0, ph

    # ------------------------------------------------------------- 1) CAPA
    wraparound = is_wraparound_cover(cover)
    spread_ir = reader(cover) if wraparound else None

    def draw_wraparound_title():
        """Titulo branco no terco superior, sem painel — o ceu da arte e o fundo."""
        t = _win(title or "")
        upper_name = _win(name).upper()
        y_cursor = H * 0.10
        if name and upper_name and upper_name in t.upper():
            i = t.upper().index(upper_name)
            before, after = t[:i].strip(" ,-"), t[i + len(name):].strip(" ,-")
            if before:
                overlay(before, F["italic"], 18, 22, 56, top=y_cursor)
                y_cursor += 28
            overlay(name, F["body"], 36, 40, 40, top=y_cursor)
            y_cursor += 48
            if after:
                overlay(after, F["body"], 20, 26, 48, top=y_cursor)
        else:
            overlay(t, F["body"], 28, 34, 42, top=y_cursor)

    if wraparound and spread_ir:
        bleed_spread_half(spread_ir, "right")
        draw_wraparound_title()
        c.showPage()
    else:
        cov = reader(cover) or (
            reader(pages[0].get("image")) if pages and pages[0].get("image") else None
        )
        bg(SKY)
        if cov:
            full_bleed(cov)
            c.setFillColorRGB(0, 0, 0)
            c.setFillAlpha(0.28)
            c.rect(0, 0, W, H, fill=1, stroke=0)
            c.setFillAlpha(1)

        c.setFillColorRGB(*GOLD)
        c.setFillAlpha(0.85)
        c.rect(0, H - 110, W, 110, fill=1, stroke=0)
        c.setFillAlpha(1)

        t = _win(title or "")
        upper_name = _win(name).upper()
        if name and upper_name and upper_name in t.upper():
            i = t.upper().index(upper_name)
            before, after = t[:i].strip(" ,-"), t[i + len(name):].strip(" ,-")
            y_cursor = H - 38
            if before:
                overlay(before, F["italic"], 20, 24, 56, top=y_cursor)
                y_cursor += 30
            overlay(name, F["body"], 42, 46, 40, top=y_cursor)
            y_cursor += 54
            if after:
                overlay(after, F["body"], 24, 30, 48, top=y_cursor)
        else:
            overlay(t, F["body"], 34, 40, 42, top=H - 36)

        star(46, H - 52, 10, GOLD)
        star(W - 50, H - 84, 8, CORAL)
        star(W / 2 - 80, H - 140, 6, GOLD, 0.7)
        star(W / 2 + 80, H - 140, 6, GOLD, 0.7)

        c.setStrokeColorRGB(*GOLD)
        c.setLineWidth(2.5)
        c.setFillAlpha(0)
        c.roundRect(18, 18, W - 36, H - 36, 16, fill=0, stroke=1)
        c.setFillAlpha(1)

        brand_badge()
        c.showPage()

    # -------------------------------------------- 2) POEMA DE ABERTURA
    bg(CREAM)
    corner_flourish(26, H - 120, 1, 1)
    corner_flourish(W - 26, 120, -1, -1)
    c.setFillColorRGB(*INK)
    c.setFont(F["italic"], 17)
    lines = split_lines(tr["opening"], F["italic"], 17, W * 0.66)
    y = H / 2 + (len(lines) - 1) * 14
    for ln in lines:
        c.drawCentredString(W / 2, y, ln)
        y -= 28
    c.showPage()

    # ------------------------- 3) FEITO ESPECIALMENTE PARA {NOME}
    if name or portrait:
        bg(CREAM)
        corner_flourish(26, H - 120, 1, 1)
        corner_flourish(W - 26, 120, -1, -1)
        c.setFillColorRGB(*INK)
        c.setFont(F["italic"], 15)
        c.drawCentredString(W / 2, H - 96, _win(tr["made_for"]))
        if name:
            c.setFillColorRGB(*NAVY)
            c.setFont(F["body"], 34)
            c.drawCentredString(W / 2, H - 136, _win(name).upper())

        # retrato circular do protagonista
        pr = reader(portrait)
        if pr:
            R = 108.0
            cx, cy = W / 2, H / 2 + 6
            c.saveState()
            p = c.beginPath()
            p.circle(cx, cy, R)
            c.clipPath(p, stroke=0, fill=0)
            iw, ih = pr.getSize()
            s = max((2 * R) / iw, (2 * R) / ih)
            dw, dh = iw * s, ih * s
            c.drawImage(pr, cx - dw / 2, cy - dh / 2, dw, dh,
                        preserveAspectRatio=False, mask="auto")
            c.restoreState()
            c.setStrokeColorRGB(*GOLD)
            c.setLineWidth(4)
            c.circle(cx, cy, R, fill=0, stroke=1)
            star(cx + R * 0.82, cy + R * 0.82, 9, GOLD)

        # personagens extras (pequenos circulos ao redor do protagonista)
        if extra_characters:
            extras = extra_characters[:4]  # no maximo 4 extras
            positions = [
                (W / 2 - 160, H / 2 + 6),
                (W / 2 + 160, H / 2 + 6),
                (W / 2 - 130, H / 2 - 120),
                (W / 2 + 130, H / 2 - 120),
            ]
            for idx, ec in enumerate(extras):
                ec_bytes = ec.get("image_bytes")
                if not ec_bytes:
                    continue
                ec_reader = reader(ec_bytes)
                if not ec_reader or idx >= len(positions):
                    continue
                ecx, ecy = positions[idx]
                eR = 42.0
                c.saveState()
                ep = c.beginPath()
                ep.circle(ecx, ecy, eR)
                c.clipPath(ep, stroke=0, fill=0)
                eiw, eih = ec_reader.getSize()
                es = max((2 * eR) / eiw, (2 * eR) / eih)
                edw, edh = eiw * es, eih * es
                c.drawImage(ec_reader, ecx - edw / 2, ecy - edh / 2, edw, edh,
                            preserveAspectRatio=False, mask="auto")
                c.restoreState()
                c.setStrokeColorRGB(*CORAL)
                c.setLineWidth(2.5)
                c.circle(ecx, ecy, eR, fill=0, stroke=1)

        # bencao
        c.setFillColorRGB(*INK)
        c.setFont(F["italic"], 13.5)
        y = H / 2 - 132
        for ln in split_lines(tr["blessing"], F["italic"], 13.5, W * 0.62):
            c.drawCentredString(W / 2, y, ln)
            y -= 20
        c.showPage()

    # --------------------------------------- 4) DEDICATORIA DOS PAIS
    if dedication and dedication.strip():
        bg(CREAM)
        c.setStrokeColorRGB(*GOLD)
        c.setLineWidth(2)
        c.roundRect(W * 0.12, H * 0.28, W * 0.76, H * 0.44, 22, fill=0, stroke=1)
        star(W / 2, H * 0.66, 12, GOLD)
        c.setFillColorRGB(*NAVY)
        c.setFont(F["italic"], 17)
        lines = split_lines(dedication.strip(), F["italic"], 17, W * 0.60)
        y = H / 2 + (len(lines) - 1) * 13
        for ln in lines:
            c.drawCentredString(W / 2, y, ln)
            y -= 26
        c.setFillColorRGB(*CORAL)
        c.setFont(F["italic"], 13)
        c.drawCentredString(W / 2, H * 0.32, _win(tr["with_love"]))
        c.showPage()

    # ------ 5) PAGINAS (arte em sangria; estrofe ja composta na imagem)
    # Se preview_pages estiver definido, limita as paginas da historia
    is_preview = preview_pages is not None and len(pages) > preview_pages
    visible_pages = pages[:preview_pages] if is_preview else pages

    for p in visible_pages:
        layout = (p.get("layout") or "story").strip()
        text = p.get("text", "")
        if layout == "dedication":
            bg(CREAM)
            corner_flourish(26, H - 120, 1, 1)
            corner_flourish(W - 26, 120, -1, -1)
            raw = (text or "").replace("\r\n", "\n").strip()
            poem, sep, prose = raw.partition("\n\n")
            if not sep:
                poem, prose = raw, ""
            poem_lines = split_lines(poem, F["italic"], 17, W * 0.66)
            prose_lines = split_lines(prose, F["italic"], 15, W * 0.68) if prose.strip() else []
            items: list[tuple[str, str, float, float]] = [
                (ln, F["italic"], 17.0, 28.0) for ln in poem_lines
            ]
            if poem_lines and prose_lines:
                items.append(("", F["italic"], 0.0, 12.0))
            items.extend((ln, F["italic"], 15.0, 22.0) for ln in prose_lines)
            total_h = sum(item[3] for item in items) if items else 0.0
            y = H / 2 + total_h / 2
            c.setFillColorRGB(*INK)
            for ln, font, size, leading in items:
                if ln:
                    c.setFont(font, size)
                    c.drawCentredString(W / 2, y - size * 0.75, _win(ln))
                y -= leading
            c.showPage()
            continue
        bg(CREAM)
        ir = reader(p.get("image"))
        if ir:
            full_bleed(ir)
        c.showPage()

    # Pagina de preview: aviso de que o livro completo esta disponivel
    if is_preview:
        bg(CREAM)
        c.setFillColorRGB(*NAVY)
        c.setFont(F["body"], 22)
        c.drawCentredString(W / 2, H / 2 + 40, _win(tr["preview_title"]))
        c.setFillColorRGB(*INK)
        c.setFont(F["italic"], 15)
        preview_lines = split_lines(
            tr["preview_msg"].format(total=len(pages), shown=preview_pages),
            F["italic"], 15, W * 0.65
        )
        y = H / 2
        for ln in preview_lines:
            c.drawCentredString(W / 2, y, ln)
            y -= 24
        star(W / 2 - 60, H / 2 - 60, 8, GOLD)
        star(W / 2 + 60, H / 2 - 60, 8, CORAL)
        brand_badge(y=H * 0.28)
        c.showPage()

    # --------------------- 6) CONTRACAPA
    if wraparound and spread_ir:
        bleed_spread_half(spread_ir, "left")
        card_w, card_h = W * 0.72, 220.0
        card_x = (W - card_w) / 2
        card_y = (H - card_h) / 2 - 16
        c.setFillColorRGB(*NAVY)
        c.setFillAlpha(0.88)
        c.roundRect(card_x, card_y, card_w, card_h, 18, fill=1, stroke=0)
        c.setFillAlpha(1)
        c.setStrokeColorRGB(*GOLD)
        c.setLineWidth(1.8)
        c.roundRect(card_x + 8, card_y + 8, card_w - 16, card_h - 16, 14, fill=0, stroke=1)
        y = card_y + card_h - 48
        c.setFillColorRGB(1, 1, 1)
        c.setFont(F["brand"], 16)
        c.drawCentredString(W / 2, y, "Story R Us")
        y -= 22
        c.setFillColorRGB(*GOLD)
        c.setFont(F["italic"], 11)
        c.drawCentredString(W / 2, y, _win(tr["tagline"]))
        y -= 28
        c.setFillColorRGB(1, 1, 1)
        c.setFont(F["body"], 13)
        for line in (BRAND_SITE, BRAND_EMAIL, BRAND_INSTA):
            c.drawCentredString(W / 2, y, line)
            y -= 20
        c.showPage()
    else:
        bg(SKY)
        last = reader(pages[-1].get("image")) if pages and pages[-1].get("image") else None
        if last:
            full_bleed(last)
            c.setFillColorRGB(1, 1, 1)
            c.setFillAlpha(0.25)
            c.rect(0, 0, W, H, fill=1, stroke=0)
            c.setFillAlpha(1)
        closing = tr["closing_named"].format(name=_win(name)) if name else tr["closing"]
        poem_panel(closing, H * 0.62)
        brand_badge(y=H * 0.24)
        star(60, H - 70, 10, GOLD)
        star(W - 64, H - 96, 8, CORAL)
        c.showPage()

    # ----------------------------------------- 7) OBRIGADO / THANK YOU
    bg(CREAM)
    corner_flourish(26, H - 120, 1, 1)
    corner_flourish(W - 26, 120, -1, -1)
    # faixa (ribbon) central estilo referencia
    rw, rh = 300.0, 64.0
    rx, ry = W / 2 - rw / 2, H / 2 - rh / 2
    c.setFillColorRGB(*CORAL)
    # pontas dobradas
    pth = c.beginPath()
    pth.moveTo(rx - 26, ry + rh / 2)
    pth.lineTo(rx + 8, ry + rh)
    pth.lineTo(rx + 8, ry)
    pth.close()
    c.drawPath(pth, fill=1, stroke=0)
    pth = c.beginPath()
    pth.moveTo(rx + rw + 26, ry + rh / 2)
    pth.lineTo(rx + rw - 8, ry + rh)
    pth.lineTo(rx + rw - 8, ry)
    pth.close()
    c.drawPath(pth, fill=1, stroke=0)
    c.roundRect(rx, ry, rw, rh, 10, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(F["body"], 30)
    c.drawCentredString(W / 2, ry + rh / 2 - 10, _win(tr["thanks"]))
    star(W / 2 - rw / 2 - 52, H / 2 + 46, 9, GOLD)
    star(W / 2 + rw / 2 + 52, H / 2 - 52, 8, GOLD)
    c.setFillColorRGB(*NAVY)
    c.setFont(F["brand"], 12)
    c.drawCentredString(W / 2, 46, "Story R Us")
    c.showPage()

    c.save()
    return buf.getvalue()
