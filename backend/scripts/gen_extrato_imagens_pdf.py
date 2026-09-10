"""PDF tecnico: cada geracao de imagem prevista em setembro + gasto real do Studio."""
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
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Extrato-imagens-setembro-2026.pdf"
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"
WIN = Path(r"C:\Windows\Fonts")

NAVY = colors.Color(0.106, 0.184, 0.373)
GOLD = colors.Color(0.956, 0.718, 0.251)
CREAM = colors.Color(1.0, 0.972, 0.936)
INK = colors.Color(0.18, 0.20, 0.24)
MUTED = colors.Color(0.38, 0.40, 0.45)
RULE = colors.Color(0.82, 0.84, 0.88)
ROW = colors.Color(0.97, 0.96, 0.94)

UNIT_USD = 0.039
UNIT_BRL = 0.69  # 18 x 0,69 = 12,42 ≈ ticket publicado de R$ 12,50
BOOKS = 32
LINES = [
    "Avatar — geração",
    "Avatar — refine 1",
    "Avatar — refine 2",
    "Ficha — character sheet",
    "Ficha — expression sheet",
    "Ficha — costume lock",
    "Página 1 — geração",
    "Página 1 — refine (lock)",
    "Página 1 — retry",
    "Página 2 — geração",
    "Página 2 — refine (lock)",
    "Página 2 — retry",
    "Página 3 — geração",
    "Página 3 — refine (lock)",
    "Página 4 — geração",
    "Retrabalho — página 4 refine",
    "Retrabalho — página 3 retry extra",
    "Retrabalho — página 4 retry",
]


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
    s["body_left"] = ParagraphStyle(
        "body_left", parent=s["body"], alignment=TA_LEFT,
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
    story.append(_p("EXTRATO TÉCNICO DE IMAGENS", styles["cover_kicker"]))
    story.append(_p("Cada geração prevista<br/>em setembro 2026", styles["cover_title"]))
    story.append(_p(
        "A — 18 chamadas por livro × 32 livros<br/>"
        "B — já faturado no Google AI Studio (1–3/09)<br/>"
        "C — daqui pra frente cada linha sai em storyrus.ai/gastos",
        styles["cover_sub"],
    ))
    story.append(PageBreak())

    story.append(_p("A. Previsto — um livro (4 páginas)", styles["h1"]))
    story.append(_p(
        "Pipeline do gerador: avatar (geração + 2 refines), ficha (3 folhas) e páginas "
        "ilustradas com lock nas primeiras (geração + refine + retry). Texto sobre a arte "
        "não gera imagem. Juiz Flash Lite não entra nesta tabela (~R$ 2–4 no mês).",
        styles["body"],
    ))
    story.append(_callout(
        "Preço da linha",
        f"No código, Nano Banana Pro = <b>US$ {UNIT_USD:.3f}</b> por imagem. "
        "O ticket publicado do plano (~R$ 12,50/livro, ~R$ 400 no mês) reparte essas "
        f"18 linhas a <b>~R$ {UNIT_BRL:.2f}</b> cada, já com lock e retrabalho.",
        styles, W,
    ))
    story.append(Spacer(1, 4 * mm))

    line_rows = []
    for i, label in enumerate(LINES, 1):
        line_rows.append([
            str(i),
            label,
            f"US$ {UNIT_USD:.3f}",
            f"R$ {UNIT_BRL:.2f}".replace(".", ","),
        ])
    story.append(_table(
        ["#", "Chamada", "USD código", "BRL plano"],
        line_rows,
        [12 * mm, 85 * mm, 38 * mm, 40 * mm],
        styles,
    ))
    story.append(_p(
        f"Soma 1 livro: 18 × US$ {UNIT_USD:.3f} = US$ {18 * UNIT_USD:.3f} · "
        "ticket publicado ~R$ 12,50.",
        styles["small"],
    ))

    story.append(_p("A. Previsto — mês cheio (32 livros)", styles["h2"]))
    story.append(_table(
        ["Bloco", "Linhas / livro", "× 32 livros", "BRL plano"],
        [
            ["Avatar (geração + 2 refine)", "3", "96", "~R$ 66"],
            ["Ficha (3 folhas)", "3", "96", "~R$ 66"],
            ["Páginas + lock + retrabalho", "12", "384", "~R$ 268"],
            ["Total desenho", "18", "576", "~R$ 400"],
            ["Ferramenta Cursor (fixa)", "—", "—", "~R$ 100"],
            ["Total previsto no mês", "—", "—", "~R$ 500"],
        ],
        [70 * mm, 35 * mm, 35 * mm, 35 * mm],
        styles,
    ))
    story.append(_p(
        "Sem texto ok no dia anterior: 0 livros naquele dia. 10 livros ≈ R$ 125 de desenho, "
        "não R$ 400. Vídeo e impresso automático não entram.",
        styles["small"],
    ))

    story.append(_p("B. Já faturado — Google AI Studio", styles["h1"]))
    story.append(_p(
        "Lido em 3 de setembro de 2026. Projeto <b>Storyrus</b> "
        "(gen-lang-client-0496805571), conta eng.andrevitor89@gmail.com, "
        "filtro <b>Este mês</b> (1–3/09, PDT).",
        styles["body"],
    ))
    story.append(_callout(
        "Setembro até agora",
        "Custo total do mês no Studio: <b>R$ 0,35</b>. O Studio não nomeia livro nem página — "
        "só dia e modelo. A produção 2/dia só começa em 9/09; este valor é setup/teste, "
        "não os 32 livros.",
        styles, W,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_table(
        ["Dia (eixo do gráfico, PDT)", "Custo"],
        [
            ["2 de set., 00:00", "R$ 0,349"],
            ["3 de set., 00:00", "R$ 0,00"],
            ["4 de set., 00:00", "R$ 0,00"],
            ["Total 1–3/09", "R$ 0,35"],
        ],
        [120 * mm, 55 * mm],
        styles,
    ))
    story.append(_p(
        "Fal.ai / PuLID: dashboard pediu login — não lido. Claude e ElevenLabs não entram "
        "neste extrato de imagem.",
        styles["small"],
    ))

    story.append(_p("C. Extrato ao vivo", styles["h1"]))
    story.append(_p(
        "A partir deste deploy, cada generate/refine/retry/ficha grava uma linha em "
        "<b>usage_events</b> e aparece em <b>https://storyrus.ai/gastos</b> (senha). "
        "Jobs antigos continuam como “job sem extrato”.",
        styles["body"],
    ))
    items = [
        ListItem(_p(b, styles["body_left"]), leftIndent=8, value="•")
        for b in [
            "Avatar: geração + refine 1 + refine 2.",
            "Ficha: character sheet, expression sheet, costume lock.",
            "Cada página ilustrada: geração, refine se o juiz recusar, retry se ainda falhar.",
            "PuLID/Fal, quando ligado, entra com o preço da linha Fal.",
        ]
    ]
    story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=12, spaceAfter=10))
    story.append(_p(
        "Documento interno. Conferido em 3 de setembro de 2026. Não substitui o PDF enxuto "
        "da cliente (~R$ 500) nem contrato.",
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
        canvas.drawString(18 * mm, h - 8 * mm, "STORY R US  ·  Extrato de imagens — setembro 2026")
        canvas.drawRightString(w - 18 * mm, h - 8 * mm, "3 de setembro de 2026")
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
        title="Extrato de imagens — setembro 2026",
        author="Story R Us",
        subject="Cada geração de imagem prevista e já faturada",
    )
    doc.build(story, onFirstPage=first_page, onLaterPages=later)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    print(f"{path.stat().st_size / 1024:.0f} KB")
