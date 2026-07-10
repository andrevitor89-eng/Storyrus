"""Montagem do ebook como livro infantil ilustrado para impressao.

build_pdf gera um PDF em formato de livro (proporcao retrato ~3:4) com as
ilustracoes em SANGRIA TOTAL (ocupando a pagina inteira, sem molduras brancas)
e o texto da historinha numa faixa arredondada translucida sobre a arte.
Usa reportlab (puro Python, sem dependencias de sistema).
"""
from __future__ import annotations

import base64
import html
import io
import logging
import math

logger = logging.getLogger("ebook")

CREAM = (1.0, 0.968, 0.925)
SKY = (0.878, 0.933, 1.0)
NAVY = (0.106, 0.184, 0.373)
GOLD = (0.956, 0.718, 0.251)
CORAL = (0.937, 0.561, 0.294)


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


def build_pdf(title: str, pages: list[dict], cover: bytes | None = None) -> bytes:
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas

    # formato de livro infantil (retrato ~3:4). "para impressao": alta contagem de pts.
    W, H = 612.0, 828.0  # ~ 8.5 x 11.5 in, proporcao 0.739 (casa com a arte gerada)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))

    def bg(color):
        c.setFillColorRGB(*color)
        c.rect(0, 0, W, H, fill=1, stroke=0)

    def reader(b):
        try:
            return ImageReader(io.BytesIO(b)) if b else None
        except Exception:  # noqa: BLE001
            return None

    def cover_draw(ir):
        """Desenha a imagem cobrindo a pagina inteira (sangria), cortando o excesso."""
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

    def plate(text, font, size, leading, pad, bottom, side, fill=(1, 1, 1), alpha=0.9,
              text_color=NAVY, star_top=True):
        maxw = W - 2 * side - 2 * 18
        lines = simpleSplit(text or "", font, size, maxw)
        ph = len(lines) * leading + pad * 2
        px, py, pw = side, bottom, W - 2 * side
        c.setFillAlpha(alpha)
        c.setFillColorRGB(*fill)
        c.roundRect(px, py, pw, ph, 20, fill=1, stroke=0)
        c.setFillAlpha(1)
        if star_top:
            star(W / 2, py + ph, 8, GOLD)
        c.setFillColorRGB(*text_color)
        c.setFont(font, size)
        y = py + ph - pad - size * 0.8
        for ln in lines:
            c.drawCentredString(W / 2, y, ln)
            y -= leading
        return ph

    # ---------------- CAPA (arte em sangria) ----------------
    cov = reader(cover) or (reader(pages[0].get("image")) if pages and pages[0].get("image") else None)
    bg(SKY)
    if cov:
        cover_draw(cov)
    # faixa do titulo no topo
    plate(title, "Times-Bold", 30, 36, 20, H - 40 - (len(simpleSplit(title, "Times-Bold", 30, W - 76)) * 36 + 40),
          30, alpha=0.92, star_top=False)
    star(46, H - 60, 11, GOLD)
    star(W - 52, H - 96, 9, CORAL)
    # selo inferior
    c.setFillAlpha(0.92)
    c.setFillColorRGB(*NAVY)
    c.roundRect(W / 2 - 118, 34, 236, 40, 20, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, 56, "Story R Us")
    c.setFillColorRGB(*GOLD)
    c.setFont("Times-Italic", 11)
    c.drawCentredString(W / 2, 42, "um livro personalizado")
    c.showPage()

    # ---------------- PAGINAS (arte em sangria + texto sobre a arte) ----------------
    for i, p in enumerate(pages, 1):
        bg(CREAM)
        ir = reader(p.get("image"))
        if ir:
            cover_draw(ir)
        plate(p.get("text", ""), "Times-Roman", 16, 23, 18, 40, 34, alpha=0.9)
        # numero da pagina (discreto, canto)
        c.setFillColorRGB(*GOLD)
        c.circle(W - 34, H - 34, 13, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(W - 34, H - 38, str(i))
        c.showPage()

    # ---------------- FIM ----------------
    bg(SKY)
    c.setFillColorRGB(*GOLD)
    c.circle(W / 2, H / 2 + 6, 110, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.circle(W / 2, H / 2 + 6, 96, fill=1, stroke=0)
    star(W / 2, H / 2 + 84, 14, GOLD)
    c.setFillColorRGB(*NAVY)
    c.setFont("Times-Bold", 40)
    c.drawCentredString(W / 2, H / 2 - 8, "Fim")
    c.setFillColorRGB(*CORAL)
    c.setFont("Times-Italic", 14)
    c.drawCentredString(W / 2, H / 2 - 42, "feito com amor")
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W / 2, 46, "Story R Us")
    c.showPage()

    c.save()
    return buf.getvalue()
