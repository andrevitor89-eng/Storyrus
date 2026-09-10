"""Gera o relatorio de entregas da plataforma para a cliente (A4)."""
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
    KeepTogether,
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
OUT = ROOT / "Relatorio-Story-R-Us-plataforma-setembro-2026.pdf"
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"
WIN = Path(r"C:\Windows\Fonts")

NAVY = colors.Color(0.106, 0.184, 0.373)
GOLD = colors.Color(0.956, 0.718, 0.251)
CREAM = colors.Color(1.0, 0.972, 0.936)
INK = colors.Color(0.18, 0.20, 0.24)
MUTED = colors.Color(0.38, 0.40, 0.45)
RULE = colors.Color(0.82, 0.84, 0.88)
ROW = colors.Color(0.97, 0.96, 0.94)


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
    s["footer"] = ParagraphStyle(
        "footer", parent=base["Normal"], fontName=face, fontSize=8,
        textColor=MUTED, alignment=TA_CENTER,
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
    for i, row in enumerate(rows):
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


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 12 * mm, w, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 12.8 * mm, w, 1.2 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Body-Bold" if "Body-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold", 8)
    canvas.drawString(18 * mm, h - 8 * mm, "STORY R US  ·  Relatório de entregas da plataforma")
    canvas.drawRightString(w - 18 * mm, h - 8 * mm, "1º de setembro de 2026")
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 12 * mm, w, 1 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Body" if "Body" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 8)
    canvas.drawString(18 * mm, 5 * mm, "storyrus.ai  ·  confidencial — uso da cliente")
    canvas.drawRightString(w - 18 * mm, 5 * mm, f"Página {doc.page}")
    canvas.restoreState()


def _cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 8 * mm, w, 8 * mm, fill=1, stroke=0)
    canvas.rect(0, 0, w, 8 * mm, fill=1, stroke=0)
    canvas.restoreState()
    _header_footer(canvas, doc)


def build() -> Path:
    face, bold, italic = _register_fonts()
    styles = _styles(face, bold, italic)
    W = A4[0] - 36 * mm
    story = []

    # --- capa (flowables sobre fundo navy via onFirstPage) ---
    story.append(Spacer(1, 28 * mm))
    if LOGO.exists():
        img = Image(str(LOGO), width=42 * mm, height=42 * mm)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 8 * mm))
    story.append(_p("RELATÓRIO DE ENTREGAS", styles["cover_kicker"]))
    story.append(_p("O que a Story R Us<br/>já entrega hoje", styles["cover_title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(_p(
        "Inventário da plataforma para a cliente<br/>"
        "junho de 2026 a 1º de setembro de 2026<br/><br/>"
        "site no ar · estúdio · livros de amostra · o que ainda falta",
        styles["cover_sub"],
    ))
    story.append(PageBreak())

    # --- 0 resumo ---
    story.append(_p("Pode conferir agora", styles["h1"]))
    story.append(_callout(
        "A plataforma está publicada",
        "O endereço <b>https://storyrus.ai</b> não é um rascunho. O site, o estúdio, "
        "os livros de exemplo, os vídeos e o fluxo foto → personagem → história → PDF "
        "já existem. Este documento descreve, em português, o que foi feito desde junho "
        "— e, com honestidade, o que ainda não está pronto. Não é contrato nem lista de preços.",
        styles, W,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_stats([
        ("No ar", "Site e estúdio\nem storyrus.ai"),
        ("4 + 4", "Livros de exemplo\ne vídeos no site"),
        ("28", "Temas para criar\na história"),
        ("9", "PDFs de amostra\njá gerados"),
    ], styles, W))
    story.append(Spacer(1, 8 * mm))
    story.append(_p("Mensagem objetiva (para enviar)", styles["h2"]))
    story.append(_p(
        "A plataforma Story R Us está no ar em storyrus.ai: site em português e inglês, "
        "quatro livros de exemplo que folheiam, quatro vídeos narrados, estúdio para enviar "
        "a foto, gerar o personagem, escolher entre 28 temas (ou um livro pronto), baixar o "
        "PDF e pedir vídeo. Também já produzimos, para aprovação, o Alfabeto da Amazônia do "
        "Matteo (livro completo), as primeiras páginas de Cores e do Pomar com o texto que "
        "vocês enviaram, e avatares de oito crianças. O e-book digital já nasce na plataforma; "
        "o livro impresso ainda é sob consulta. O próximo passo combinado é fechar o restante "
        "das páginas dos livros educativos e seguir travando o rosto da criança em todas as cenas.",
        styles["quote"],
    ))

    story.append(_p("1. O site público — o que a família vê", styles["h1"]))
    story.append(_p(
        "Aberto hoje em <b>https://storyrus.ai</b>, em português e inglês, com tema claro e "
        "escuro. A promessa na primeira tela é a mesma do produto: a foto vira personagem, "
        "história, livro em PDF e vídeo narrado.",
        styles["body"],
    ))
    story.append(_table(
        ["O que tem no site", "Para que serve", "Como conferir"],
        [
            ["Hero com foto real → capa do livro",
             "Mostra o antes e o depois: a criança e o livro ilustrado",
             "Primeira tela: Matteo/dinossauros, Sofia/floresta, Noah/circo"],
            ["Como funciona em 3 passos",
             "Foto → personagem e história → a família folheia o livro",
             "Seção “Como funciona”, com o livro do Matteo abrindo"],
            ["Dicas de foto",
             "Ensina o enquadramento que a IA precisa (rosto de frente, luz, uma criança)",
             "Exemplos com certo e errado"],
            ["Catálogo com 4 livros + história surpresa",
             "Cada tema é um livro 3D que folheia páginas reais daquele universo",
             "Lia (mar), Sofia (floresta), Matteo (dinos), Noah (circo) + IA"],
            ["Quatro vídeos narrados",
             "A mesma história ganha voz, trilha e movimento",
             "Seção “Vídeos narrados” — cada card tem player"],
            ["Folheie nossos livros",
             "Flipbook interativo com páginas geradas pela plataforma",
             "Abas: Lia, Chloe, Sofia, Matteo, Noah"],
            ["Perguntas frequentes",
             "Como criar, prévia, privacidade da foto, digital vs impresso, alterações, vídeo",
             "Rodapé da página"],
            ["Privacidade e termos",
             "A foto da criança não vai para marketing; só entra na geração do livro",
             "Links Privacidade e Termos no rodapé"],
            ["Botão Criar minha história",
             "Leva para o estúdio, onde a família envia a foto e gera o livro",
             "Vários botões na página, inclusive no hero"],
        ],
        [48 * mm, 72 * mm, 55 * mm],
        styles,
    ))

    story.append(_p("2. O estúdio — o produto, não só a vitrine", styles["h1"]))
    story.append(_p(
        "O site mostra exemplos. O estúdio é onde o livro da criança nasce. "
        "O fluxo abaixo já funciona de ponta a ponta.",
        styles["body"],
    ))
    story.append(_table(
        ["Etapa", "O que a família faz", "O que a plataforma devolve"],
        [
            ["Foto", "Envia uma foto de frente, uma criança, luz boa",
             "Personagem ilustrado com o rosto da criança (não um desenho genérico)"],
            ["Aprovar o personagem", "Confere se reconhece o filho",
             "Esse personagem vira a base de todas as páginas"],
            ["História",
             "Escolhe um tema, um livro pronto do catálogo, escreve o texto ou manda um arquivo",
             "Texto com o nome da criança no título e nas páginas; templates prontos não gastam crédito de IA"],
            ["Livro em PDF", "Pede para montar o e-book (1 crédito)",
             "Capa + páginas ilustradas, para folhear na tela e baixar"],
            ["Animação curta", "Opcional, 5 créditos",
             "Clipe de 5–10 segundos do personagem em movimento"],
            ["Vídeo narrado", "Opcional, 8 créditos",
             "História de 1–2 minutos com voz e as cenas do livro"],
            ["Voz", "Pode clonar uma voz da família",
             "A narração sai com essa voz, não só com voz padrão"],
            ["Personagem extra", "Pode incluir irmão, pai, avó…",
             "Segundo personagem na história, sem misturar os rostos"],
        ],
        [38 * mm, 72 * mm, 65 * mm],
        styles,
    ))
    story.append(_p("Temas que a família já pode escolher", styles["h2"]))
    story.append(_p(
        "Vinte e oito temas, em três grupos — não é “uma história genérica”. "
        "Dá para combinar até dois temas na mesma história, informar traço e interesse "
        "da criança, e escolher o idioma. Login e cadastro existem; quem entra sem conta "
        "também consegue experimentar, agora com sessão própria (não mistura com outro visitante).",
        styles["body"],
    ))
    story.append(_table(
        ["Grupo", "Temas"],
        [
            ["Aventura e fantasia",
             "Aventura, princesas, super-heróis, espaço, fundo do mar, dinossauros, fantasia"],
            ["Datas",
             "Aniversário, Natal, Páscoa, Dia das Crianças, Dia das Mães, Dia dos Pais, Ano Novo"],
            ["Educativo",
             "Alfabetização, matemática, cores, opostos, higiene, hora de dormir, alimentação, "
             "vestir-se, sentimentos, corpo, compartilhar, animais, transporte, clima"],
        ],
        [42 * mm, 133 * mm],
        styles,
    ))

    story.append(_p("3. Livros e artes já produzidos", styles["h1"]))
    story.append(_p(
        "Além dos exemplos da vitrine, geramos livros de verdade — PDFs com dezenas de "
        "megabytes, páginas ilustradas, personagem a partir da foto. Isso é o que se manda "
        "para aprovação, não um mockup.",
        styles["body"],
    ))
    story.append(_table(
        ["Livro", "Para quem", "O que existe hoje", "Tam."],
        [
            ["Alfabeto da Amazônia", "Matteo",
             "Livro completo: dedicatória, página do nome (M · A · T · T · E · O), 24 animais "
             "da floresta, capa jaqueta (frente + verso) e logo na contracapa. Sem a cartilha "
             "“A de Arara”: cada página é o animal na cena.", "95 MB"],
            ["Matteo e as Cores", "Catálogo educativo",
             "Páginas 1 a 5 prontas: dedicatória, preto, branco, vermelho, verde. O livro "
             "completo no spec tem 15 páginas (inclui mistura de cores).", "16 MB"],
            ["Matteo no Pomar", "Texto aprovado pela cliente (VF)",
             "Páginas 1 a 4: dedicatória (regar, esperar madurar, cuidar da terra), página do "
             "nome no pomar, abacaxi, banana. Spec de 15 frutas até o encerramento.", "12 MB"],
            ["Amazônia — recortes", "Ajustes de rosto e layout",
             "Várias versões P1–P4 / P1–P6 e uma versão realista, enquanto o rosto era travado "
             "página a página.", "11–17 MB"],
            ["Amazônia — Sofia", "Outra criança, mesmo livro",
             "Avatar + página 3 (floresta e arara), para não depender só do Matteo.", "6 MB"],
            ["Lia e o Fundo do Mar", "Exemplo do site",
             "Capa, páginas e vídeo no ar. A capa foi refeita com a camiseta certa, sem copiar "
             "a roupa da foto.", "No site"],
            ["Sofia, Matteo dinos, Noah circo", "Exemplos do site",
             "Capas, 6 páginas internas cada, vídeos narrados, flipbook. Títulos em tipografia "
             "(não queimados na arte), para o rosto não ficar coberto.", "No site"],
        ],
        [38 * mm, 38 * mm, 78 * mm, 21 * mm],
        styles,
    ))
    story.append(_p("Avatares de crianças reais (lote aprovado)", styles["h2"]))
    story.append(_p(
        "O personagem não é um “menino loiro padrão”. Rodamos o pipeline foto → recorte do "
        "rosto → personagem → duas correções em oito crianças, com imagem de comparação ao "
        "lado da foto: <b>Matteo, Emilia, Martin, Facundo, Antonio, Cristobal, Maria Jesus e Nicolas</b>.",
        styles["body"],
    ))
    story.append(_p(
        "O trabalho de agosto em identidade existe por um motivo que a família sente na hora: "
        "a página 3 não pode nascer com outro menino. Por isso o estúdio passou a exigir "
        "aprovação do rosto antes de montar o livro, e cada cena é julgada contra a foto.",
        styles["body"],
    ))

    story.append(_p("4. Como isso foi construído (junho → setembro)", styles["h1"]))
    story.append(_p(
        "Nada disso apareceu de uma vez. Abaixo, em linguagem de produto — o que passou a "
        "existir em cada fase.",
        styles["body"],
    ))
    story.append(_table(
        ["Quando", "O que a cliente passou a ter"],
        [
            ["29–30 de junho",
             "A plataforma existe: site infantil, estúdio, livro em PDF a partir da foto, "
             "logo e paleta. Site na Vercel e API no ar. Em 30 de junho já havia um produto "
             "visitável, não um slide."],
            ["Julho",
             "A vitrine deixa de ser cartaz: hero com foto real virando capa; catálogo 3D que "
             "folheia; quatro livros de exemplo (Lia, Sofia, Matteo, Noah); vídeos; dicas de "
             "foto; português/inglês; claro/escuro. Por baixo: personagem fiel em todas as "
             "páginas; histórias com começo, meio e fim; temas educativos; personagens extras; "
             "datas; estúdio numa tela só. No fim do mês: login no visual do site e títulos "
             "do hero sem tapar o rosto."],
            ["1–13 de agosto",
             "Artes e capa: Matteo reenquadrado (título não cobre o rosto); camiseta da Lia "
             "no livro do mar; personagem com rosto mais fotográfico e corpo de livro. Isso "
             "depois entrou no produto."],
            ["14–31 de agosto",
             "O mês mais visível: o personagem deixa de virar um bebê 3D genérico e trava na "
             "foto; vídeo narrado e vozes no estúdio; exemplos do site renovados; cada visitante "
             "com sessão própria; páginas de privacidade e termos. Livro da Amazônia do Matteo "
             "(29 páginas, capa jaqueta); Cores (5 primeiras páginas); Pomar com o texto "
             "aprovado (4 primeiras páginas); catálogo educativo (cores, pomar, números, "
             "grande/pequeno) no estúdio."],
        ],
        [38 * mm, 137 * mm],
        styles,
    ))

    story.append(_p("5. O que ainda não está pronto", styles["h1"]))
    story.append(_p(
        "Dizer que “não foi realizado nada” não fecha com o site no ar nem com os PDFs. "
        "O que ainda está aberto, com clareza — para não vender o que não tem:",
        styles["body"],
    ))
    story.append(_table(
        ["Item", "Situação hoje", "O que falta"],
        [
            ["Livro impresso com envio automático",
             "O site fala a verdade: PDF na hora; impresso é cotação em até 24 horas.",
             "Checkout, gráfica e rastreio ainda não são self-service."],
            ["Amazônia no catálogo do estúdio",
             "O PDF completo do Matteo existe; o livro saiu do catálogo público enquanto o rosto era travado.",
             "Republicar quando a identidade estiver estável, ou manter só como exemplar."],
            ["Cores e Pomar até a última página",
             "Spec de 15 páginas cada; geradas 5 (cores) e 4 (pomar).",
             "Gerar o restante depois da aprovação das primeiras."],
            ["Rosto 100% igual em todas as páginas",
             "A trava e o juiz já existem; ainda se ajusta.",
             "É o ponto em que mais se investiu em agosto — não está abandonado."],
            ["Melhorias ainda em revisão",
             "Padrão da foto no upload, pintura digital, PDF completo — código escrito, parte já no ar.",
             "Não muda o fato de o site e o estúdio já operarem."],
        ],
        [48 * mm, 68 * mm, 59 * mm],
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_callout(
        "Como responder à frase “não foi realizado nada”",
        "O endereço <b>storyrus.ai</b> está no ar com livros que folheiam, vídeos que tocam "
        "e um estúdio que gera personagem, história, PDF e vídeo a partir da foto. Existem "
        "PDFs de amostra (Amazônia com 29 páginas, Cores, Pomar). O que não está pronto é o "
        "envio automático do impresso e o fechamento de alguns livros educativos até a última "
        "página — não a inexistência da plataforma.",
        styles, W,
    ))

    story.append(_p("Como conferir em cinco minutos", styles["h1"]))
    bullets = [
        "Abra <b>https://storyrus.ai</b> no celular ou no computador.",
        "Folheie os quatro livros do catálogo e dê play nos quatro vídeos.",
        "Clique em <b>Criar minha história</b> e veja o estúdio (foto, temas, PDF, vídeo).",
        "Abra Privacidade e Termos no rodapé.",
        "Peça os PDFs de amostra já gerados: Amazônia (Matteo, livro completo), Cores P1–P5 e Pomar P1–P4.",
    ]
    items = [ListItem(_p(b, styles["body_left"]), leftIndent=8, value="•") for b in bullets]
    story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=12, spaceAfter=10))

    story.append(Spacer(1, 4 * mm))
    story.append(_p(
        "Conferido em 1º de setembro de 2026 no site público storyrus.ai e no material gerado "
        "(PDFs e artes). Este texto descreve o produto; não substitui contrato nem proposta comercial.",
        styles["small"],
    ))

    # capa usa onFirstPage diferente — platypus still draws header on page 1 via onFirstPage=_cover
    # Cover flowables are white text; header_footer on cover would clash. Use two templates.

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="O que a Story R Us já entrega hoje",
        author="Story R Us",
        subject="Relatório de entregas da plataforma — 1º de setembro de 2026",
    )

    def first_page(canvas, doc_):
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

    doc.build(story, onFirstPage=first_page, onLaterPages=_header_footer)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    print(f"{path.stat().st_size / 1024:.0f} KB")
