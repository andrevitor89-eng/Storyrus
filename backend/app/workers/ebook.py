"""Montagem do ebook (HTML -> PDF).

Gera um HTML autocontido (capa + paginas com ilustracao e texto) e converte para
PDF. A conversao usa um renderer injetavel: por padrao tenta WeasyPrint; se nao
estiver instalado, devolve o HTML em bytes (entregavel ainda valido) e registra
a limitacao no meta. Mantemos isso atras de uma funcao para trocar o motor sem
tocar o handler.
"""
from __future__ import annotations

import base64
import html
import logging

logger = logging.getLogger("ebook")


def _img_tag(image_bytes: bytes | None, mime: str = "image/png") -> str:
    if not image_bytes:
        return ""
    b64 = base64.b64encode(image_bytes).decode()
    return f'<img class="page-img" src="data:{mime};base64,{b64}" alt="ilustracao"/>'


def build_html(title: str, pages: list[dict]) -> str:
    """pages: [{ "text": str, "image": bytes|None, "mime": str }]."""
    blocks = []
    for i, p in enumerate(pages, 1):
        blocks.append(
            f'<section class="page">{_img_tag(p.get("image"), p.get("mime", "image/png"))}'
            f'<p class="page-text">{html.escape(p.get("text", ""))}</p>'
            f'<span class="page-num">{i}</span></section>'
        )
    return f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8"/>
<style>
  @page {{ size: A5; margin: 0; }}
  body {{ font-family: Georgia, serif; margin: 0; }}
  .cover {{ display:flex; align-items:center; justify-content:center; height:100vh;
            background:#1f2a44; color:#fff; text-align:center; padding:2rem; }}
  .cover h1 {{ font-size: 2.2rem; }}
  .page {{ page-break-after: always; padding: 2rem; position: relative; min-height: 100vh; box-sizing:border-box; }}
  .page-img {{ width:100%; border-radius: 12px; margin-bottom: 1rem; }}
  .page-text {{ font-size: 1.1rem; line-height: 1.6; }}
  .page-num {{ position:absolute; bottom:1rem; right:1.5rem; color:#888; }}
</style></head><body>
<section class="cover"><h1>{html.escape(title)}</h1></section>
{''.join(blocks)}
</body></html>"""


def render_pdf(html_str: str) -> tuple[bytes, str]:
    """Retorna (bytes, mime). Tenta WeasyPrint; fallback = HTML."""
    try:
        from weasyprint import HTML  # type: ignore

        pdf = HTML(string=html_str).write_pdf()
        return pdf, "application/pdf"
    except Exception as exc:  # noqa: BLE001
        logger.warning("WeasyPrint indisponivel (%s); entregando HTML", exc)
        return html_str.encode("utf-8"), "text/html"


def build_pdf(title: str, pages: list[dict]) -> bytes:
    """Monta o e-book como PDF (capa + uma pagina por trecho).

    Layout de cada pagina: ilustracao em cima, legenda (texto) embaixo, centralizada.
    Usa reportlab (puro Python, sem dependencias de sistema).
    """
    import io

    from reportlab.lib.pagesizes import A5
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    W, H = A5
    c = canvas.Canvas(buf, pagesize=A5)
    margin = 30

    def draw_wrapped(text: str, cx: float, top_y: float, max_w: float,
                     font: str, size: float, leading: float, color) -> None:
        c.setFillColorRGB(*color)
        c.setFont(font, size)
        y = top_y
        for line in simpleSplit(text or "", font, size, max_w):
            c.drawCentredString(cx, y, line)
            y -= leading

    # ---- capa ----
    c.setFillColorRGB(0.12, 0.16, 0.27)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    draw_wrapped(title, W / 2, H / 2 + 20, W - 2 * margin, "Helvetica-Bold", 22, 28, (1, 1, 1))
    c.setFillColorRGB(0.75, 0.8, 0.9)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(W / 2, 40, "Story R Us")
    c.showPage()

    # ---- paginas ----
    for i, p in enumerate(pages, 1):
        img = p.get("image")
        text_top = H - margin
        if img:
            try:
                ir = ImageReader(io.BytesIO(img))
                iw, ih = ir.getSize()
                max_w = W - 2 * margin
                max_h = H * 0.58
                scale = min(max_w / iw, max_h / ih)
                dw, dh = iw * scale, ih * scale
                x = (W - dw) / 2
                y = H - margin - dh
                c.drawImage(ir, x, y, dw, dh, preserveAspectRatio=True, mask=None)
                text_top = y - 24
            except Exception as exc:  # noqa: BLE001
                logger.warning("falha ao desenhar imagem da pagina %s: %s", i, exc)
        draw_wrapped(
            p.get("text", ""), W / 2, text_top, W - 2 * margin,
            "Helvetica", 13, 18, (0.16, 0.18, 0.28),
        )
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(W / 2, 18, str(i))
        c.showPage()

    c.save()
    return buf.getvalue()
