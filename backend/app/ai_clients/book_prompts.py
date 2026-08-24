# -*- coding: utf-8 -*-
"""Prompts do pipeline foto -> avatar -> paginas do livro.

Regras de ouro:
- 1 avatar-base gerado da foto; reusado como character_ref em TODAS as paginas
- Personagem em CGI 3D de filme infantil, nunca foto nem pintura 2D
- Identidade da foto e imutavel: nao inventar franja, olhos, idade, etnia
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
    "alegria": "sorriso aberto, olhos vivos e brilhantes, bochechas levemente erguidas",
    "curiosidade": "sobrancelhas levemente erguidas, boca entreaberta, olhar atento",
    "medo_gentil": "olhos um pouco mais abertos, boca fechada tensa, sem terror",
    "determinacao": "olhar firme, queixo um pouco erguido, boca fechada decidida",
    "surpresa": "olhos abertos, boca em 'o' suave, sobrancelhas erguidas",
    "calma": "sorriso fechado suave, olhar sereno e aconchegante",
    "tristeza_leve": "cantos da boca baixos, olhar um pouco baixo, sem choro exagerado",
    "concentracao": "sobrancelhas levemente franzidas, olhar focado, boca fechada",
    "carinho": "sorriso terno, olhar suave, cabeca levemente inclinada",
    "orgulho": "peito erguido, sorriso confiante, olhos brilhantes",
    "vergonha": "olhar baixo, sorriso timido, bochechas levemente rosadas",
    "animacao": "sorriso largo, olhos bem abertos de empolgacao, energia no rosto",
}

_DEFAULT_EXPRESSION = "alegria"

_INFER_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("medo_gentil", re.compile(r"medo|assust|escuro|trem|perigo|susto|receio", re.I)),
    ("tristeza_leve", re.compile(r"trist|chor|doente|separad|desanim|sozinh|saudade", re.I)),
    ("vergonha", re.compile(r"vergonh|timid|constrang|envergonh|corado", re.I)),
    ("surpresa", re.compile(r"surpre|de repente|olha!|inesperad|uau|nossa|assombro", re.I)),
    ("curiosidade", re.compile(r"curios|pergunt|descob|imagin|pensa|olha as|observ|investig", re.I)),
    ("determinacao", re.compile(r"decid|determin|coragem|tentar|construir|ajuda|limpo|miss|enfrentar", re.I)),
    ("concentracao", re.compile(r"concent|cuidado|conta|junta|coloca|aprende|foco", re.I)),
    ("carinho", re.compile(r"abrac|carinh|amor|anin|colo|corac|beijo", re.I)),
    ("orgulho", re.compile(r"orgulh|conquist|consegui|pronto|cheinho|vitor", re.I)),
    ("animacao", re.compile(r"empolg|animad|eufor|pulando|correndo de alegria|animacao", re.I)),
    ("calma", re.compile(r"calm|quiet|paz|dorm|tranquil|seren|descans", re.I)),
    ("alegria", re.compile(r"feliz|alegr|sorr|brinc|festa|brilha|divert|risad", re.I)),
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
        "MUDE so a emocao: sobrancelhas, cantos da boca, tensao dos labios, "
        "abertura dos olhos e olhar — o necessario para a emocao aparecer. "
        "NAO mude identidade: mesmo formato de rosto/bochechas, mesmos olhos "
        "(cor, tamanho NATURAL, espacamento), mesmo nariz, mesma estrutura da "
        "boca, mesmo cabelo, mesmo tom de pele e mesma idade do avatar-base. "
        "PROIBIDO copiar a expressao neutra do avatar; a emocao desta pagina "
        "vence. Nunca altere a estrutura do rosto so para forcar a expressao."
    )


# --------------------------------------------------------------------------- #
# Avatar (foto -> personagem-base)
# --------------------------------------------------------------------------- #
_HEAD_PROPORTION = (
    "PROPORCAO DA CABECA: identica a da foto — tamanho NATURAL, anatomico, "
    "sem aumentar. Estilizacao 3D leve (fofo) e permitida; PROIBIDO cabeca "
    "grande, bobblehead, chibi, funko, anime ou olhos grandes de cartoon."
)

_SUBJECT_LOCK = (
    "SUJEITO: a crianca da foto de referencia e a UNICA pessoa a desenhar. "
    "Ignore adultos, colo, maos de quem segura, outras pessoas, casa, caminho "
    "e cenario. NAO inclua ninguem alem da crianca."
)

_GENERIC_FACE_LOCK = (
    "ANTI-ROSTO-GENERICO (prioridade maxima): NAO invente um bebe CGI fofo, "
    "rosto de banco de imagens ou crianca 'bonitinha' padronizada. A identidade "
    "e a da foto anexa. Colocada ao lado da foto, um familiar deve reconhecer "
    "na hora que e a MESMA crianca. Se o modelo hesitar, copie os tracos "
    "atipicos da foto em vez de suavizar."
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
    "ROSTO EM CGI 3D: reinterprete a pessoa como personagem de filme de "
    "animacao infantil em render 3D — volumes suaves, luz de estudio, pele "
    "CGI (nao poros de foto). NAO copie a foto original, NAO cole o rosto "
    "fotografico, NAO faca pintura 2D nem oleo. "
    "IDENTIDADE: copie da foto formato, espacamento e cor EXATA dos olhos, "
    "palpebras, estrutura ossea, bochechas, sobrancelhas, nariz, labios, "
    "tom de pele e idade aparente. Estilizacao 3D leve (fofo) e ok; "
    "PROIBIDO olhos anime, chibi, cartoon ou olhos CGI enormes. "
    "IDADE: a da foto (bebe continua bebe; nao 'envelheca' para um modelo fofo). "
    "PELE: o tom NATURAL da foto — nao porcelana, nao blush rosado pesado, "
    "nao filtro de beleza. "
    "BOCA: copie a BOCA e o TIPO de sorriso da foto (se for sorriso pequeno/"
    "candido, mantenha pequeno). PROIBIDO sorriso largo de banco de imagens "
    "e sorriso fechado de desenho. "
    "ACESSORIOS: preserve brinco, oculos ou outro acessorio visivel na foto; "
    "NAO invente o que nao estiver la. "
    "NAO embeleze, NAO 'corrija' tracos atipicos, assimetria ou estrutura "
    "ossea unica. NAO invente sardas, pintas, covinhas ou dentes que nao "
    "estejam claramente na foto."
)

_CGI_3D_STYLE = (
    "ESTILO CGI 3D DE FILME INFANTIL OBRIGATORIO: personagem em render 3D de "
    "animacao infantil — volumes suaves, luz de estudio; pele, cabelo, corpo, "
    "roupa e fundo no MESMO material CGI. Claramente um personagem de filme, "
    "fofo e estilizado. "
    "PROIBIDO: fotografia, filtro de beleza, pintura 2D, oleo, colagem, "
    "recorte, linha preta, chibi, olhos anime."
)

_WATERMARK_LOCK = (
    "MARCA D'AGUA E TEXTO: ignore e REMOVA qualquer marca d'agua de banco de "
    "imagens (Vecteezy, Dreamstime, Shutterstock, Getty, etc.), letras na frente "
    "do rosto, logos e captions. Nunca copie texto da foto para a ilustracao."
)

AVATAR_PROMPT = (
    "TAREFA: gere UM retrato-base (avatar) da pessoa da foto, para ser a UNICA "
    "referencia de identidade em todas as paginas de um livro infantil personalizado.\n\n"
    "IDENTITY LOCK: desenhe ESTA crianca especifica da foto anexa. NAO invente "
    "uma crianca generica. Se colocada ao lado da foto, um pai/mae deve "
    "reconhecer na hora.\n\n"
    "IDENTIDADE (prioridade maxima): a pessoa deve ser reconhecivel — mesmos "
    "tracos da foto (formato do rosto e bochechas; olhos cor/formato/tamanho "
    "NATURAL; sobrancelhas; nariz; boca; cabelo; tom de pele; idade), mas "
    "REINTERPRETADOS em CGI 3D de filme infantil, nao copiados como fotografia. "
    "NAO embelezar, NAO inventar caracteristicas, NAO mudar etnia, idade ou "
    "proporcoes. Colocada ao lado da foto, a pessoa deve ser 100% reconhecivel.\n\n"
    f"{_SUBJECT_LOCK}\n\n"
    f"{_GENERIC_FACE_LOCK}\n\n"
    f"{_FACE_FIDELITY}\n\n"
    f"{_HEAD_PROPORTION}\n\n"
    f"{_HAIR_LOCK}\n\n"
    f"{_CGI_3D_STYLE}\n\n"
    f"{_WATERMARK_LOCK}\n\n"
    "COMPOSICAO: UMA so crianca, meio corpo (peito + ombros visiveis e largos o bastante), de frente, "
    "camera na altura dos olhos (NAO plongee / NAO close de rosto). A cabeca deve "
    "ocupar no maximo ~1/3 da altura do quadro; ombros e tronco visiveis abaixo. "
    "Proporcao cabeca-corpo NATURAL da foto — NUNCA cabeca gigante nem bobblehead. "
    "Expressao NEUTRA-ALEGRE leve: parta do sorriso REAL da foto (pequeno se a "
    "foto for pequena) — so o rosto-padrao de referencia; nas cenas do livro a "
    "expressao facial MUDARA conforme a historia. Fundo neutro, "
    "liso, creme suave — SEM cenario, SEM objetos, SEM texto, SEM moldura, SEM "
    "marca d'agua. Roupa da foto, peca por peca, volumes CGI 3D.\n\n"
    "SAIDA: uma unica imagem limpa do personagem 3D. Este arquivo sera o character_ref "
    "imutavel de todas as paginas."
)

STYLE = (
    "CGI 3D de filme infantil (rosto e corpo no mesmo material 3D, nao copia "
    "da foto); personagem fofo de animacao; identidade da foto; cabeca em "
    "proporcao NATURAL (sem aumentar, sem chibi); fundo liso; sem texto"
)

CHARACTER_GEN_PREFIX = (
    "Crie um personagem em CGI 3D DE FILME INFANTIL a partir das fotos de "
    "referencia: render 3D (nao copiado da foto), corpo no mesmo material CGI. "
    "TRAVE A IDENTIDADE: mesmo formato de rosto, mesmos olhos (cor e tamanho "
    "NATURAL), mesmo nariz, boca e sobrancelhas, mesmo cabelo e penteado da "
    "foto (franja so se a foto tiver franja; testa visivel se a foto mostrar "
    "testa), mesmo tom de pele e mesma idade. Use a mesma roupa das fotos. "
    "Nao invente tracos, nao embeleze, nao 'corrija' tracos atipicos, nao mude "
    f"etnia nem idade. Sem texto, sem moldura, sem marca d'agua. {_SUBJECT_LOCK} "
    f"{_GENERIC_FACE_LOCK} {_FACE_FIDELITY} "
    f"{_HEAD_PROPORTION} {_HAIR_LOCK} {_CGI_3D_STYLE} {_WATERMARK_LOCK} "
)

# --------------------------------------------------------------------------- #
# Cena (avatar + historia -> pagina)
# --------------------------------------------------------------------------- #
SCENE_GEN_PREFIX = (
    "REGRA CRITICA DE IDENTIDADE (prioridade maxima, acima de qualquer outra "
    "instrucao): a imagem anexada e a UNICA fonte de verdade para a aparencia "
    "do protagonista. Voce NAO esta criando um personagem novo - voce esta "
    "REDESENHANDO EXATAMENTE A MESMA CRIANCA da imagem de referencia (avatar-base) "
    "em uma nova cena. Copie da referencia, traco a traco: formato do rosto e das "
    "bochechas; olhos (cor, formato, tamanho NATURAL, espacamento); sobrancelhas; "
    "nariz; boca (estrutura base); cabelo (cor exata, textura, comprimento, franja, "
    "risca, penteado); tom de pele; idade aparente; proporcoes do corpo; e a "
    "MESMA ROUPA da referencia, peca por peca, com as mesmas cores. "
    "Colocada lado a lado com a referencia, a crianca desta cena deve parecer "
    "dois quadros do mesmo filme - mesma pessoa; so mudam pose, EXPRESSAO FACIAL "
    "e cenario. "
    f"{_FACE_FIDELITY} "
    f"{_HEAD_PROPORTION} {_HAIR_LOCK} "
    "EXPRESSAO: o avatar-base tem expressao NEUTRA — NAO a copie. Aplique a "
    "emocao pedida nesta pagina (sorriso, tristeza, surpresa, etc.) mudando so "
    "sobrancelhas, boca e olhar; a estrutura do rosto permanece a do avatar. "
    f"{_CGI_3D_STYLE} "
    "PROIBIDO: inventar outra crianca parecida; mudar cabelo, roupa, idade, "
    "etnia ou tom de pele; 'embelezar' ou estilizar o rosto de forma diferente "
    "da referencia; adicionar acessorios que nao existem na referencia; copiar a "
    "POSE ESTATICA (sentado/parado de frente para a camera) da imagem de "
    "referencia quando a cena pedir outra coisa - a referencia e so um retrato "
    "parado e NAO deve travar a pose desta cena. "
    "ENQUADRAMENTO E COMPOSICAO: siga EXATAMENTE o que a descricao da cena pedir "
    "- se pedir um CLOSE ou PLANO DETALHE (ex.: closeup de uma mao, de um objeto), "
    "faca um close de verdade, aproximando a camera de verdade do objeto/acao "
    "pedido: o objeto (moeda, mao, etc.) deve ocupar boa parte do quadro, e o "
    "rosto do personagem pode ficar PARCIALMENTE fora do enquadramento, desfocado "
    "ou nem aparecer - nao force mostrar o rosto inteiro nem afaste a camera so "
    "para caber o personagem completo; se "
    "pedir uma cena com 2 personagens, pose e as duas; se pedir uma cena DIVIDIDA "
    "em paineis, divida a imagem em paineis. NAO force um enquadramento de corpo "
    "inteiro em cenas que pedem outra coisa. Fora isso, a pose e a acao do "
    "personagem devem ser dinamicas e condizentes com a cena (nao paradas feito "
    "retrato), respeitando sempre o enquadramento pedido. So a IDENTIDADE (rosto, "
    "cabelo, roupa, tom de pele) fica fixa; pose, expressao, acao, enquadramento e "
    "cenario seguem a cena descrita. "
)

REFINE_SCENE_PROMPT = (
    "Voce recebe DUAS imagens: (1) o AVATAR-BASE de referencia e (2) uma "
    "ILUSTRACAO de cena de um livro infantil. Sua unica tarefa e corrigir a "
    "identidade: redesenhe o protagonista da cena para ficar IDENTICO ao "
    "avatar de referencia, copiando traco a traco: formato do rosto e "
    "bochechas; olhos (cor, formato, TAMANHO EXATO da referencia/foto — "
    "proporcao natural, PROIBIDO olhos grandes anime/chibi/cartoon, espacamento, "
    "palpebras); sobrancelhas (espessura); nariz (largura/ponta); boca (labios); "
    "cabelo (cor exata, textura, comprimento, franja, risca - NAO troque o "
    "penteado/corte); tom de pele; idade aparente; e a "
    "MESMA ROUPA da referencia, peca por peca, com as mesmas cores (se a "
    "referencia veste o macacao direto sobre a pele, sem camiseta por baixo, "
    "REMOVA qualquer camiseta/blusa que a cena tenha adicionado por baixo, "
    "mesmo em vistas de costas ou de lado). Se qualquer um desses itens estiver "
    "diferente na cena, substitua-o pelo da referencia - a referencia SEMPRE "
    "vence. NAO mude o cenario, a composicao, o enquadramento, a iluminacao, "
    "a pose nem a acao da cena. PRESERVE a EXPRESSAO FACIAL ja presente na "
    "cena (ajuste so a estrutura do rosto para bater com o avatar; NAO resetar "
    "para a expressao neutra do avatar; nao apague a emocao da pagina). "
    "Mantenha o mesmo estilo CGI 3D de filme infantil (personagem 3D, nao foto). "
    f"{_CGI_3D_STYLE} {_HEAD_PROPORTION} {_HAIR_LOCK} "
    "Devolva apenas a cena corrigida."
)

REFINE_IDENTITY_PROMPT = (
    "Voce recebe DUAS imagens em ordem: (1) a FOTO real — fonte de verdade da "
    "IDENTIDADE (rosto + cabelo); (2) o PERSONAGEM 3D a corrigir. Ajuste so a "
    "identidade para ficar reconhecivel, MANTENDO o estilo CGI 3D de filme "
    "infantil. "
    f"{_SUBJECT_LOCK} {_GENERIC_FACE_LOCK} {_FACE_FIDELITY} {_HAIR_LOCK} {_WATERMARK_LOCK} "
    "PROIBIDO copiar a foto original, colar o rosto fotografico ou 'fotorealizar' "
    "o personagem. Se os olhos estiverem grandes ou genericos, REDUZA para o "
    "tamanho da foto (estilizacao 3D leve ok; sem anime). Se o sorriso for "
    "largo demais ou 'de banco de imagens', volte ao sorriso da foto. Preserve "
    "a mesma roupa, pose, enquadramento (meio corpo) e fundo — NAO copie o close "
    "da foto nem aumente a cabeca. NAO invente franja. NAO 'corrija' tracos atipicos. "
    f"{_CGI_3D_STYLE} {_HEAD_PROPORTION} "
    "Devolva apenas o personagem 3D corrigido."
)


def build_scene_prompt(
    *,
    page: int,
    text: str,
    scene: str = "",
    expression: str | None = None,
    extras: str = "",
    child_name: str = "",
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
        "Composicao QUADRADA (1:1), cena em CGI 3D de filme infantil, luz de "
        "estudio, cores limpas; deixe uma area mais calma/limpa (ceu, campo, "
        "parede) para receber o texto impresso."
    )
    return " ".join(parts)
