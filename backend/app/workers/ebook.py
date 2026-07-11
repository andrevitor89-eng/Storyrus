"""Montagem do ebook como livro infantil ilustrado para impressao.

build_pdf gera um PDF em formato de livro (proporcao retrato ~3:4) com as
ilustracoes em SANGRIA TOTAL (ocupando a pagina inteira, sem molduras brancas)
e o texto da historinha MESCLADO na arte (sombra + contorno, sem bloco branco
e sem numeracao de pagina). Usa reportlab (puro Python, sem deps de sistema).
"""
from __future__ import annotations

import base64
import html
import io
import logging
import math
import unicodedata

logger = logging.getLogger("ebook")

CREAM = (1.0, 0.968, 0.925)
SKY = (0.878, 0.933, 1.0)
NAVY = (0.106, 0.184, 0.373)
GOLD = (0.956, 0.718, 0.251)
CORAL = (0.937, 0.561, 0.294)


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


def build_pdf(title: str, pages: list[dict], cover: bytes | None = None,
              dedication: str | None = None) -> bytes:
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

    def overlay(text, font, size, leading, side, bottom=None, top=None):
        """Texto mesclado na arte: sombra suave + contorno escuro, SEM bloco branco.

        Ancora pela base (bottom) ou pelo topo (top). Retorna a altura ocupada.
        """
        lines = simpleSplit(_win(text or ""), font, size, W - 2 * side)
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
            c.drawCentredString(W / 2 + 1.4, y - 1.6, ln)
            y -= leading
        c.restoreState()
        # 2) texto branco com contorno fino escuro (fill + stroke)
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColorRGB(*shadow)
        c.setLineWidth(max(0.8, size / 18.0))
        y = ytop
        for ln in lines:
            t = c.beginText(W / 2 - c.stringWidth(ln, font, size) / 2, y)
            t.setTextRenderMode(2)
            t.setFont(font, size)
            t.textOut(ln)
            c.drawText(t)
            y -= leading
        return h

    # ---------------- CAPA (arte em sangria) ----------------
    cov = reader(cover) or (reader(pages[0].get("image")) if pages and pages[0].get("image") else None)
    bg(SKY)
    if cov:
        cover_draw(cov)
    # titulo mesclado na arte, no topo
    overlay(title, "Times-Bold", 32, 38, 40, top=44)
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

    # ---------------- DEDICATÓRIA ----------------
    if dedication and dedication.strip():
        bg(CREAM)
        c.setStrokeColorRGB(*GOLD)
        c.setLineWidth(2)
        c.roundRect(W * 0.12, H * 0.30, W * 0.76, H * 0.40, 22, fill=0, stroke=1)
        star(W / 2, H * 0.66, 12, GOLD)
        c.setFillColorRGB(*NAVY)
        c.setFont("Times-Italic", 17)
        y = H * 0.58
        for ln in simpleSplit(_win(dedication.strip()), "Times-Italic", 17, W * 0.60):
            c.drawCentredString(W / 2, y, ln)
            y -= 26
        c.setFillColorRGB(*CORAL)
        c.setFont("Times-Italic", 13)
        c.drawCentredString(W / 2, H * 0.34, "com amor")
        c.showPage()

    # ------- PAGINAS (arte em sangria + texto mesclado, sem numeracao) -------
    for p in pages:
        bg(CREAM)
        ir = reader(p.get("image"))
        if ir:
            cover_draw(ir)
        overlay(p.get("text", ""), "Times-Bold", 17, 24, 40, bottom=48)
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
