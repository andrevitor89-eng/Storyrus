"""Gera o plano de producao (setembro + manutencao) em PT-BR e EN."""
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
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"
WIN = Path(r"C:\Windows\Fonts")

NAVY = colors.Color(0.106, 0.184, 0.373)
GOLD = colors.Color(0.956, 0.718, 0.251)
CREAM = colors.Color(1.0, 0.972, 0.936)
INK = colors.Color(0.18, 0.20, 0.24)
MUTED = colors.Color(0.38, 0.40, 0.45)
RULE = colors.Color(0.82, 0.84, 0.88)
ROW = colors.Color(0.97, 0.96, 0.94)

COPY = {
    "pt": {
        "out": ROOT / "Plano-producao-Story-R-Us-setembro-2026-pt.pdf",
        "lang": "Português (Brasil)",
        "header": "STORY R US  ·  Plano de produção",
        "date": "2 de setembro de 2026",
        "footer_l": "storyrus.ai  ·  confidencial — uso da cliente",
        "cover_kicker": "PLANO DE PRODUÇÃO",
        "cover_title": "Setembro 2026<br/>e o que vem depois",
        "cover_sub": (
            "Dois livros novos por dia em setembro, no mínimo 4 páginas cada<br/>"
            "A partir de outubro: manutenção de storyrus.ai<br/><br/>"
            "Piso de 4 páginas · identity lock · texto aprovado no dia anterior<br/>"
            "Gasto previsto no mês: ~R$ 500"
        ),
        "title_doc": "Plano de produção — Story R Us — setembro 2026",
        "h_pronto": "Quando uma entrega conta",
        "pronto_t": "Regra única",
        "pronto_b": (
            "Está em <b>storyrus.ai</b> (não em preview nem storyrus2), o rosto "
            "passa no teste da família (lock no gerador), o livro novo tem no "
            "mínimo <b>4 páginas</b>, e o texto teve ok no dia anterior. Sem "
            "texto aprovado, o dia gera <b>0</b> — não dois livros inventados. "
            "Se o lock falhar em 3 páginas seguidas, o dia para."
        ),
        "stats": [
            ("2/dia", "Previsto 9–30/09\n(≥ 4 págs cada)"),
            ("~R$ 500", "Total previsto\nno mês"),
            ("2–8/09", "Setup: site\ne lock"),
            ("1/10+", "Previsto:\nmanutenção"),
        ],
        "h_blocos": "Três blocos",
        "blocos_intro": (
            "2 a 8 de setembro desbloqueia. 9 a 30 é dois livros novos por dia "
            "útil, com piso de 4 páginas e texto ok. A partir de 1º de outubro "
            "o previsto é manutenção do site — não dois livros por dia no "
            "automático. Cores e Pomar só entram na cota se forem o livro "
            "novo do dia."
        ),
        "th_bloco": ["Bloco", "Datas", "Previsto", "Condição"],
        "rows_bloco": [
            [
                "Setup",
                "2–8/09",
                "Site no critério combinado, lock publicado, margens, sem “antes e depois”",
                "Sexta 5: link do site. Texto do par do dia 9 precisa de ok até o dia 8",
            ],
            [
                "Produção 2/dia",
                "9–30/09",
                "Dois livros novos, no mínimo 4 páginas cada, por dia útil, enquanto houver texto ok",
                "Texto aprovado no dia anterior. Sem ok: zero livros naquele dia",
            ],
            [
                "Manutenção",
                "1/10 em diante",
                "Manter storyrus.ai: margens, “antes e depois”, português, login; lock ligado; pedidos no WhatsApp no dia ou no dia seguinte",
                "Livro novo só com texto novo. Publicar só em storyrus.ai",
            ],
        ],
        "h_fila": "Fila dos primeiros dias (alvo 9/09)",
        "th_fila": ["Dia", "Par (2 livros novos)", "Páginas previstas"],
        "rows_fila": [
            ["9/09", "Dois livros novos do catálogo educativo", "4 + 4"],
            ["10/09", "Próximo par com texto ok", "4 + 4"],
            ["11/09 em diante", "Próximo par do catálogo educativo", "4 + 4, só com texto ok"],
        ],
        "h_setup": "Setup — 2 a 8 de setembro",
        "setup_intro": (
            "Sem o lock no ar, a produção nasce com o bug antigo. Publicação "
            "em storyrus.ai."
        ),
        "setup_items": [
            "Margens da home: textos centralizados com alinhamento lateral.",
            "Confirmar no ar que a galeria “antes e depois” não aparece.",
            "Identity lock publicado no gerador.",
            "Texto do par do dia 9 precisa de ok até o dia 8.",
        ],
        "h_estoque": "O que já existe — não recomeçar",
        "th_estoque": ["Peça", "Hoje", "Falta"],
        "rows_estoque": [
            ["Site e estúdio", "No ar em storyrus.ai", "Margens, conferir “antes e depois”"],
            ["Identity lock", "Código local (refine + juiz)", "Publicar no gerador"],
            ["Cores Matteo", "Páginas 1–5 prontas", "Entra na cota só se for livro novo do dia (≥ 4 págs)"],
            ["Pomar Matteo", "Páginas 1–4 prontas", "Entra na cota só se for livro novo do dia (≥ 4 págs)"],
            ["Números e Grande/Pequeno", "Textos já enviados", "Entram como par do dia se tiverem ok; piso 4 págs"],
        ],
        "h_out": "Outubro em diante — manutenção primeiro",
        "out_intro": (
            "Fila contínua, não sprint de livro. Se o lock quebrar, para o "
            "livro e conserta. Livro novo só se vier texto novo."
        ),
        "out_items": [
            "Site certo no ar: regressão de margens, “antes e depois”, português, login.",
            "Identity lock ligado. Se quebrar, para livro e conserta.",
            "Pedidos novos no WhatsApp sobre o site, no dia ou no dia seguinte.",
            "Publicar só em storyrus.ai, não em preview nem storyrus2.",
        ],
        "h_assume": "Previsto e não previsto",
        "th_assume": ["Previsto", "Não previsto"],
        "rows_assume": [
            [
                "Setembro: site do setup em storyrus.ai; lock até 8/09; 2 livros novos/dia de 9 a 30/09 com piso de 4 páginas e texto ok; gasto no mês ~R$ 500. Outubro: manutenção do site; livro novo só com texto novo.",
                "2 livros/dia sem texto aprovado (aquele dia é zero). Outubro não carrega a meta de 2/dia. Vídeo narrado estável. Livro impresso automático. Site “100%” como nota. Instagram como prioridade. Catálogo inteiro sem texto.",
            ],
        ],
        "h_gastos": "Gastos previstos — setembro",
        "gastos_intro": (
            "Até 32 livros no mês (2 por dia útil, no mínimo 4 páginas cada). "
            "Se faltar texto aprovado, faz menos livros e gasta menos."
        ),
        "total_t": "Total previsto no mês",
        "total_b": (
            "Desenhar os livros (~R$ 400) + ferramenta de trabalho (~R$ 100). "
            "Fecha em <b>~R$ 500</b>. Vídeo e livro impresso automático não "
            "entram nesse número."
        ),
        "th_fecha": ["O que", "Previsto"],
        "rows_fecha": [
            ["Desenhar os livros (IA)", "~R$ 400"],
            ["Ferramenta de trabalho (Cursor)", "~R$ 100"],
            ["Total previsto", "~R$ 500"],
        ],
        "h_desenho": "Como o dinheiro sai — desenhar os livros",
        "desenho_b": (
            "Você aprova o texto no dia anterior. Sem esse ok, aquele dia "
            "não gera livro e não gasta desenho. Com o texto ok, um programa "
            "de inteligência artificial desenha cada página com o rosto da "
            "criança. Não é um desenho só por página: as primeiras páginas "
            "quase sempre precisam de uma segunda tentativa, para o rosto "
            "ficar parecido. Essa repetição já está dentro dos R$ 400 — não "
            "é um extra escondido. Colocar o texto em cima da arte (título e "
            "estrofe) não cobra de novo. O que pesa é só o desenho."
        ),
        "th_escala": ["Escala", "Desenho previsto"],
        "rows_escala": [
            ["Um livro (4 páginas)", "~R$ 12,50"],
            ["Um dia (2 livros)", "~R$ 25"],
            ["O mês cheio (32 livros)", "~R$ 400"],
        ],
        "escala_note": (
            "Conta redonda: 32 livros × ~R$ 12,50 = ~R$ 400. Se o mês tiver "
            "10 livros, o desenho fica perto de R$ 125, não de R$ 400."
        ),
        "h_ferramenta": "Como o dinheiro sai — ferramenta de trabalho",
        "ferramenta_b": (
            "O Cursor é o programa usado para montar e consertar o site "
            "(storyrus.ai) e o gerador dos livros: margens, login, o teste "
            "do rosto, bugs que aparecem no meio do mês. É uma mensalidade "
            "fixa, uns R$ 100 — como uma assinatura de trabalho. Vale para "
            "o mês inteiro: a semana de acerto do site (2–8/09) e os dias "
            "de livro (9–30/09). Não cai se saírem 2 livros em vez de 32. "
            "Uso extra além dessa assinatura não está previsto nos 500."
        ),
        "h_conta": "A conta do mês, junta",
        "th_conta": ["Parte", "Por livro", "Por dia (2 livros)", "Mês"],
        "rows_conta": [
            ["Desenhar os livros", "~R$ 12,50", "~R$ 25", "~R$ 400"],
            ["Ferramenta (fixa)", "—", "—", "~R$ 100"],
            ["Total previsto", "—", "—", "~R$ 500"],
        ],
        "gastos_note": (
            "Vídeo narrado e livro impresso automático não entram nesses 500. "
            "Se um dia ligar vídeo, isso é outro gasto, fora dos 500. Se o "
            "mês tiver menos livros, só o desenho cai; a ferramenta de R$ 100 "
            "continua."
        ),
        "h_msg": "Recado objetivo",
        "quote": (
            "Setembro: até dia 8, previsto site certo e lock no ar. A partir "
            "do dia 9, previsto 2 livros novos por dia, no mínimo 4 páginas "
            "cada. Texto novo precisa de ok no dia anterior. Gasto previsto "
            "no mês: uns 500 reais (IA + ferramentas). Outubro em diante o "
            "previsto é manutenção do site. Livro novo só com texto novo. "
            "Vídeo e livro impresso automático não estão previstos."
        ),
        "check_title": "Como acompanhar",
        "check_items": [
            "Sexta 5/09: link do site certo.",
            "Sextas de setembro: quantos livros fecharam na semana (previsto 2/dia útil, ≥ 4 págs).",
            "Sextas de outubro: o que foi consertado no site, não cota de livro.",
        ],
        "fine": (
            "Plano interno e para a cliente. Conferido em 2 de setembro de 2026. "
            "Não substitui contrato nem proposta comercial."
        ),
        "cover_foot": "storyrus.ai",
    },
    "en": {
        "out": ROOT / "Production-plan-Story-R-Us-september-2026-en.pdf",
        "lang": "English",
        "header": "STORY R US  ·  Production plan",
        "date": "2 September 2026",
        "footer_l": "storyrus.ai  ·  confidential — client use",
        "cover_kicker": "PRODUCTION PLAN",
        "cover_title": "September 2026<br/>and what follows",
        "cover_sub": (
            "Two new books a day in September, at least 4 pages each<br/>"
            "From October: maintenance of storyrus.ai<br/><br/>"
            "4-page floor · identity lock · copy approved the day before<br/>"
            "Planned spend for the month: ~R$ 500"
        ),
        "title_doc": "Production plan — Story R Us — September 2026",
        "h_pronto": "When a delivery counts",
        "pronto_t": "One rule",
        "pronto_b": (
            "It is live on <b>storyrus.ai</b> (not a preview, not storyrus2), "
            "the face passes a family test (lock on the generator), the new "
            "book has at least <b>4 pages</b>, and the copy was approved the "
            "day before. With no approved copy, that day ships <b>0</b> — "
            "not two invented books. If the lock fails on 3 pages in a row, "
            "the day stops."
        ),
        "stats": [
            ("2/day", "Planned 9–30 Sep\n(≥ 4 pages each)"),
            ("~R$ 500", "Planned total\nfor the month"),
            ("2–8 Sep", "Setup: site\nand lock"),
            ("1 Oct+", "Planned:\nmaintenance"),
        ],
        "h_blocos": "Three blocks",
        "blocos_intro": (
            "2–8 September unlocks the month. 9–30 is two new books per "
            "working day, with a 4-page floor and approved copy. From 1 "
            "October the planned work is site maintenance — not two books a "
            "day on autopilot. Colors and Orchard enter the quota only if "
            "they are that day’s new book."
        ),
        "th_bloco": ["Block", "Dates", "Planned", "Gate"],
        "rows_bloco": [
            [
                "Setup",
                "2–8 Sep",
                "Site to the agreed bar, lock published, margins, no before/after",
                "Friday 5: site link. Copy for the 9 Sep pair needs OK by the 8th",
            ],
            [
                "2/day production",
                "9–30 Sep",
                "Two new books, at least 4 pages each, per working day, while copy is OK",
                "Copy approved the day before. No OK: zero books that day",
            ],
            [
                "Maintenance",
                "1 Oct onward",
                "Keep storyrus.ai healthy: margins, before/after, Portuguese, login; lock on; WhatsApp site tickets same day or next",
                "A new book only with new copy. Ship only to storyrus.ai",
            ],
        ],
        "h_fila": "Queue for the first production days (target 9 Sep)",
        "th_fila": ["Day", "Pair (2 new books)", "Planned pages"],
        "rows_fila": [
            ["9 Sep", "Two new books from the educational catalog", "4 + 4"],
            ["10 Sep", "Next pair with approved copy", "4 + 4"],
            ["11 Sep onward", "Next pair from the educational catalog", "4 + 4, only with approved copy"],
        ],
        "h_setup": "Setup — 2 to 8 September",
        "setup_intro": (
            "Without the lock live, production ships the old bug. Ship to "
            "storyrus.ai."
        ),
        "setup_items": [
            "Home margins: centered copy with aligned side edges.",
            "Confirm live that the before/after gallery is gone.",
            "Identity lock published on the generator.",
            "Copy for the 9 Sep pair needs OK by the 8th.",
        ],
        "h_estoque": "What already exists — do not start over",
        "th_estoque": ["Piece", "Today", "Still open"],
        "rows_estoque": [
            ["Site and studio", "Live at storyrus.ai", "Margins, confirm before/after is gone"],
            ["Identity lock", "Local code (refine + judge)", "Publish on the generator"],
            ["Colors Matteo", "Pages 1–5 done", "Enters the quota only if it is that day’s new book (≥ 4 pages)"],
            ["Orchard Matteo", "Pages 1–4 done", "Enters the quota only if it is that day’s new book (≥ 4 pages)"],
            ["Numbers and Big/Small", "Copy already sent", "Enter as that day’s pair if OK; 4-page floor"],
        ],
        "h_out": "October onward — maintenance first",
        "out_intro": (
            "A standing queue, not a book sprint. If the lock breaks, stop "
            "the book and fix it. A new book only if new copy arrives."
        ),
        "out_items": [
            "Keep the right site live: regressions on margins, before/after, Portuguese, login.",
            "Identity lock on. If it breaks, stop books and fix it.",
            "New WhatsApp site requests, same day or next.",
            "Ship only to storyrus.ai, not a preview or storyrus2.",
        ],
        "h_assume": "Planned and not planned",
        "th_assume": ["Planned", "Not planned"],
        "rows_assume": [
            [
                "September: setup site on storyrus.ai; lock by 8 Sep; 2 new books/day from 9–30 Sep with a 4-page floor and approved copy; month spend ~R$ 500. October: site maintenance; a new book only with new copy.",
                "2 books/day with no approved copy (that day is zero). October does not carry the 2/day goal. Stable narrated video. Automatic print shipping. A “100% site” score. Instagram as P0. The full catalog with no copy.",
            ],
        ],
        "h_gastos": "Planned spend — September",
        "gastos_intro": (
            "Up to 32 books in the month (2 per working day, at least 4 pages "
            "each). If approved copy is missing, fewer books ship and spend "
            "drops."
        ),
        "total_t": "Planned total for the month",
        "total_b": (
            "Drawing the books (~R$ 400) + the work tool (~R$ 100). Closes at "
            "<b>~R$ 500</b>. Video and automatic print are not in this number."
        ),
        "th_fecha": ["What", "Planned"],
        "rows_fecha": [
            ["Drawing the books (AI)", "~R$ 400"],
            ["Work tool (Cursor)", "~R$ 100"],
            ["Planned total", "~R$ 500"],
        ],
        "h_desenho": "How the money is spent — drawing the books",
        "desenho_b": (
            "You approve the copy the day before. With no OK, that day makes "
            "no book and spends nothing on drawings. With approved copy, an "
            "artificial-intelligence program draws each page with the child’s "
            "face. It is not one drawing per page: the first pages almost "
            "always need a second try, so the face looks like the child. "
            "Those repeats are already inside the R$ 400 — not a hidden extra. "
            "Putting the words on the art (title and verse) does not charge "
            "again. The cost is the drawing."
        ),
        "th_escala": ["Scale", "Planned drawing spend"],
        "rows_escala": [
            ["One book (4 pages)", "~R$ 12.50"],
            ["One day (2 books)", "~R$ 25"],
            ["A full month (32 books)", "~R$ 400"],
        ],
        "escala_note": (
            "Round numbers: 32 books × ~R$ 12.50 = ~R$ 400. If the month has "
            "10 books, drawing spend is about R$ 125, not R$ 400."
        ),
        "h_ferramenta": "How the money is spent — the work tool",
        "ferramenta_b": (
            "Cursor is the program used to build and fix the site "
            "(storyrus.ai) and the book generator: margins, login, the face "
            "check, bugs that show up mid-month. It is a fixed monthly fee, "
            "about R$ 100 — like a work subscription. It covers the whole "
            "month: the site-setup week (2–8 Sep) and the book days "
            "(9–30 Sep). It does not drop if 2 books go out instead of 32. "
            "Extra use beyond this subscription is not planned inside the 500."
        ),
        "h_conta": "The month added up",
        "th_conta": ["Part", "Per book", "Per day (2 books)", "Month"],
        "rows_conta": [
            ["Drawing the books", "~R$ 12.50", "~R$ 25", "~R$ 400"],
            ["Tool (fixed)", "—", "—", "~R$ 100"],
            ["Planned total", "—", "—", "~R$ 500"],
        ],
        "gastos_note": (
            "Narrated video and automatic print are not in this 500. If video "
            "is turned on one day, that is a separate spend, outside the 500. "
            "If the month has fewer books, only drawing spend drops; the "
            "R$ 100 tool stays."
        ),
        "h_msg": "Plain statement",
        "quote": (
            "September: by the 8th, the planned work is the right site and "
            "the face lock live. From the 9th, the planned work is 2 new "
            "books a day, at least 4 pages each. New copy needs OK the day "
            "before. Planned spend for the month: about 500 reais (AI + "
            "tools). From October the planned work is site maintenance. A "
            "new book only with new copy. Video and automatic print are not "
            "planned."
        ),
        "check_title": "How to follow along",
        "check_items": [
            "Friday 5 Sep: link to the right site.",
            "September Fridays: how many books closed that week (planned: 2 per working day, ≥ 4 pages).",
            "October Fridays: what was fixed on the site, not a book quota.",
        ],
        "fine": (
            "Internal and client plan. Checked on 2 September 2026. "
            "This is not a contract or a commercial proposal."
        ),
        "cover_foot": "storyrus.ai",
    },
}


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
        textColor=GOLD, letterSpacing=1.2, alignment=TA_CENTER, spaceAfter=8,
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title", parent=base["Normal"], fontName=bold, fontSize=26,
        textColor=colors.white, leading=32, alignment=TA_CENTER, spaceAfter=10,
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
    s["stat_n"] = ParagraphStyle(
        "stat_n", parent=base["Normal"], fontName=bold, fontSize=13,
        textColor=NAVY, alignment=TA_CENTER, leading=16,
    )
    s["stat_l"] = ParagraphStyle(
        "stat_l", parent=base["Normal"], fontName=face, fontSize=7.5,
        textColor=MUTED, alignment=TA_CENTER, leading=10,
    )
    s["quote"] = ParagraphStyle(
        "quote", parent=base["Normal"], fontName=italic, fontSize=10.5,
        textColor=INK, leading=15, alignment=TA_JUSTIFY, leftIndent=8, rightIndent=8,
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
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
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
    inner = [
        [_p(title, styles["callout_t"])],
        [_p(body, styles["callout"])],
    ]
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


def _stats(items: list[tuple[str, str]], styles: dict, width: float) -> Table:
    n = len(items)
    cw = width / n
    nums = [_p(a, styles["stat_n"]) for a, _ in items]
    labs = [_p(b, styles["stat_l"]) for _, b in items]
    t = Table([nums, labs], colWidths=[cw] * n)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEAFTER", (0, 0), (-2, -1), 0.4, RULE),
    ]))
    return t


def _bullets(items: list[str], styles: dict) -> ListFlowable:
    flow = [ListItem(_p(b, styles["body_left"]), leftIndent=8, value="•") for b in items]
    return ListFlowable(flow, bulletType="bullet", start="•", leftIndent=12, spaceAfter=10)


def build_lang(lang: str) -> Path:
    c = COPY[lang]
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
    story.append(_p(c["cover_kicker"], styles["cover_kicker"]))
    story.append(_p(c["cover_title"], styles["cover_title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(_p(c["cover_sub"], styles["cover_sub"]))
    story.append(PageBreak())

    story.append(_p(c["h_pronto"], styles["h1"]))
    story.append(_callout(c["pronto_t"], c["pronto_b"], styles, W))
    story.append(Spacer(1, 6 * mm))
    story.append(_stats(c["stats"], styles, W))
    story.append(Spacer(1, 6 * mm))

    story.append(_p(c["h_blocos"], styles["h1"]))
    story.append(_p(c["blocos_intro"], styles["body"]))
    story.append(_table(c["th_bloco"], c["rows_bloco"], [32 * mm, 28 * mm, 62 * mm, 53 * mm], styles))

    story.append(_p(c["h_fila"], styles["h2"]))
    story.append(_table(c["th_fila"], c["rows_fila"], [38 * mm, 72 * mm, 65 * mm], styles))

    story.append(_p(c["h_setup"], styles["h1"]))
    story.append(_p(c["setup_intro"], styles["body"]))
    story.append(_bullets(c["setup_items"], styles))

    story.append(_p(c["h_estoque"], styles["h1"]))
    story.append(_table(c["th_estoque"], c["rows_estoque"], [48 * mm, 58 * mm, 69 * mm], styles))

    story.append(_p(c["h_out"], styles["h1"]))
    story.append(_p(c["out_intro"], styles["body"]))
    story.append(_bullets(c["out_items"], styles))

    story.append(_p(c["h_assume"], styles["h1"]))
    story.append(_table(c["th_assume"], c["rows_assume"], [87.5 * mm, 87.5 * mm], styles))

    story.append(_p(c["h_gastos"], styles["h1"]))
    story.append(_p(c["gastos_intro"], styles["body"]))
    story.append(_callout(c["total_t"], c["total_b"], styles, W))
    story.append(Spacer(1, 4 * mm))
    story.append(_table(c["th_fecha"], c["rows_fecha"], [120 * mm, 55 * mm], styles))
    story.append(_p(c["h_desenho"], styles["h2"]))
    story.append(_p(c["desenho_b"], styles["body"]))
    story.append(_table(c["th_escala"], c["rows_escala"], [120 * mm, 55 * mm], styles))
    story.append(_p(c["escala_note"], styles["small"]))
    story.append(_p(c["h_ferramenta"], styles["h2"]))
    story.append(_p(c["ferramenta_b"], styles["body"]))
    story.append(_p(c["h_conta"], styles["h2"]))
    story.append(_table(c["th_conta"], c["rows_conta"], [55 * mm, 40 * mm, 45 * mm, 35 * mm], styles))
    story.append(_p(c["gastos_note"], styles["small"]))

    story.append(_p(c["h_msg"], styles["h2"]))
    story.append(_p(c["quote"], styles["quote"]))
    story.append(Spacer(1, 6 * mm))
    story.append(_p(c["check_title"], styles["h2"]))
    story.append(_bullets(c["check_items"], styles))
    story.append(_p(c["fine"], styles["small"]))

    out: Path = c["out"]

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
        canvas.drawString(18 * mm, h - 8 * mm, c["header"])
        canvas.drawRightString(w - 18 * mm, h - 8 * mm, c["date"])
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, 12 * mm, w, 1 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont(font, 8)
        canvas.drawString(18 * mm, 5 * mm, c["footer_l"])
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
        canvas.drawCentredString(w / 2, 8 * mm, c["cover_foot"])
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=c["title_doc"],
        author="Story R Us",
        subject=c["title_doc"],
    )
    doc.build(story, onFirstPage=first_page, onLaterPages=later)
    return out


def build() -> list[Path]:
    return [build_lang("pt"), build_lang("en")]


if __name__ == "__main__":
    for p in build():
        print(p)
