# -*- coding: utf-8 -*-
"""PDF tecnico: gasto real de 9/09/2026 (Google AI Studio + artefatos locais)."""
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
OUT = ROOT / "Extrato-hoje-2026-09-09.pdf"
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"
WIN = Path(r"C:\Windows\Fonts")

NAVY = colors.Color(0.106, 0.184, 0.373)
GOLD = colors.Color(0.956, 0.718, 0.251)
CREAM = colors.Color(1.0, 0.972, 0.936)
INK = colors.Color(0.18, 0.20, 0.24)
MUTED = colors.Color(0.38, 0.40, 0.45)
RULE = colors.Color(0.82, 0.84, 0.88)
ROW = colors.Color(0.97, 0.96, 0.94)

UNIT_GEMINI_USD = 0.039
UNIT_BRL = 0.69
BRL_PER_USD = UNIT_BRL / UNIT_GEMINI_USD
FAL_USD = 0.03
FAL_BRL = FAL_USD * BRL_PER_USD

# Lido no AI Studio (projeto Storyrus) em 9/09/2026 ~22:30 BRT.
STUDIO_MONTH_ALL = 28.44
STUDIO_MONTH_PRO = 28.05
STUDIO_SEP8_PRO = 3.378
STUDIO_SEP9_PRO = 24.673
STUDIO_SEP9_ALL = 24.695
STUDIO_SEP1 = 0.349

# 2 avatares + 4 pags manha + 5 Amazonia + 5 Reino-5 + 3 Reino-lock + 17 corpo.
GEMINI_CONFIRMED = 36
CODE_GEMINI_USD = GEMINI_CONFIRMED * UNIT_GEMINI_USD
CODE_GEMINI_BRL = GEMINI_CONFIRMED * UNIT_BRL
FAL_SWAPS = 33  # 3 paginas x 11 timeouts, 0 entrega
FAL_AVATAR = 2
FAL_SAM = 1
CODE_FAL_USD = (FAL_SWAPS + FAL_AVATAR + FAL_SAM) * FAL_USD
CODE_FAL_BRL = CODE_FAL_USD * BRL_PER_USD


def _brl(n: float) -> str:
    return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _usd(n: float) -> str:
    return f"US$ {n:.3f}".replace(".", ",")


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
    story.append(_p("O que foi gasto hoje", styles["cover_title"]))
    story.append(_p(
        "9 de setembro de 2026 · projeto Storyrus<br/>"
        f"Oficial no Studio até ~22h30 BRT: <b>{_brl(STUDIO_SEP9_PRO)}</b> "
        "(Nano Banana Pro)<br/>"
        "36 imagens Gemini confirmadas · Fal face-swap: 33 timeouts, 0 página",
        styles["cover_sub"],
    ))
    story.append(PageBreak())

    story.append(_p("O que este extrato é", styles["h1"]))
    story.append(_p(
        "Gasto de <b>hoje</b> (9/09, eixo PDT no Studio). Número oficial = aba Gasto "
        "do Google AI Studio, projeto <b>Storyrus</b> (gen-lang-client-0496805571), "
        "conta eng.andrevitor89@gmail.com, filtro <b>Este mês</b>. "
        "As linhas nomeadas vêm dos artefatos em <b>backend/scripts/out</b> e dos "
        "logs dos scripts. Fal.ai não foi lido (sem dashboard). "
        "Claude, Kling e ElevenLabs não rodaram.",
        styles["body"],
    ))
    story.append(_callout(
        "Oficial agora (Studio)",
        f"Barra de 9/09 (Nano Banana Pro): <b>{_brl(STUDIO_SEP9_PRO)}</b> — "
        f"mês Pro {_brl(STUDIO_MONTH_PRO)} menos o pico de 8/09 {_brl(STUDIO_SEP8_PRO)}. "
        f"Todos os modelos hoje: {_brl(STUDIO_SEP9_ALL)}. "
        f"Mês todos: {_brl(STUDIO_MONTH_ALL)}. "
        "O Studio avisa atraso de até 24 h.",
        styles, W,
    ))
    story.append(Spacer(1, 4 * mm))

    story.append(_p("A. Oficial — Google AI Studio", styles["h1"]))
    story.append(_p(
        f"Filtro Este mês (1–9/09 PDT). 3–7/09 zerados. "
        f"2/09 residual de setup ({_brl(STUDIO_SEP1)}, quase só Flash). "
        "Limite mensal experimental: R$ 123,66 (não é gasto).",
        styles["body"],
    ))
    story.append(_table(
        ["Quando (eixo PDT)", "Modelo", "Custo"],
        [
            ["1–2/09 (residual)", "misto / Flash", _brl(STUDIO_SEP1)],
            ["3–7/09", "—", _brl(0)],
            ["8/09", "Nano Banana Pro", _brl(STUDIO_SEP8_PRO)],
            ["9/09 — hoje · só Pro", "Nano Banana Pro", _brl(STUDIO_SEP9_PRO)],
            ["9/09 — hoje · todos", "todos", _brl(STUDIO_SEP9_ALL)],
            ["Total 1–9/09 · só Pro", "Nano Banana Pro", _brl(STUDIO_MONTH_PRO)],
            ["Total 1–9/09 · todos", "todos", _brl(STUDIO_MONTH_ALL)],
        ],
        [80 * mm, 48 * mm, 47 * mm],
        styles,
    ))
    story.append(_p(
        f"Outros modelos no mês (Flash Lite / recorte / juiz): "
        f"{_brl(STUDIO_MONTH_ALL - STUDIO_MONTH_PRO)}. "
        f"Desses, hoje: {_brl(STUDIO_SEP9_ALL - STUDIO_SEP9_PRO)}.",
        styles["small"],
    ))

    story.append(_p("B. O que rodou hoje (artefatos + logs)", styles["h1"]))
    story.append(_p(
        "Horários em America/Sao_Paulo. Páginas da manhã do Reino foram "
        "regeneradas à noite (contam as duas chamadas). Avatar do Reino "
        "às 12:58 e o character das 18:07 não entram na soma Gemini — "
        "cópia ou arquivo local. Amazônia: job matteo-5 abortado aos 67 s "
        "com P2/P3 já disparadas; as 5 páginas e o PDF saíram em seguida.",
        styles["body"],
    ))
    story.append(_table(
        ["Bloco", "Hora", "O quê", "Provedor", "N"],
        [
            [
                "Avatares",
                "11:39–12:20",
                "Nicolas + Matteo (recorte, geração, refine)",
                "Pro + Flash + Fal/Gemini",
                "2 Pro",
            ],
            [
                "Reino manhã",
                "14:10–14:13",
                "P2–P5 Matteo (1ª leva; depois sobrescrita)",
                "Nano Banana Pro",
                "4",
            ],
            [
                "Amazônia",
                "19:32–19:36",
                "P2–P6 Matteo + PDF",
                "Nano Banana Pro",
                "5",
            ],
            [
                "Reino noite",
                "19:33–19:38",
                "P2–P6 Matteo (reino-5)",
                "Nano Banana Pro",
                "5",
            ],
            [
                "Reino lock",
                "19:50–20:05",
                "P2, P3, P6 de novo (reino-lock)",
                "Nano Banana Pro",
                "3",
            ],
            [
                "SAM",
                "20:34",
                "Novo recorte Matteo (face_segment + SAM2)",
                "Fal SAM + Flash",
                "1 Fal",
            ],
            [
                "Corpo",
                "20:38–20:45",
                "Avatar placeholder + P2–P17 sem rosto",
                "Nano Banana Pro",
                "17",
            ],
            [
                "Rosto",
                "21:11–22:15",
                "Cola rosto nas chapas — 3 páginas × 11 timeouts",
                "Fal face-swap",
                "33 Fal",
            ],
        ],
        [28 * mm, 28 * mm, 62 * mm, 38 * mm, 19 * mm],
        styles,
    ))
    story.append(_p(
        "PDFs locais (sem API): Reino p1–p4 14:17 / 16:22 / 17:38; "
        "Amazônia 19:36; Reino p1–p6 20:05; corpo 20:45; rosto 22:15 "
        "(só dedicatória — 16 páginas faltando). "
        "Juiz InsightFace nas páginas do Reino: local, sem cobrança.",
        styles["small"],
    ))

    story.append(_p("C. Soma", styles["h1"]))
    story.append(_table(
        ["Bloco", "USD código", "BRL plano", "Studio (oficial)"],
        [
            [
                f"{GEMINI_CONFIRMED} imagens Gemini confirmadas",
                _usd(CODE_GEMINI_USD),
                _brl(CODE_GEMINI_BRL),
                f"{_brl(STUDIO_SEP9_PRO)} (Pro hoje)",
            ],
            [
                "Recortes Flash Lite",
                "~0,00",
                _brl(0),
                f"{_brl(STUDIO_SEP9_ALL - STUDIO_SEP9_PRO)} hoje",
            ],
            [
                f"2 refine de avatar (se Fal cobrou)",
                _usd(FAL_AVATAR * FAL_USD),
                _brl(FAL_AVATAR * FAL_BRL),
                "não entra no Studio",
            ],
            [
                "1 SAM2 (recorte 20:34)",
                _usd(FAL_SAM * FAL_USD),
                _brl(FAL_SAM * FAL_BRL),
                "não entra no Studio",
            ],
            [
                f"{FAL_SWAPS} face-swap timeout (teto)",
                _usd(FAL_SWAPS * FAL_USD),
                _brl(FAL_SWAPS * FAL_BRL),
                "Fal sem dashboard",
            ],
            [
                "Teto código Gemini + Fal",
                _usd(CODE_GEMINI_USD + CODE_FAL_USD),
                _brl(CODE_GEMINI_BRL + CODE_FAL_BRL),
                "só Gemini é oficial",
            ],
        ],
        [62 * mm, 35 * mm, 35 * mm, 43 * mm],
        styles,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_callout(
        "Como ler os dois números",
        f"O Studio cobra o preço real da Google em BRL — hoje <b>{_brl(STUDIO_SEP9_PRO)}</b> "
        f"no Pro. {GEMINI_CONFIRMED} gerações no código a {_usd(UNIT_GEMINI_USD)} "
        f"({_brl(UNIT_BRL)}) somam {_usd(CODE_GEMINI_USD)} / {_brl(CODE_GEMINI_BRL)}. "
        f"A diferença é {_brl(abs(CODE_GEMINI_BRL - STUDIO_SEP9_PRO))} — câmbio e arredondamento, "
        "não gerações faltando. O teto Fal (refine + SAM + 33 swaps) não está no Studio; "
        "os 33 timeouts podem ou não ter sido faturados.",
        styles, W,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_p(
        "Documento interno. Relido em 9 de setembro de 2026 ~22h30 BRT "
        "(atualiza o recorte das 15h). Não substitui fatura da Google nem contrato. "
        "/gastos da plataforma não foi consultado (scripts locais, sem job no banco). "
        "Fal.ai: sem dashboard nesta leitura.",
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
        canvas.drawString(18 * mm, h - 8 * mm, "STORY R US  ·  Extrato de hoje — 9 de setembro de 2026")
        canvas.drawRightString(w - 18 * mm, h - 8 * mm, "9 de setembro de 2026")
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, 12 * mm, w, 1 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(font, 8)
        canvas.drawString(18 * mm, 5 * mm, "interno — gasto real do Studio + artefatos do dia")
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
        title="Extrato de hoje — 9 de setembro de 2026",
        author="Story R Us",
        subject="Gasto real de 9/09 no Google AI Studio e nas gerações locais",
    )
    doc.build(story, onFirstPage=first_page, onLaterPages=later)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    print(f"{path.stat().st_size / 1024:.0f} KB")
