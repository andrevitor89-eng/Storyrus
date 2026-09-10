# -*- coding: utf-8 -*-
"""PDF tecnico: gasto do catalogo mergulho_mar + avatar Fal do Nicolas (8/09)."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Extrato-nicolas-mergulho-2026-09-08.pdf"
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"
WIN = Path(r"C:\Windows\Fonts")

NAVY = colors.Color(0.106, 0.184, 0.373)
GOLD = colors.Color(0.956, 0.718, 0.251)
CREAM = colors.Color(1.0, 0.972, 0.936)
INK = colors.Color(0.18, 0.20, 0.24)
MUTED = colors.Color(0.38, 0.40, 0.45)
RULE = colors.Color(0.82, 0.84, 0.88)
ROW = colors.Color(0.97, 0.96, 0.94)

# Mesmo câmbio do extrato de setembro: US$ 0,039 = R$ 0,69.
UNIT_GEMINI_USD = 0.039
UNIT_BRL = 0.69
BRL_PER_USD = UNIT_BRL / UNIT_GEMINI_USD
FAL_USD = 0.03
FAL_BRL = FAL_USD * BRL_PER_USD
CONFIRMED_USD = FAL_USD
CONFIRMED_BRL = FAL_BRL


def _brl(n: float) -> str:
    return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _usd(n: float) -> str:
    return f"US$ {n:.2f}".replace(".", ",")


def _register_fonts() -> tuple[str, str, str]:
    regular = WIN / "arial.ttf"
    bold = WIN / "arialbd.ttf"
    italic = WIN / "ariali.ttf"
    if regular.exists():
        pdfmetrics.registerFont(TTFont("Body", str(regular)))
        pdfmetrics.registerFont(TTFont("Body-Bold", str(bold if bold.exists() else regular)))
        pdfmetrics.registerFont(TTFont("Body-Italic", str(italic if italic.exists() else regular)))
        return "Body", "Body-Bold", "Body-Italic"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


def _styles(face: str, bold: str, italic: str) -> dict:
    base = getSampleStyleSheet()
    s = {}
    s["cover_kicker"] = ParagraphStyle(
        "cover_kicker", parent=base["Normal"], fontName=bold, fontSize=9,
        textColor=GOLD, alignment=TA_CENTER, spaceAfter=8,
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title", parent=base["Normal"], fontName=bold, fontSize=24,
        textColor=colors.white, leading=30, alignment=TA_CENTER, spaceAfter=10,
    )
    s["cover_sub"] = ParagraphStyle(
        "cover_sub", parent=base["Normal"], fontName=face, fontSize=11,
        textColor=colors.Color(0.85, 0.88, 0.93), leading=16, alignment=TA_CENTER,
    )
    s["h1"] = ParagraphStyle(
        "h1", parent=base["Normal"], fontName=bold, fontSize=16,
        textColor=NAVY, leading=20, spaceBefore=4, spaceAfter=10,
    )
    s["h2"] = ParagraphStyle(
        "h2", parent=base["Normal"], fontName=bold, fontSize=12.5,
        textColor=NAVY, leading=16, spaceBefore=14, spaceAfter=6,
    )
    s["body"] = ParagraphStyle(
        "body", parent=base["Normal"], fontName=face, fontSize=10,
        textColor=INK, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=8,
    )
    s["small"] = ParagraphStyle(
        "small", parent=base["Normal"], fontName=face, fontSize=8.5,
        textColor=MUTED, leading=12, alignment=TA_LEFT, spaceAfter=4,
    )
    s["th"] = ParagraphStyle(
        "th", parent=base["Normal"], fontName=bold, fontSize=8,
        textColor=colors.white, leading=11,
    )
    s["td"] = ParagraphStyle(
        "td", parent=base["Normal"], fontName=face, fontSize=8,
        textColor=INK, leading=11,
    )
    s["td_b"] = ParagraphStyle(
        "td_b", parent=s["td"], fontName=bold,
    )
    s["callout"] = ParagraphStyle(
        "callout", parent=base["Normal"], fontName=face, fontSize=10,
        textColor=NAVY, leading=14.5, alignment=TA_JUSTIFY,
    )
    s["callout_t"] = ParagraphStyle(
        "callout_t", parent=base["Normal"], fontName=bold, fontSize=10,
        textColor=NAVY, leading=13, spaceAfter=4,
    )
    return s


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def _table(headers: list[str], rows: list[list[str]], col_widths: list, styles: dict) -> Table:
    head = [_p(h, styles["th"]) for h in headers]
    body = []
    for row in rows:
        cells = []
        for j, cell in enumerate(row):
            st = styles["td_b"] if j == 0 else styles["td"]
            cells.append(_p(cell, st))
        body.append(cells)
    data = [head] + body
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ROW))
    t.setStyle(TableStyle(cmds))
    return t


def _callout(title: str, body: str, styles: dict, width: float) -> Table:
    inner = [[_p(title, styles["callout_t"])], [_p(body, styles["callout"])]]
    box = Table(inner, colWidths=[width])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 1.2, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (0, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return box


def build() -> Path:
    face, bold, italic = _register_fonts()
    styles = _styles(face, bold, italic)
    W = A4[0] - 36 * mm
    story = []

    story.append(Spacer(1, 28 * mm))
    if LOGO.exists():
        img = Image(str(LOGO), width=42 * mm, height=42 * mm)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 8 * mm))
    story.append(_p("EXTRATO TÉCNICO DE GASTO", styles["cover_kicker"]))
    story.append(_p("Nicolas / mergulho", styles["cover_title"]))
    story.append(_p(
        "Catálogo <b>mergulho_mar</b> + avatar Fal do Nicolas<br/>"
        "8 de setembro de 2026 · identity lock no Fal (PuLID)<br/>"
        f"Confirmado agora: {_usd(CONFIRMED_USD)} · {_brl(CONFIRMED_BRL)}",
        styles["cover_sub"],
    ))
    story.append(PageBreak())

    story.append(_p("O que este extrato é", styles["h1"]))
    story.append(_p(
        "Lote pontual de 8/09 — não é o extrato mensal de setembro (previsão de 32 livros). "
        "Números = preço no código (<b>price_fal_image_usd = 0,03</b>) mais o que esta sessão "
        "gerou. O dashboard Fal não foi lido. Câmbio igual ao extrato de setembro: "
        f"US$ {UNIT_GEMINI_USD:.3f} = {_brl(UNIT_BRL)} (~{_brl(BRL_PER_USD)} / USD).",
        styles["body"],
    ))

    story.append(_p("A. Catálogo mergulho_mar", styles["h1"]))
    story.append(_p(
        "História cadastrada no JSON do catálogo (17 páginas, figurino de mergulhador, "
        "testes). Nenhuma chamada de imagem. Claude não rodou.",
        styles["body"],
    ))
    story.append(_table(
        ["Item", "Provedor", "Status", "USD", "BRL"],
        [
            [
                "Template JSON + prompts + testes",
                "—",
                "concluído (código)",
                _usd(0),
                _brl(0),
            ],
        ],
        [52 * mm, 32 * mm, 38 * mm, 26 * mm, 27 * mm],
        styles,
    ))

    story.append(_p("B. Avatar Nicolas (8/09)", styles["h1"]))
    story.append(_p(
        "Foto em CRIANÇAS APROVADAS/NICOLAS.png. "
        "<b>IDENTITY_HEAD_PROVIDER=pulid</b>. Recorte do rosto no Gemini; geração e refine no Fal. "
        "Páginas do livro não foram ilustradas.",
        styles["body"],
    ))
    story.append(_table(
        ["#", "Chamada", "Provedor", "Status", "USD"],
        [
            [
                "1",
                "Recorte do rosto",
                "Gemini 3.1 Flash Lite",
                "concluído (retries de TLS)",
                "~0,00",
            ],
            [
                "2",
                "Avatar — geração",
                "Fal PuLID fal-ai/flux-pulid",
                "concluído (character-raw.png)",
                _usd(FAL_USD),
            ],
            [
                "3",
                "Avatar — refine 1",
                "Fal easel-ai/advanced-face-swap",
                "fila pos. 341 — não completou",
                "em aberto",
            ],
            [
                "4",
                "Avatar — refine 2",
                "Fal face-swap",
                "não rodou",
                _usd(0),
            ],
            [
                "5",
                "Páginas do livro (16 artes)",
                "—",
                "fora de escopo",
                _usd(0),
            ],
        ],
        [12 * mm, 42 * mm, 48 * mm, 46 * mm, 27 * mm],
        styles,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_callout(
        "Confirmado agora",
        f"<b>{_usd(CONFIRMED_USD)}</b> · <b>{_brl(CONFIRMED_BRL)}</b> — só a geração PuLID. "
        "O refine não entrou no character.png: a fila do face-swap ficou parada na posição 341. "
        f"Se o Fal cobrar esse pedido ao completar, +{_usd(FAL_USD)}. "
        "Houve um POST fal.run com timeout (~4 min); não entra como linha faturada.",
        styles,
        W,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_table(
        ["Bloco", "USD", "BRL"],
        [
            ["Catálogo (código)", _usd(0), _brl(0)],
            ["Avatar PuLID (confirmado)", _usd(CONFIRMED_USD), _brl(CONFIRMED_BRL)],
            ["Refine 1 se o Fal completar", _usd(FAL_USD), _brl(FAL_BRL)],
            ["Total confirmado agora", _usd(CONFIRMED_USD), _brl(CONFIRMED_BRL)],
            ["Teto se o refine 1 faturar", _usd(CONFIRMED_USD + FAL_USD), _brl(CONFIRMED_BRL + FAL_BRL)],
        ],
        [95 * mm, 40 * mm, 40 * mm],
        styles,
    ))
    story.append(_p(
        "Artefatos: backend/scripts/out/avatar/aprovados/nicolas/ "
        "(face-crop.jpg, character-raw.png, character.png, comparacao.png) e "
        "CRIANÇAS APROVADAS/avatar-nicolas.png. O character.png publicado é o PuLID, sem os 2 face-swaps.",
        styles["small"],
    ))
    story.append(_p(
        "Documento interno. Conferido em 9 de setembro de 2026. Não substitui o extrato mensal "
        "nem contrato. Claude, Kling e ElevenLabs não entram.",
        styles["small"],
    ))

    def later(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 12 * mm, w, 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, h - 12.8 * mm, w, 1.2 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        font_b = "Body-Bold" if "Body-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
        font = "Body" if "Body" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
        canvas.setFont(font_b, 8)
        canvas.drawString(18 * mm, h - 8 * mm, "STORY R US  ·  Extrato Nicolas / mergulho")
        canvas.drawRightString(w - 18 * mm, h - 8 * mm, "8 de setembro de 2026")
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, 12 * mm, w, 1 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(font, 8)
        canvas.drawString(18 * mm, 5 * mm, "interno — não é o PDF da cliente")
        canvas.drawRightString(w - 18 * mm, 5 * mm, f"{doc.page}")
        canvas.restoreState()

    def first_page(canvas, doc):
        w, h = A4
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, h, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, h - 6 * mm, w, 6 * mm, fill=1, stroke=0)
        canvas.rect(0, 0, w, 6 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.Color(0.85, 0.88, 0.93))
        canvas.setFont(face, 8)
        canvas.drawCentredString(w / 2, 8 * mm, "storyrus.ai")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="Extrato técnico — Nicolas / mergulho — 8 de setembro de 2026",
        author="Story R Us",
        subject="Gasto do catálogo mergulho_mar e do avatar Fal do Nicolas",
    )
    doc.build(story, onFirstPage=first_page, onLaterPages=later)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    print(f"{path.stat().st_size / 1024:.0f} KB")
