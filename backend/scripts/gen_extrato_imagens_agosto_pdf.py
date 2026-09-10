"""PDF tecnico: gasto real de imagens em agosto 2026 (Google AI Studio)."""
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
OUT = ROOT / "Extrato-imagens-agosto-2026.pdf"
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"
WIN = Path(r"C:\Windows\Fonts")

NAVY = colors.Color(0.106, 0.184, 0.373)
GOLD = colors.Color(0.956, 0.718, 0.251)
CREAM = colors.Color(1.0, 0.972, 0.936)
INK = colors.Color(0.18, 0.20, 0.24)
MUTED = colors.Color(0.38, 0.40, 0.45)
RULE = colors.Color(0.82, 0.84, 0.88)
ROW = colors.Color(0.97, 0.96, 0.94)

TOTAL_28D = 255.52
SEP1 = 8.393
AGOSTO_DIAS = round(TOTAL_28D - SEP1, 2)  # 247.13
JULHO = 95.23
SALDO = 2.43

MODELS = [
    ("Nano Banana Pro (Gemini 3 Pro Image)", 157.51, "Imagens 2K — avatares, páginas, refine"),
    ("Nano Banana (2.5 Flash Preview Image)", 72.73, "Imagem (lote anterior ao Pro)"),
    ("Gemini 3.5 Flash", 20.29, "Texto / juiz / prompts"),
    ("Nano Banana 2 (3.1 Flash Image)", 4.77, "Imagem Flash"),
    ("Gemini 3.1 Flash Lite", 0.21, "Juiz / recorte de rosto"),
    ("Gemini 3.6 Flash", 0.01, "Texto"),
]
IMAGE_MODELS = {0, 1, 3}  # índices de MODELS que são geração de imagem

DAYS = [
    ("8/08", 6.597),
    ("11/08", 19.949),
    ("13/08", 2.958),
    ("14/08", 6.19),
    ("15/08", 7.123),
    ("16/08", 0.457),
    ("18/08", 2.628),
    ("19/08", 10.745),
    ("20/08", 1.843),
    ("26/08", 19.85),
    ("27/08", 37.004),
    ("28/08", 10.982),
    ("29/08", 95.689),
    ("31/08", 25.109),
]


def _brl(n: float) -> str:
    return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(part: float, total: float) -> str:
    return f"{(part / total) * 100:.1f}%".replace(".", ",")


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
    img_total = sum(MODELS[i][1] for i in IMAGE_MODELS)

    story.append(Spacer(1, 28 * mm))
    if LOGO.exists():
        img = Image(str(LOGO), width=42 * mm, height=42 * mm)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 8 * mm))
    story.append(_p("EXTRATO TÉCNICO DE IMAGENS", styles["cover_kicker"]))
    story.append(_p("Gasto real de agosto 2026", styles["cover_title"]))
    story.append(_p(
        "Google AI Studio · projeto Gabriel<br/>"
        "5 ago – 1 set (28 dias, PDT) · lido em 1º de setembro de 2026<br/>"
        f"Total da janela: {_brl(TOTAL_28D)} · só agosto (8–31): {_brl(AGOSTO_DIAS)}",
        styles["cover_sub"],
    ))
    story.append(PageBreak())

    story.append(_p("O que este extrato é", styles["h1"]))
    story.append(_p(
        "Agosto já aconteceu. Não há “previsto de 32 livros”: o número oficial é o "
        "que a Google cobrou. O Studio <b>não nomeia</b> livro nem página — só modelo "
        "e dia. Cada linha abaixo é o faturamento real da aba Gasto.",
        styles["body"],
    ))
    story.append(_callout(
        "Totais",
        f"Janela 28 dias (5/08–1/09): <b>{_brl(TOTAL_28D)}</b>. "
        f"Dias de agosto com gasto (8–31/08): <b>{_brl(AGOSTO_DIAS)}</b>. "
        f"1/09 (já no extrato de setembro da janela antiga): {_brl(SEP1)}. "
        f"Só geração de imagem (3 modelos Banana): <b>{_brl(img_total)}</b> na janela de 28 dias.",
        styles, W,
    ))
    story.append(Spacer(1, 4 * mm))

    story.append(_p("Por modelo", styles["h2"]))
    model_rows = []
    for name, cost, role in MODELS:
        kind = "Imagem" if any(name == MODELS[i][0] for i in IMAGE_MODELS) else "Texto / juiz"
        model_rows.append([name, kind, role, _brl(cost), _pct(cost, TOTAL_28D)])
    model_rows.append(["Total 28 dias", "—", "—", _brl(TOTAL_28D), "100%"])
    story.append(_table(
        ["Modelo", "Tipo", "Papel", "Valor", "%"],
        model_rows,
        [52 * mm, 22 * mm, 48 * mm, 28 * mm, 25 * mm],
        styles,
    ))
    story.append(_p(
        f"Imagem (Banana Pro + Banana + Banana 2) = {_brl(img_total)}. "
        f"Texto/juiz (Flash + Flash Lite + 3.6) = {_brl(TOTAL_28D - img_total)}. "
        "Soma dos seis modelos fecha o total da aba Gasto.",
        styles["small"],
    ))

    story.append(_p("Cada dia com gasto (agosto)", styles["h1"]))
    story.append(_p(
        "Eixo à meia-noite PDT. Dias zerados no intervalo e omitidos da tabela: "
        "6–7, 9–10, 12, 17, 21–25 e 30/08. Pico em 29/08 (Amazônia / lote de páginas).",
        styles["body"],
    ))
    day_rows = [[d, _brl(v)] for d, v in DAYS]
    day_rows.append(["Soma 8–31/08", _brl(AGOSTO_DIAS)])
    day_rows.append(["1/09 (janela de 28 dias, já é setembro)", _brl(SEP1)])
    day_rows.append(["Total 28 dias", _brl(TOTAL_28D)])
    story.append(_table(
        ["Dia", "Custo"],
        day_rows,
        [120 * mm, 55 * mm],
        styles,
    ))

    story.append(_p("Conta", styles["h2"]))
    story.append(_table(
        ["Quando", "Tipo", "Valor"],
        [
            ["28/08/2026", "Recarga pré-paga", _brl(100)],
            ["1–31/07/2026", "Fatura julho", _brl(61.35)],
            ["Julho (90d − 28d, aba Gasto)", "Consumo estimado", _brl(JULHO)],
            ["Agora (lido 1/09)", "Saldo pré-pago", _brl(SALDO)],
        ],
        [70 * mm, 55 * mm, 50 * mm],
        styles,
    ))
    story.append(_p(
        "Billing 017752-126A71-615AEF · conta eng.andrevitor89@gmail.com · "
        "projeto Gabriel. Recarga automática desligada. O consumo de agosto saiu "
        "do crédito pré-pago. Fal, Claude, ElevenLabs e Kling: login — não lidos.",
        styles["small"],
    ))

    story.append(_p(
        "Documento interno. Números oficiais do AI Studio lidos em 1º de setembro "
        "de 2026. O Studio não entrega “página 3 do Matteo”. Jobs de agosto no "
        "/gastos aparecem como “sem extrato” — o ledger linha a linha só vale "
        "depois do deploy de setembro. Não substitui contrato.",
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
        canvas.drawString(18 * mm, h - 8 * mm, "STORY R US  ·  Extrato de imagens — agosto 2026")
        canvas.drawRightString(w - 18 * mm, h - 8 * mm, "1º de setembro de 2026")
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, 12 * mm, w, 1 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(font, 8)
        canvas.drawString(18 * mm, 5 * mm, "interno — gasto real do Studio, não previsto")
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
        title="Extrato de imagens — agosto 2026",
        author="Story R Us",
        subject="Gasto real de imagens no Google AI Studio — agosto 2026",
    )
    doc.build(story, onFirstPage=first_page, onLaterPages=later)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    print(f"{path.stat().st_size / 1024:.0f} KB")
