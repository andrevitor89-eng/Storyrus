"""Prompts do pipeline foto -> avatar -> paginas do livro.

Regras de ouro:
- 1 avatar-base gerado da foto; reusado como character_ref em TODAS as paginas
- Estilo TMT aprovado: rosto pintura fotorrealista 1:1; corpo ilustrado; luz cinematografica; cenario pintado
- Figurino da HISTORIA nas paginas (explorador, medica, marinheiro...); avatar nao trava a roupa da foto
- Identidade da foto e imutavel e esta ACIMA do estilo: nao inventar franja, olhos, idade, etnia
- Proporcoes naturais da foto (cabeca anatomica, sem aumento); sem chibi/funko
- Expressao facial MUDA por pagina e deve coincidir com a historia
"""
from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------- #
# Expressoes faciais permitidas
# --------------------------------------------------------------------------- #
EXPRESSIONS: dict[str, str] = {
    "alegria": "sorriso aberto, olhar atento, bochechas levemente erguidas",
    "curiosidade": "sobrancelhas levemente erguidas, boca entreaberta, olhar atento",
    "medo_gentil": "palpebras um pouco mais abertas (sem aumentar o globo), boca fechada tensa, sem terror",
    "determinacao": "olhar firme, queixo um pouco erguido, boca fechada decidida",
    "surpresa": "palpebras um pouco mais abertas (sem aumentar o globo), boca em 'o' suave, sobrancelhas erguidas",
    "calma": "sorriso fechado suave, olhar sereno e aconchegante",
    "tristeza_leve": "cantos da boca baixos, olhar um pouco baixo, sem choro exagerado",
    "concentracao": "sobrancelhas levemente franzidas, olhar focado, boca fechada",
    "carinho": "sorriso terno, olhar suave, cabeca levemente inclinada",
    "orgulho": "peito erguido, sorriso confiante, olhar firme",
    "vergonha": "olhar baixo, sorriso timido, bochechas levemente rosadas",
    "animacao": "sorriso largo, energia no olhar, sem aumentar os olhos",
}

_DEFAULT_EXPRESSION = "alegria"

_INFER_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("medo_gentil", re.compile(r"medo|assust|escuro|trem|perigo|susto|receio", re.IGNORECASE)),
    ("tristeza_leve", re.compile(r"trist|chor|doente|separad|desanim|sozinh|saudade", re.IGNORECASE)),
    ("vergonha", re.compile(r"vergonh|timid|constrang|envergonh|corado", re.IGNORECASE)),
    ("surpresa", re.compile(r"surpre|de repente|olha!|inesperad|uau|nossa|assombro", re.IGNORECASE)),
    ("curiosidade", re.compile(r"curios|pergunt|descob|imagin|pensa|olha as|observ|investig", re.IGNORECASE)),
    ("determinacao", re.compile(r"decid|determin|coragem|tentar|construir|ajuda|limpo|miss|enfrentar", re.IGNORECASE)),
    ("concentracao", re.compile(r"concent|cuidado|conta|junta|coloca|aprende|foco", re.IGNORECASE)),
    ("carinho", re.compile(r"abrac|carinh|amor|anin|colo|corac|beijo", re.IGNORECASE)),
    ("orgulho", re.compile(r"orgulh|conquist|consegui|pronto|cheinho|vitor", re.IGNORECASE)),
    ("animacao", re.compile(r"empolg|animad|eufor|pulando|correndo de alegria|animacao", re.IGNORECASE)),
    ("calma", re.compile(r"calm|quiet|paz|dorm|tranquil|seren|descans", re.IGNORECASE)),
    ("alegria", re.compile(r"feliz|alegr|sorr|brinc|festa|brilha|divert|risad", re.IGNORECASE)),
]


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize_expression(value: str | None) -> str:
    if not value:
        return _DEFAULT_EXPRESSION
    key = _strip_accents(value.strip().lower()).replace(" ", "_").replace("-", "_")
    aliases = {
        "medo": "medo_gentil",
        "tristeza": "tristeza_leve",
        "triste": "tristeza_leve",
        "feliz": "alegria",
        "happy": "alegria",
        "curious": "curiosidade",
        "surprised": "surpresa",
        "calm": "calma",
        "determined": "determinacao",
        "proud": "orgulho",
        "tender": "carinho",
        "focused": "concentracao",
        "shy": "vergonha",
        "excited": "animacao",
        "empolgado": "animacao",
        "timido": "vergonha",
    }
    key = aliases.get(key, key)
    return key if key in EXPRESSIONS else _DEFAULT_EXPRESSION


def infer_expression(*texts: str) -> str:
    blob = _strip_accents(" ".join(t for t in texts if t))
    for name, pattern in _INFER_RULES:
        if pattern.search(blob):
            return name
    return _DEFAULT_EXPRESSION


def expression_directive(expression: str | None) -> str:
    key = normalize_expression(expression)
    detail = EXPRESSIONS[key]
    return (
        f"EXPRESSAO FACIAL OBRIGATORIA desta pagina: '{key}' ({detail}). "
        "MUDE so a emocao: sobrancelhas, cantos da boca, tensao dos labios e "
        "olhar — o necessario para a emocao aparecer. "
        "NAO mude o TAMANHO dos olhos: emocao NAO autoriza olhos maiores; a "
        "fracao do rosto permanece a da foto/avatar. "
        "NAO mude identidade: mesmo formato de rosto/bochechas, mesmos olhos "
        "(cor, tamanho NATURAL, espacamento), mesmo nariz, mesma estrutura da "
        "boca, mesmo cabelo, mesmo tom de pele e mesma idade do avatar-base. "
        "PROIBIDO copiar a expressao neutra do avatar; a emocao desta pagina "
        "vence. Nunca altere a estrutura do rosto so para forcar a expressao."
    )


# --------------------------------------------------------------------------- #
# Enquadramento e faixa de texto (roteiro visual da pagina)
# --------------------------------------------------------------------------- #
SHOTS: dict[str, str] = {
    "close": "close do rosto ou da acao — aproxime a camera; o objeto/rosto ocupa boa parte do quadro",
    "medium": "plano medio — tronco e cabeca visiveis, cenario ainda le",
    "wide": "plano geral — corpo inteiro e cenario amplo",
    "detail": "plano detalhe — objeto, mao ou acao em close; o rosto pode sair do quadro",
}
_DEFAULT_SHOT = "medium"
_SHOT_ALIASES = {
    "closeup": "close",
    "close_up": "close",
    "plano_detalhe": "detail",
    "detalhe": "detail",
    "wide_shot": "wide",
    "geral": "wide",
    "plano_geral": "wide",
    "plano_medio": "medium",
    "medio": "medium",
}

TEXT_BANDS = ("top", "bottom", "left", "right")
_DEFAULT_TEXT_BAND = "bottom"

# Expressoes empacotadas na grade 2x2 da ficha (expression_sheet).
EXPRESSION_SHEET_KEYS: tuple[str, ...] = ("alegria", "surpresa", "determinacao", "calma")


def normalize_shot(value: str | None) -> str:
    if not value:
        return _DEFAULT_SHOT
    key = _strip_accents(value.strip().lower()).replace(" ", "_").replace("-", "_")
    key = _SHOT_ALIASES.get(key, key)
    return key if key in SHOTS else _DEFAULT_SHOT


def normalize_text_band(value: str | None) -> str:
    if not value:
        return _DEFAULT_TEXT_BAND
    key = _strip_accents(value.strip().lower())
    return key if key in TEXT_BANDS else _DEFAULT_TEXT_BAND


def shot_directive(shot: str | None) -> str:
    key = normalize_shot(shot)
    return f"ENQUADRAMENTO OBRIGATORIO: '{key}' ({SHOTS[key]})."


def text_band_directive(band: str | None) -> str:
    key = normalize_text_band(band)
    if key in {"left", "right"}:
        lado = "esquerdo" if key == "left" else "direito"
        return (
            f"FAIXA DE TEXTO: reserve cerca de 45% do lado {lado} do quadro ({key}) "
            "como uma area calma e limpa (nevoa suave, agua ou folhagem desfocada), "
            "sem personagens nem objetos importantes. Mantenha o protagonista "
            "inteiramente no lado oposto: rosto, cabelo, corpo e maos nao podem "
            "entrar nessa area."
        )
    lado = "superior" if key == "top" else "inferior"
    return (
        f"FAIXA DE TEXTO: deixe a faixa {lado} do quadro ({key}) mais calma/limpa "
        "(ceu, agua ou folhagem suave) para a estrofe impressa. Nao coloque o "
        "rosto do protagonista nessa faixa."
    )


# --------------------------------------------------------------------------- #
# Avatar (foto -> personagem-base)
# --------------------------------------------------------------------------- #
_HEAD_PROPORTION = (
    "PROPORCAO DA CABECA: identica a da foto — tamanho NATURAL, anatomico, "
    "sem aumentar. PROIBIDO cabeca grande, bobblehead, chibi, funko, anime "
    "ou olhos grandes de cartoon."
)

_SUBJECT_LOCK = (
    "SUJEITO: a crianca da foto de referencia e a UNICA pessoa a desenhar. "
    "Ignore adultos, colo, maos de quem segura, outras pessoas, casa, caminho "
    "e cenario. NAO inclua ninguem alem da crianca."
)

_GENERIC_FACE_LOCK = (
    "ANTI-ROSTO-GENERICO (prioridade maxima): NAO invente um bebe de animacao "
    "fofo, rosto de banco de imagens ou crianca 'bonitinha' padronizada. A "
    "identidade e a da foto anexa. Colocada ao lado da foto, um familiar deve "
    "reconhecer na hora que e a MESMA crianca. Se o modelo hesitar, copie os "
    "tracos atipicos da foto em vez de suavizar. "
    "NAO deixe a crianca 'mais fofa' aumentando os olhos. Identidade da foto "
    "esta ACIMA do estilo de livro."
)

_HAIR_LOCK = (
    "CABELO (imutavel): copie da foto o penteado EXATO — cor, textura, "
    "comprimento, risca, volume, densidade e se existe ou NAO existe franja. "
    "Se o cabelo da foto for fino, ralo ou esvoacante, MANTENHA assim — "
    "PROIBIDO engrossar, escurecer ou 'penteado de salao'. "
    "Se a testa estiver visivel na foto, a testa DEVE ficar visivel no avatar. "
    "PROIBIDO inventar franja, cortina, baby bangs, fios na testa ou mudar o "
    "penteado. Nao 'melhore' o cabelo."
)

_FACE_FIDELITY = (
    "ROSTO REALISTA: deve parecer uma foto desta crianca, qualidade de camera — "
    "pintura digital fotorrealista (pele, cilios, iris, labios, cabelo fio a fio), "
    "identidade 1:1. "
    "Acabamento levemente pictorico, com tracos leves de desenho — mais REAL "
    "que desenho. Nao foto crua colada; nao cartoon. IDENTIDADE (rosto, olhos, "
    "nariz, boca, idade) esta ACIMA do estilo. NAO cole o rosto fotografico "
    "como recorte. "
    "OLHOS: ocupam a MESMA fracao do rosto que na foto — mesma largura, "
    "altura, espacamento e quantidade de branco visivel. Se hesitar, DIMINUA; "
    "NUNCA aumente. PROIBIDO iris gigante, olho de boneca, brilho de lente "
    "cobrindo o olho, fofura via olhos maiores, olhos anime/chibi/cartoon. "
    "IDENTIDADE: copie da foto formato, espacamento e cor EXATA dos olhos, "
    "palpebras, estrutura ossea, bochechas, sobrancelhas, nariz, labios, "
    "tom de pele e idade aparente. "
    "IDADE: a da foto (bebe continua bebe; nao 'envelheca' para um modelo fofo). "
    "FORMATO DO ROSTO: largura, bochechas, queixo e pescoco identicos a foto "
    "(mesma fracao da largura da cabeca). PROIBIDO embelezar engordando "
    "bochechas, arredondando o maxilar ou alargando a cara — nao faca uma "
    "versao mais gorda/fofa do mesmo menino. Se o rosto estiver "
    "mais cheio que a foto, REDUZA o volume das bochechas ate bater. "
    "PELE: microtextura NATURAL da foto, acabamento pictorico leve (nao "
    "porcelana, nao airbrush pesado, nao filtro de beleza, nao pele plastica lisa). "
    "Sem poros grotescos de close extremo. "
    "BOCA: copie a BOCA e o TIPO de sorriso da foto (se for sorriso pequeno/"
    "candido, mantenha pequeno). PROIBIDO sorriso largo de banco de imagens "
    "e sorriso fechado de desenho. "
    "ACESSORIOS DE IDENTIDADE: preserve brinco, oculos ou outro acessorio do "
    "ROSTO visivel na foto; NAO invente o que nao estiver la. "
    "NAO embeleze, NAO 'corrija' tracos atipicos, assimetria ou estrutura "
    "ossea unica. NAO invente sardas, pintas, covinhas ou dentes que nao "
    "estejam claramente na foto."
)

_HYBRID_STYLE = (
    "ESTILO TMT OBRIGATORIO (Tell My Tale). "
    "ROSTO: pintura digital fotorrealista desta crianca, identidade 1:1 da foto "
    "(olhos, nariz, boca, orelhas, cabelo fio a fio, idade). Acabamento "
    "levemente pictorico, tracos leves de desenho — mais REAL que desenho. "
    "Nao foto crua colada; nao cartoon; nao chibi. "
    "CORPO: ilustracao 3D de livro infantil (pescoco, ombros, bracos, maos "
    "desenhados; junta continua no pescoco); corpo mais DESENHO que o rosto. "
    "LUZ: cinematografica, quente, glow suave, contraluz/rim light, atmosfera magica. "
    "CENARIO: concept art pintado, rico, saturado, com profundidade — nao foto, "
    "nao 2D chapado, nao linha preta. "
    "IDENTIDADE ACIMA DO ESTILO: o realismo do rosto NAO altera proporcoes "
    "do rosto ou dos olhos. "
    "PROIBIDO: colagem, recorte fotografico, pele de porcelana/plastica, "
    "olhos de boneca enormes, chibi, olhos anime, cel-shading, cartoon chapado, "
    "Pixar/CGI, marca d'agua, texto."
)

_WATERMARK_LOCK = (
    "MARCA D'AGUA E TEXTO: ignore e REMOVA qualquer marca d'agua de banco de "
    "imagens (Vecteezy, Dreamstime, Shutterstock, Getty, etc.), letras na frente "
    "do rosto, logos e captions. Nunca copie texto da foto para a ilustracao."
)

AVATAR_PROMPT = (
    "TAREFA: gere UM retrato-base (avatar) da pessoa da foto, para ser a UNICA "
    "referencia de IDENTIDADE (rosto, cabelo, corpo) em todas as paginas de um "
    "livro infantil personalizado. A roupa deste retrato NAO e o figurino do livro.\n\n"
    "IDENTITY LOCK: desenhe ESTA crianca especifica da foto anexa. NAO invente "
    "uma crianca generica. Se colocada ao lado da foto, um pai/mae deve "
    "reconhecer na hora.\n\n"
    "IDENTIDADE (prioridade maxima, ACIMA do estilo): a pessoa deve ser "
    "reconhecivel — mesmos tracos da foto (formato do rosto e bochechas; olhos "
    "na MESMA fracao do rosto; sobrancelhas; nariz; boca; cabelo; tom de pele; "
    "idade). O rosto deve parecer uma foto desta crianca, qualidade de camera, "
    "com tracos leves de desenho; corpo claramente DESENHADO. NAO cole a "
    "foto como recorte. "
    "NAO embelezar, NAO inventar caracteristicas, NAO mudar etnia, idade ou "
    "proporcoes. Colocada ao lado da foto, a pessoa deve ser 100% reconhecivel.\n\n"
    f"{_SUBJECT_LOCK}\n\n"
    f"{_GENERIC_FACE_LOCK}\n\n"
    f"{_FACE_FIDELITY}\n\n"
    f"{_HEAD_PROPORTION}\n\n"
    f"{_HAIR_LOCK}\n\n"
    f"{_HYBRID_STYLE}\n\n"
    f"{_WATERMARK_LOCK}\n\n"
    "COMPOSICAO: UMA so crianca, meio corpo (peito + ombros visiveis e largos o bastante), de frente, "
    "camera na altura dos olhos (NAO plongee / NAO close de rosto). A cabeca deve "
    "ocupar no maximo ~1/3 da altura do quadro; ombros e tronco visiveis abaixo. "
    "Proporcao cabeca-corpo NATURAL da foto — NUNCA cabeca gigante nem bobblehead. "
    "Expressao NEUTRA-ALEGRE leve: parta do sorriso REAL da foto (pequeno se a "
    "foto for pequena) — so o rosto-padrao de referencia; nas cenas do livro a "
    "expressao facial MUDARA conforme a historia. Fundo creme suave ou bokeh "
    "luminoso — SEM casa, SEM caminho, SEM cenario narrativo, SEM objetos, SEM "
    "texto, SEM moldura, SEM marca d'agua. "
    "ROUPA: peca ilustrada simples (nao copiar o macacao/trator nem a roupa da "
    "foto peca por peca). Este retrato e so identidade; o figurino do livro "
    "entra nas paginas.\n\n"
    "SAIDA: uma unica imagem limpa do personagem TMT (rosto pintura fotorrealista "
    "com tracos leves; corpo desenhado). "
    "Este arquivo sera o character_ref imutavel de identidade de todas as paginas."
)

STYLE = (
    "estilo TMT: rosto pintura fotorrealista, qualidade de camera, tracos leves "
    "de desenho (mais real que desenho); "
    "corpo mais DESENHO que o rosto; luz cinematografica quente com glow e "
    "contraluz; crianca identica a referencia (rosto e olhos na mesma fracao da foto); "
    "cabeca em proporcao NATURAL; identidade acima do estilo; figurino da historia "
    "nas paginas; sem texto"
)

CHARACTER_GEN_PREFIX = (
    "Crie um personagem TMT a partir das fotos de "
    "referencia: o rosto deve parecer uma foto, qualidade de camera, com tracos leves "
    "de desenho; corpo claramente desenhado. A foto vale para rosto, cabelo e corpo — "
    "NAO copie a roupa da foto. "
    "TRAVE A IDENTIDADE (acima do estilo): mesmo formato de rosto, mesmos olhos "
    "(cor e MESMA fracao do rosto; se hesitar, diminua), mesmo nariz, boca e sobrancelhas, mesmo cabelo e penteado da "
    "foto (franja so se a foto tiver franja; testa visivel se a foto mostrar "
    "testa), mesmo tom de pele e mesma idade. "
    "Nao invente tracos, nao embeleze, nao 'corrija' tracos atipicos, nao mude "
    f"etnia nem idade. Sem texto, sem moldura, sem marca d'agua. {_SUBJECT_LOCK} "
    f"{_GENERIC_FACE_LOCK} {_FACE_FIDELITY} "
    f"{_HEAD_PROPORTION} {_HAIR_LOCK} {_HYBRID_STYLE} {_WATERMARK_LOCK} "
)

# --------------------------------------------------------------------------- #
# Cena (avatar + historia -> pagina)
# --------------------------------------------------------------------------- #
SCENE_GEN_PREFIX = (
    "REGRA CRITICA DE IDENTIDADE (prioridade maxima, acima de qualquer outra "
    "instrucao): a imagem anexada e a UNICA fonte de verdade para o ROSTO, "
    "cabelo, idade e proporcoes do protagonista. Voce NAO esta criando um "
    "personagem novo - voce esta REDESENHANDO EXATAMENTE A MESMA CRIANCA da "
    "imagem de referencia (avatar-base) em uma nova cena. Copie da referencia, "
    "traco a traco: formato do rosto e das "
    "bochechas; olhos (cor, formato, MESMA fracao do rosto, espacamento); sobrancelhas; "
    "nariz; boca (estrutura base); cabelo (cor exata, textura, comprimento, franja, "
    "risca, penteado); tom de pele; idade aparente; proporcoes do corpo. "
    "NAO copie a ROUPA do avatar nem a roupa da foto — o figurino e o da HISTORIA "
    "(explorador, medica, marinheiro, etc.), o mesmo em todas as paginas. "
    "Colocada lado a lado com a referencia, a crianca desta cena deve parecer "
    "dois quadros do mesmo filme - mesma pessoa; mudam pose, EXPRESSAO FACIAL, "
    "cenario e figurino tematico. "
    f"{_FACE_FIDELITY} "
    f"{_HEAD_PROPORTION} {_HAIR_LOCK} "
    "EXPRESSAO: o avatar-base tem expressao NEUTRA — NAO a copie. Aplique a "
    "emocao pedida nesta pagina (sorriso, tristeza, surpresa, etc.) mudando so "
    "sobrancelhas, boca e olhar — NAO o tamanho dos olhos; a estrutura do rosto permanece a do avatar. "
    f"{_HYBRID_STYLE} "
    "PROIBIDO: inventar outra crianca parecida; mudar cabelo, idade, "
    "etnia ou tom de pele; 'embelezar' ou estilizar o rosto de forma diferente "
    "da referencia; copiar a roupa da foto ou do avatar; copiar a "
    "POSE ESTATICA (sentado/parado de frente para a camera) da imagem de "
    "referencia quando a cena pedir outra coisa - a referencia e so um retrato "
    "parado e NAO deve travar a pose desta cena. "
    "ENQUADRAMENTO E COMPOSICAO: siga EXATAMENTE o que a descricao da cena pedir "
    "- se pedir um CLOSE ou PLANO DETALHE (ex.: closeup de uma mao, de um objeto), "
    "faca um close de verdade, aproximando a camera de verdade do objeto/acao "
    "pedido: o objeto (moeda, mao, etc.) deve ocupar boa parte do quadro, e o "
    "rosto do personagem pode ficar PARCIALMENTE fora do enquadramento, desfocado "
    "ou nem aparecer - nao force mostrar o rosto inteiro nem afaste a camera so "
    "para caber o personagem completo. CLOSE NAO AUMENTA OS OLHOS: a fracao do "
    "olho no rosto permanece a da foto/avatar; se o rosto entrar no close, "
    "REDUZA os olhos se estiverem maiores. se "
    "pedir uma cena com 2 personagens, pose e as duas; se pedir uma cena DIVIDIDA "
    "em paineis, divida a imagem em paineis. NAO force um enquadramento de corpo "
    "inteiro em cenas que pedem outra coisa. Fora isso, a pose e a acao do "
    "personagem devem ser dinamicas e condizentes com a cena (nao paradas feito "
    "retrato), respeitando sempre o enquadramento pedido. So a IDENTIDADE (rosto, "
    "cabelo, tom de pele, idade) fica fixa; pose, expressao, acao, figurino, "
    "enquadramento e cenario seguem a cena descrita. "
)

REFINE_SCENE_PROMPT = (
    "Voce recebe DUAS imagens: (1) o AVATAR-BASE de referencia e (2) uma "
    "ILUSTRACAO de cena de um livro infantil. Sua unica tarefa e corrigir a "
    "IDENTIDADE DO ROSTO: redesenhe a cabeca do protagonista para ficar IDENTICA ao "
    "avatar de referencia, copiando traco a traco: formato do rosto e "
    "bochechas; olhos (cor, formato, MESMA fracao do rosto da referencia/foto — "
    "se maiores, REDUZA; PROIBIDO olhos grandes anime/chibi/cartoon, espacamento, "
    "palpebras); sobrancelhas (espessura); nariz (largura/ponta); boca (labios); "
    "cabelo (cor exata, textura, comprimento, franja, risca - NAO troque o "
    "penteado/corte); tom de pele; idade aparente. "
    "PRESERVE o FIGURINO ja presente na cena (roupa, chapeu, botas, acessorios "
    "de historia). NAO substitua o figurino pela roupa do avatar nem pela roupa "
    "da foto. Se qualquer item de IDENTIDADE (rosto/cabelo/idade) estiver "
    "diferente na cena, substitua-o pelo da referencia - a referencia SEMPRE "
    "vence no rosto. NAO mude o cenario, a composicao, o enquadramento, a iluminacao, "
    "a pose, a acao nem a ROUPA da cena. PRESERVE a EXPRESSAO FACIAL ja presente na "
    "cena (ajuste so a estrutura do rosto para bater com o avatar; NAO resetar "
    "para a expressao neutra do avatar; nao apague a emocao da pagina). "
    "Mantenha o estilo TMT: o rosto deve parecer uma foto, qualidade de "
    "camera, com tracos leves de desenho; corpo DESENHADO; figurino da historia; "
    "cenario pintado, nao fotografia. "
    "Se a primeira imagem extra for a FOTO real, ela e a verdade do ROSTO "
    "(geometria, realismo e nitidez; REDUZA olhos se maiores que na foto); o avatar "
    "vale para identidade e estilo desenhado, NAO para o guarda-roupa. "
    f"{_HYBRID_STYLE} {_HEAD_PROPORTION} {_HAIR_LOCK} "
    "Devolva apenas a cena corrigida."
)

REFINE_IDENTITY_PROMPT = (
    "TAREFA CIRURGICA: voce recebe DUAS imagens em ordem. "
    "(1) o RECORTE do rosto da FOTO — unica fonte de verdade dos olhos, nariz, "
    "bochechas, queixo e do REALISMO do rosto (nao cole o close como colagem). "
    "(2) o PERSONAGEM a corrigir. "
    "Ajuste SO A CABECA: copie a GEOMETRIA e a qualidade de camera do recorte "
    "para o rosto (deve parecer uma foto, com tracos leves de desenho). Preserve corpo e "
    "roupa DESENHADOS, pose, enquadramento (meio corpo) e fundo. "
    f"{_SUBJECT_LOCK} {_GENERIC_FACE_LOCK} {_FACE_FIDELITY} {_HAIR_LOCK} {_WATERMARK_LOCK} "
    "Os olhos costumam estar maiores que na foto; REDUZA ate a "
    "mesma fracao do rosto. Se hesitar, diminua. NUNCA aumente. "
    "Se o rosto estiver mais gordo/cheio que a foto, REDUZA o volume das "
    "bochechas e a largura da cara ate a geometria do recorte. "
    "PROIBIDO colar o rosto fotografico como recorte. "
    "NAO invente franja. NAO 'corrija' tracos atipicos. "
    f"{_HEAD_PROPORTION} "
    "Devolva apenas o personagem corrigido."
)


def build_scene_prompt(
    *,
    page: int,
    text: str,
    scene: str = "",
    expression: str | None = None,
    extras: str = "",
    child_name: str = "",
    shot: str = "",
    text_band: str = "",
) -> str:
    """Monta o prompt de cena para uma pagina do livro."""
    note = (scene or "").strip()
    caption = (text or "").strip()
    expr = normalize_expression(expression) if expression else infer_expression(caption, note)
    name_bit = f" O protagonista se chama {child_name}." if child_name else ""
    extras_bit = f" {extras.strip()}" if extras and extras.strip() else ""

    parts = [
        f"Pagina {page} da historia.{name_bit}",
        expression_directive(expr),
    ]
    if shot:
        parts.append(shot_directive(shot))
    if note:
        parts.append(
            "CENA (siga o enquadramento pedido com exatidao - close, plano detalhe, "
            f"cena dividida em paineis, ou outro, conforme descrito): {note}"
        )
    if caption:
        parts.append(
            "Texto da pagina (so para entender acao/sentimento, NAO escrever na "
            f'imagem): "{caption}".'
        )
    if extras_bit:
        parts.append(extras_bit.strip())
    parts.append(
        "Composicao QUADRADA (1:1), cena TMT de livro infantil: a crianca e "
        "identica a referencia (rosto realista deve parecer uma foto, qualidade de camera, "
        "com tracos leves de desenho; "
        "corpo desenhado; figurino da historia); cenario pintado rico com "
        "luz cinematografica, glow suave e contraluz; "
        "deixe uma area mais calma/limpa (ceu, agua, folhagem suave) para receber "
        "o texto impresso."
    )
    if text_band:
        parts.append(text_band_directive(text_band))
    return " ".join(parts)


ALPHABET_SCENE_EXTRAS = (
    "Pagina de alfabeto: destaque UM animal ou UMA fruta com a acao pedida na cena; "
    "inclua uma letra grande abstrata (madeira, espuma ou topiaria na forma da "
    "letra da pagina). A letra e so silhueta — NUNCA texto legivel, palavras, "
    "legendas, captions ou o nome do animal ou da fruta escrito na arte."
)

NAME_PAGE_SCENE_EXTRAS = (
    "Pagina de apresentacao do nome: a crianca e o unico foco principal. "
    "PROIBIDO incluir animal ou fruta em destaque. PROIBIDO desenhar letras, "
    "iniciais, palavras, placas, legendas, captions ou o nome da crianca na arte, "
    "mesmo como madeira, topiaria ou silhueta. A tipografia sera acrescentada "
    "depois, fora do gerador de imagem."
)

AMAZON_SCENE_EXTRAS = (
    "Cenario: floresta amazonica umida (rio, arvores, luz filtrada). "
    "PROIBIDO neve, gelo, savana africana, eucalipto australiano."
)

NUMBER_SCENE_EXTRAS = (
    "Pagina de numeros: inclua um numeral grande abstrato (madeira, espuma ou "
    "topiaria na forma do numero da pagina). O numeral e so silhueta — NUNCA "
    "texto legivel, palavras, legendas ou captions na arte. Se a nota pedir "
    "objetos contaveis, mostre a quantidade EXATA, bem separada e facil de contar; "
    "se pedir foco no tracado, NAO amontoe dezenas de objetos."
)

COLOR_SCENE_EXTRAS = (
    "Pagina de cores: uma cor dominante, alto contraste, agrupamento de objetos "
    "reais dessa cor. Nas paginas de mistura, mostre os dois pigmentos e o "
    "resultado no meio. NUNCA texto legivel, palavras, legendas, captions ou o "
    "nome da cor escrito na arte."
)

OPPOSITES_SCENE_EXTRAS = (
    "Pagina de opostos: os dois extremos (ou o extremo pedido) visiveis e obvios "
    "na cena — escala, direcao ou estado claros. NUNCA texto legivel, palavras, "
    "legendas ou captions na arte."
)


COSTUME_EXPLORER = (
    "FIGURINO TMT OBRIGATORIO (uma fantasia por livro, igual em todas as paginas): "
    "explorador infantil — camisa ou colete caqui, shorts ou calca safari, botas. "
    "Chapeu de explorador e binoculos ok. "
    "PROIBIDO copiar a roupa da foto (macacao, trator, jeans da foto) e a roupa do avatar-base."
)

COSTUME_ORCHARD = (
    "FIGURINO TMT OBRIGATORIO (uma fantasia por livro, igual em todas as paginas): "
    "aventureiro de pomar — roupa leve ilustrada de brincadeira. "
    "PROIBIDO copiar a roupa da foto ou do avatar-base."
)

COSTUME_STORYBOOK = (
    "FIGURINO TMT OBRIGATORIO (uma fantasia por livro, igual em todas as paginas): "
    "roupa ilustrada de livro infantil condizente com a cena. "
    "PROIBIDO copiar a roupa da foto ou do avatar-base."
)

_THEME_COSTUMES: dict[str, str] = {
    "adventure": COSTUME_EXPLORER,
    "princess": (
        "FIGURINO TMT OBRIGATORIO: vestido ou traje de conto de fadas ilustrado, "
        "o mesmo em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "superhero": (
        "FIGURINO TMT OBRIGATORIO: traje de heroi infantil ilustrado (capa leve), "
        "o mesmo em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "space": (
        "FIGURINO TMT OBRIGATORIO: astronauta infantil leve ilustrado, "
        "o mesmo em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "underwater": (
        "FIGURINO TMT OBRIGATORIO: marinheiro ou mergulhador infantil ilustrado, "
        "o mesmo em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "dinosaurs": COSTUME_EXPLORER,
    "fantasy": (
        "FIGURINO TMT OBRIGATORIO: traje de conto de fadas ilustrado, "
        "o mesmo em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "birthday": (
        "FIGURINO TMT OBRIGATORIO: roupa de festa ilustrada, "
        "a mesma em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "christmas": (
        "FIGURINO TMT OBRIGATORIO: roupa natalina ilustrada, "
        "a mesma em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "easter": (
        "FIGURINO TMT OBRIGATORIO: roupa primaveril ilustrada, "
        "a mesma em todas as paginas. PROIBIDO copiar a roupa da foto ou do avatar-base."
    ),
    "childrens_day": COSTUME_STORYBOOK,
    "mothers_day": COSTUME_STORYBOOK,
    "fathers_day": COSTUME_STORYBOOK,
    "new_year": COSTUME_STORYBOOK,
}


def costume_extras_for_template(template_id: str | None) -> str:
    """Figurino TMT do livro de catalogo. Vazio se o template nao tiver fantasia propria."""
    if template_id == "alfabeto_amazonia":
        return COSTUME_EXPLORER
    if template_id == "alfabeto_frutas":
        return COSTUME_ORCHARD
    if template_id in {"numeros_1_15", "cores_basicas", "grande_pequeno"}:
        return COSTUME_STORYBOOK
    return ""


def costume_extras_for_theme(theme: str | None) -> str:
    """Figurino TMT para historia inventada, a partir do tema do projeto."""
    if not theme:
        return COSTUME_EXPLORER
    return _THEME_COSTUMES.get(theme.strip().lower(), COSTUME_STORYBOOK)


# --------------------------------------------------------------------------- #
# Ficha do personagem (3 imagens no inicio do ebook)
# --------------------------------------------------------------------------- #
CHARACTER_SHEET_PROMPT = (
    "FICHA DE PERSONAGEM (turnaround). TAREFA: uma unica imagem com a MESMA "
    "crianca em 2 ou 3 poses lado a lado — FRENTE, TRES-QUARTOS e (se couber) "
    "PERFIL. Roupa ilustrada SIMPLES, a do avatar (NAO o figurino da historia). "
    "Fundo creme limpo, sem cenario narrativo, sem texto, sem moldura. "
    "Identidade 1:1 da foto/avatar em TODAS as poses: mesmo rosto, cabelo, "
    "proporcoes, idade. Corpo desenhado, rosto pintura fotorrealista TMT. "
    f"{_SUBJECT_LOCK} {_GENERIC_FACE_LOCK} {_FACE_FIDELITY} {_HEAD_PROPORTION} "
    f"{_HAIR_LOCK} {_HYBRID_STYLE} {_WATERMARK_LOCK} "
    "SAIDA: uma ficha limpa de identidade, nao uma cena."
)

EXPRESSION_SHEET_PROMPT = (
    "GRADE DE EXPRESSOES 2x2. TAREFA: uma unica imagem com QUATRO retratos da "
    "MESMA crianca, mesma identidade, mesma roupa simples do avatar, fundo creme. "
    "Ordem: canto superior esquerdo ALEGRIA; superior direito SURPRESA; "
    "inferior esquerdo DETERMINACAO; inferior direito CALMA. "
    "Mude so sobrancelhas, boca e olhar — NAO o tamanho dos olhos nem o "
    "penteado. Sem texto, sem legendas, sem moldura. "
    f"{_SUBJECT_LOCK} {_GENERIC_FACE_LOCK} {_FACE_FIDELITY} {_HEAD_PROPORTION} "
    f"{_HAIR_LOCK} {_HYBRID_STYLE} {_WATERMARK_LOCK} "
    "SAIDA: grade 2x2 de expressoes, nao uma cena narrativa."
)


def costume_lock_prompt(costume: str) -> str:
    """Prompt do retrato de figurino (corpo inteiro, fundo creme)."""
    figurino = (costume or "").strip() or COSTUME_STORYBOOK
    return (
        "FIGURINO LOCK. TAREFA: um retrato de CORPO INTEIRO desta crianca com o "
        "figurino da HISTORIA, pose neutra-alegre, de frente, fundo creme. "
        "Este arquivo e a referencia de ROUPA de todas as paginas — copie o "
        "figurino da descricao, NAO a roupa da foto nem a do avatar. "
        f"FIGURINO: {figurino} "
        "Identidade 1:1 da foto/avatar (rosto, cabelo, idade, proporcoes). "
        "Sem cenario narrativo, sem texto, sem moldura. "
        f"{_SUBJECT_LOCK} {_GENERIC_FACE_LOCK} {_FACE_FIDELITY} {_HEAD_PROPORTION} "
        f"{_HAIR_LOCK} {_HYBRID_STYLE} {_WATERMARK_LOCK} "
        "SAIDA: um personagem de corpo inteiro no figurino da historia."
    )


def scene_extras_for_template(template_id: str | None) -> str:
    """Extras de cena do ebook conforme o livro de catálogo (inclui figurino TMT)."""
    if not template_id:
        return ""
    from app.story_templates import (
        ALPHABET_TEMPLATE_IDS,
        COLOR_TEMPLATE_IDS,
        NUMBER_TEMPLATE_IDS,
        OPPOSITES_TEMPLATE_IDS,
    )

    extras = ""
    if template_id in ALPHABET_TEMPLATE_IDS:
        extras = ALPHABET_SCENE_EXTRAS
        if template_id == "alfabeto_amazonia":
            extras = f"{extras} {AMAZON_SCENE_EXTRAS}"
    elif template_id in NUMBER_TEMPLATE_IDS:
        extras = NUMBER_SCENE_EXTRAS
    elif template_id in COLOR_TEMPLATE_IDS:
        extras = COLOR_SCENE_EXTRAS
    elif template_id in OPPOSITES_TEMPLATE_IDS:
        extras = OPPOSITES_SCENE_EXTRAS
    costume = costume_extras_for_template(template_id)
    if extras and costume:
        return f"{extras} {costume}"
    return extras or costume


def name_scene_extras_for_template(template_id: str | None) -> str:
    """Extras da pagina de nome, sem instrucoes de animal/letra do alfabeto."""
    extras = [NAME_PAGE_SCENE_EXTRAS]
    if template_id == "alfabeto_amazonia":
        extras.append(AMAZON_SCENE_EXTRAS)
    costume = costume_extras_for_template(template_id)
    if costume:
        extras.append(costume)
    return " ".join(extras)
