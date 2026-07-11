"""Montagem do ebook como livro infantil ilustrado premium (estilo WonderWraps).

build_pdf gera um PDF QUADRADO (formato dos livros personalizados impressos) com:
  1. capa em sangria total com o título (nome da criança em destaque) + selo da marca;
  2. página-poema de abertura ("Para todos os pequenos aventureiros...");
  3. página "Feito especialmente para {NOME}" com retrato do personagem em moldura;
  4. dedicatória opcional dos pais;
  5. páginas da história em sangria total com a estrofe mesclada na arte;
  6. contracapa com poema de encerramento em moldura + selo;
  7. página final "Obrigado".
Usa reportlab (puro Python, sem deps de sistema).
"""  # layout v2 (referencia WonderWraps/TellMyTale)
from __future__ import annotations

import base64
import html
import io
import logging
import math
import unicodedata

logger = logging.getLogger("ebook")

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
            "que seus corações sejam valentes,\n"
            "e que seus sonhos os levem a lugares\n"
            "incríveis e surpreendentes."
        ),
        "made_for": "Feito especialmente para",
        "blessing": (
            "Que a sua vida seja cheia de\n"
            "coragem, carinho e alegria!\n"
            "Que o seu coração sempre te leve\n"
            "a amar, proteger e explorar\n"
            "as maravilhas do mundo."
        ),
        "closing": (
            "De florestas a oceanos, e céus a brilhar,\n"
            "esta grande aventura foi movida pelo amar.\n"
            "Para cada pequeno sonhador de coração valente,\n"
            "o mundo é seu amigo — siga sonhando em frente."
        ),
        "closing_named": (
            "De florestas a oceanos, e céus a brilhar,\n"
            "a aventura de {name} foi movida pelo amar.\n"
            "Para cada pequeno sonhador de coração valente,\n"
            "o mundo é seu amigo — siga sonhando em frente."
        ),
        "thanks": "Obrigado",
        "with_love": "com amor",
        "tagline": "um livro personalizado",
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
        "<h1>" + html.escape(title) + "</h1>" + "".join(blocks)
    )


def render_pdf(html_str: str) -> tuple[bytes, str]:
    try:
        from weasyprint import HTML  # type: ignore

        return HTML(string=html_str).write_pdf(), "application/pdf"
    except Exception as exc:  # noqa: BLE001
        logger.warning("WeasyPrint indisponivel (%s); entregando HTML", exc)
        return html_str.encode("utf-8"), "text/html"


def build_pdf(
    title: str,
    pages: list[dict],
    cover: bytes | None = None,
    dedication: str | None = None,
    portrait: bytes | None = None,
    child_name: str | None = None,
    language: str | None = "pt-BR",
) -> bytes:
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas

    tr = _strings(language)
    name = (child_name or "").strip()

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
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(W / 2, y + 22, "Story R Us")
        c.setFillColorRGB(*GOLD)
        c.setFont("Times-Italic", 10.5)
        c.drawCentredString(W / 2, y + 8, _win(tr["tagline"]))

    def poem_panel(text, y_center, panel_w=W * 0.78, font="Times-Italic", size=15.5,
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
    cov = reader(cover) or (reader(pages[0].get("image")) if pages and pages[0].get("image") else None)
    bg(SKY)
    if cov:
        full_bleed(cov)
    # titulo com o nome em destaque (linha propria, maior), mesclado na arte
    t = _win(title or "")
    upper_name = _win(name).upper()
    if name and upper_name and upper_name in t.upper():
        i = t.upper().index(upper_name)
        before, after = t[:i].strip(" ,-"), t[i + len(name):].strip(" ,-")
        y_cursor = 40
        if before:
            overlay(before, "Times-Italic", 20, 24, 56, top=y_cursor)
            y_cursor += 30
        overlay(name if name.isupper() else name, "Times-Bold", 40, 44, 40, top=y_cursor)
        y_cursor += 50
        if after:
            overlay(after, "Times-Bold", 24, 30, 48, top=y_cursor)
    else:
        overlay(t, "Times-Bold", 32, 38, 42, top=46)
    star(46, H - 52, 10, GOLD)
    star(W - 50, H - 84, 8, CORAL)
    brand_badge()
    c.showPage()

    # -------------------------------------------- 2) POEMA DE ABERTURA
    bg(CREAM)
    corner_flourish(26, H - 120, 1, 1)
    corner_flourish(W - 26, 120, -1, -1)
    c.setFillColorRGB(*INK)
    c.setFont("Times-Italic", 17)
    lines = split_lines(tr["opening"], "Times-Italic", 17, W * 0.66)
    y = H / 2 + (len(lines) - 1) * 14
    for ln in lines:
        c.drawCentredString(W / 2, y, ln)
        y -= 28
    c.showPage()

    # ------------------------- 3) FEITO ESPECIALMENTE PARA {NOME}
    if name or portrait:
        bg(CREAM)
        corner_flourish(26, H - 120, 1, 1)
        corner_flourish(W - 26, H - 120, -1, 1)
        corner_flourish(26, 120, 1, -1)
        corner_flourish(W - 26, 120, -1, -1)
        c.setFillColorRGB(*INK)
        c.setFont("Times-Italic", 15)
        c.drawCentredString(W / 2, H - 96, _win(tr["made_for"]))
        if name:
            c.setFillColorRGB(*NAVY)
            c.setFont("Times-Bold", 34)
            c.drawCentredString(W / 2, H - 136, _win(name).upper())
        # retrato circular com anel dourado
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
        # bencao
        c.setFillColorRGB(*INK)
        c.setFont("Times-Italic", 13.5)
        y = H / 2 - 132
        for ln in split_lines(tr["blessing"], "Times-Italic", 13.5, W * 0.62):
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
        c.setFont("Times-Italic", 17)
        lines = split_lines(dedication.strip(), "Times-Italic", 17, W * 0.60)
        y = H / 2 + (len(lines) - 1) * 13
        for ln in lines:
            c.drawCentredString(W / 2, y, ln)
            y -= 26
        c.setFillColorRGB(*CORAL)
        c.setFont("Times-Italic", 13)
        c.drawCentredString(W / 2, H * 0.32, _win(tr["with_love"]))
        c.showPage()

    # ------ 5) PAGINAS (arte em sangria + estrofe mesclada, sem numeracao)
    for idx, p in enumerate(pages):
        bg(CREAM)
        ir = reader(p.get("image"))
        if ir:
            full_bleed(ir)
        text = p.get("text", "")
        # alterna texto embaixo/em cima, como nos livros de referencia
        if idx % 2 == 0:
            overlay(text, "Times-Bold", 16, 23, 42, bottom=44)
        else:
            overlay(text, "Times-Bold", 16, 23, 42, top=38)
        c.showPage()

    # --------------------- 6) CONTRACAPA: POEMA DE ENCERRAMENTO
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
    c.setFont("Times-Bold", 30)
    c.drawCentredString(W / 2, ry + rh / 2 - 10, _win(tr["thanks"]))
    star(W / 2 - rw / 2 - 52, H / 2 + 46, 9, GOLD)
    star(W / 2 + rw / 2 + 52, H / 2 - 52, 8, GOLD)
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, 46, "Story R Us")
    c.showPage()

    c.save()
    return buf.getvalue()
