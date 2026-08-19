"""Biblia de estilo Tell My Tale + builders de prompt para Nano Banana.

Toda geracao de personagem/cena deve passar por estes builders para manter
uma DNA unica: pintura digital de livro infantil, fisionomia fiel a foto,
figurino e cenario do tema — sem hibrido rosto-foto + corpo cartoon/Funko.
"""
from __future__ import annotations

from typing import TypedDict

# Tokens que o pipeline antigo injetava e que NUNCA devem voltar aos prompts.
FORBIDDEN_STYLE_TOKENS: tuple[str, ...] = (
    "chibi",
    "funko",
    "estilo misto",
    "mesma roupa das fotos",
    "rosto deve ser realista",
    "parecer uma foto real",
)


class ThemeStaging(TypedDict):
    costume: str
    setting: str
    action: str


STYLE_BIBLE = (
    "BIBLIA DE ESTILO (obrigatoria): ilustre como pintura digital suave de livro "
    "infantil contemporaneo premium (picture book / storybook painterly). Pincelada "
    "visivel, sombreamento de bordas suaves, volume e luz direcional gentil. Paleta "
    "saturada e harmonica. Fundo com profundidade, nao chapado. Sem contorno cartoon "
    "grosso e sem linha preta dura. "
    "ROSTO ilustrado (pele pintada, olhos luminosos, expressao viva) — a crianca deve "
    "ser imediatamente reconhecivel ao lado da foto. Nao cole um retrato fotografico "
    "no corpo; nao renderize pele fotografica, poros ou hiper-realismo. Nao use "
    "proporcoes de boneco vinyl nem cabeca enorme. "
    "PROPORCAO: cabeca apenas levemente maior que o real (estilizacao sutil de livro "
    "infantil), corpo infantil proporcional, maos e pes corretos. "
    "Sem texto, sem moldura, sem marca d'agua."
)

IDENTITY_FROM_PHOTO = (
    "TRAVE A IDENTIDADE da crianca a partir da(s) foto(s) de referencia: mesmo "
    "formato de rosto e bochechas, mesmos olhos (cor, formato, tamanho e "
    "espacamento), mesmo nariz, boca e sorriso, mesmas sobrancelhas, mesmo cabelo "
    "(cor, textura, comprimento, franja, risca e penteado), mesmo tom de pele e a "
    "mesma idade aparente. Nao invente tracos, nao embeleze, nao mude etnia nem "
    "idade. NAO copie a roupa nem o fundo da foto."
)

IDENTITY_FROM_CHARACTER = (
    "REGRA CRITICA DE IDENTIDADE (prioridade maxima): a imagem anexada e a UNICA "
    "fonte de verdade para a aparencia do protagonista. Voce NAO esta criando um "
    "personagem novo — redesenhe EXATAMENTE A MESMA CRIANCA da referencia. Copie "
    "traco a traco: formato do rosto e das bochechas; olhos (cor, formato, tamanho, "
    "espacamento); sobrancelhas; nariz; boca e sorriso; cabelo (cor, textura, "
    "comprimento, franja, risca, penteado); tom de pele; idade aparente; proporcoes "
    "do corpo. Colocada lado a lado com a referencia, a crianca deve parecer dois "
    "quadros do mesmo filme. "
    "FIGURINO: use por padrao a MESMA ROUPA da ilustracao de referencia (ja e o "
    "figurino do tema), peca por peca. Pode acrescentar so um acessorio pontual se a "
    "cena exigir (chapeu de chuva, mochila, lanterna), sem trocar o traje-base. "
    "PROIBIDO: inventar outra crianca parecida; mudar cabelo, idade, etnia ou tom de "
    "pele; embelezar o rosto de forma diferente da referencia."
)

_STYLE_HINT: dict[str, str] = {
    "realistic": (
        "Variacao leve: semi-realista painterly — continua ilustracao de livro "
        "infantil, nunca fotografia."
    ),
    "cartoon": (
        "Variacao leve: um pouco mais estilizado e colorido, ainda pintura digital "
        "de livro infantil (nao desenho de TV, nao linha dura)."
    ),
    "anime": (
        "Variacao leve: olhos um pouco mais expressivos, ainda pintura digital de "
        "livro infantil (nao anime de TV, nao linha dura)."
    ),
}

_DEFAULT_STAGING: ThemeStaging = {
    "costume": (
        "roupa de explorador infantil: camisa leve, calca resistente, botas e um "
        "acessorio de aventura (chapeu ou cinto)"
    ),
    "setting": (
        "paisagem de conto de fadas ao ar livre, com profundidade, luz dourada suave "
        "e vegetacao rica"
    ),
    "action": "A crianca olha para a camera com um sorriso confiante, pronta para a historia.",
}

THEME_STAGING: dict[str, ThemeStaging] = {
    "adventure": {
        "costume": (
            "roupa de explorador: camisa khaki, shorts ou calca resistente, botas, "
            "cinto e chapeu de safari"
        ),
        "setting": (
            "trilha de selva exuberante com lianas, um papagaio colorido e ruinas "
            "suaves ao fundo"
        ),
        "action": "A crianca segura um mapa enrolado e sorri, pronta para a aventura.",
    },
    "princess": {
        "costume": (
            "traje real infantil: vestido ou tunica principesca com detalhes dourados "
            "suaves, sem bijuteria excessiva"
        ),
        "setting": "jardim de palacio ao entardecer, castelo suave ao fundo e flores luminosas",
        "action": "A crianca esta em pose gentil e confiante, como heroi de conto de fadas.",
    },
    "superhero": {
        "costume": (
            "traje de super-heroi infantil original (capa curta, emblema simples no "
            "peito), cores vivas e tecidos pintados com volume"
        ),
        "setting": "terraço urbano ao crepusculo, cidade iluminada ao fundo e ceu dramatico",
        "action": "A crianca esta em pose heroica amigavel, capa levemente ao vento.",
    },
    "space": {
        "costume": "pequeno traje de astronauta infantil bem ajustado, viseira erguida",
        "setting": "plataforma estelar com planeta colorido, estrelas e uma nave suave ao fundo",
        "action": "A crianca acena de dentro do traje, encantada com o cosmos.",
    },
    "underwater": {
        "costume": "roupa de mergulho infantil colorida, oculos na cabeca e nadadeiras discretas",
        "setting": "recife de coral iluminado, peixes tropicais e um tesouro suave ao fundo",
        "action": "A crianca flutua no azul, curiosa e sorridente.",
    },
    "dinosaurs": {
        "costume": (
            "roupa de paleontologo/explorador: camisa caqui, shorts, botas e chapeu, "
            "binoculo no pescoco"
        ),
        "setting": "clareira jurassica verde com um dinossauro amigavel ao fundo, nao assustador",
        "action": "A crianca observa o dinossauro com maravilha, sem medo.",
    },
    "fantasy": {
        "costume": "manto ou tunica encantada infantil, detalhes de folha/estrela pintados com suavidade",
        "setting": "floresta magica com cogumelos luminosos, vagalumes e um portal suave de luz",
        "action": "A crianca segura uma lanterna ou varinha simples, encantada.",
    },
    "birthday": {
        "costume": "roupa de festa infantil elegante (vestido ou camisa festa) com um chapeu de aniversario",
        "setting": "jardim de festa com bolo, balao e luzes quentes, fundo desfocado de festa",
        "action": "A crianca sorri em frente ao bolo, celebrando.",
    },
    "christmas": {
        "costume": "casaco de inverno aconchegante, listras natalinas suaves, luvas e gorro",
        "setting": "floresta nevada iluminada por lanternas e uma arvore decorada ao fundo",
        "action": "A crianca segura um presente embrulhado, com neve suave caindo.",
    },
    "easter": {
        "costume": "roupa primaveril clara, cesta de pascoa pequena na mao",
        "setting": "prado florido com ovos coloridos escondidos na grama e coelhos amigaveis",
        "action": "A crianca mostra a cesta, radiante.",
    },
    "childrens_day": {
        "costume": "roupa de brincar colorida e comoda, como heroi de parque de diversoes",
        "setting": "parque ensolarado com brinquedos, pipa no ceu e baloes ao fundo",
        "action": "A crianca corre ou acena, cheia de alegria.",
    },
    "mothers_day": {
        "costume": "roupa bonita de domingo, com um ramalhete de flores na mao",
        "setting": "cozinha/sala aconchegante de livro infantil, luz dourada pela janela",
        "action": "A crianca oferece as flores com um sorriso terno.",
    },
    "fathers_day": {
        "costume": "roupa de aventureiro leve combinando com um detalhe 'igual ao pai' (bone ou gravata folgada)",
        "setting": "oficina ou jardim iluminado, ferramentas de brincar e um ceu claro",
        "action": "A crianca segura uma ferramenta de brinquedo, orgulhosa.",
    },
    "new_year": {
        "costume": "roupa de festa brilhante e infantil, com uma faixa de ano novo discreta",
        "setting": "varanda noturna com fogos de artifício pintados suaves e luzes douradas",
        "action": "A crianca contempla os fogos, esperancosa.",
    },
    "alfabetizacao_inicial": {
        "costume": "roupa escolar confortavel, mochila pequena e um livro aberto nas maos",
        "setting": "biblioteca aconchegante de livro infantil, letras flutuando suavemente no ar",
        "action": "A crianca aponta para uma letra no livro, curiosa.",
    },
    "pensamento_matematico": {
        "costume": "avental de inventor infantil sobre roupa comoda, giz ou blocos nas maos",
        "setting": "sala-atelier com blocos coloridos, numeros suaves e uma lousa amigavel",
        "action": "A crianca monta uma torre de blocos, concentrada e feliz.",
    },
    "cores": {
        "costume": "avental de artista salpicado de tinta, pincel na mao",
        "setting": "jardim de flores vibrantes e potes de tinta, arco-iris suave no ceu",
        "action": "A crianca mostra a paleta de cores, encantada.",
    },
    "opostos_espacial": {
        "costume": "roupa de explorador indoor (colete e botas leves)",
        "setting": "quarto magico com portas grandes/pequenas, escadas para cima e para baixo",
        "action": "A crianca compara dois objetos de tamanhos opostos, brincando.",
    },
    "higiene_desfralde": {
        "costume": "pijama fresco ou roupa de banho infantil com toalha macia nos ombros",
        "setting": "banheiro alegre de livro infantil, espuma e borrachinhos, luz suave",
        "action": "A crianca sorri orgulhosa, pronta para o banho ou para se cuidar.",
    },
    "rotina_dormir": {
        "costume": "pijama aconchegante e pantufas, ursinho de pelucia no colo",
        "setting": "quarto noturno quente, abajur dourado, lua visivel na janela",
        "action": "A crianca se aconchega, sonolenta e segura.",
    },
    "alimentacao_saudavel": {
        "costume": "avental de pequeno chef, chapeu de cozinheiro infantil",
        "setting": "cozinha solarenga com frutas, hortaliças e uma tigela colorida",
        "action": "A crianca mostra um prato saudavel, orgulhosa.",
    },
    "vestir_autonomia": {
        "costume": "roupa do dia quase pronta, um sapato em cada mao ou casaco pela metade, de forma carinhosa",
        "setting": "quarto com guarda-roupa aberto, pecas coloridas e um espelho amigavel",
        "action": "A crianca escolhe a roupa sozinha, determinada e feliz.",
    },
    "literacia_emocional": {
        "costume": "roupa comoda do dia a dia ilustrada (nao a da foto), com um coracao bordado discreto",
        "setting": "jardim sereno ao entardecer, balanco e ceu em tons pastel",
        "action": "A crianca coloca a mao no peito, em paz, reconhecendo um sentimento.",
    },
    "consciencia_corporal": {
        "costume": "roupa de movimento (camiseta e calca folgada), pés descalços na grama",
        "setting": "prado ensolarado, a crianca em pose de alongamento suave",
        "action": "A crianca aponta para si mesma, descobrindo o proprio corpo com alegria.",
    },
    "compartilhar_revezar": {
        "costume": "roupa de brincar colorida, um brinquedo na mao estendida",
        "setting": "parquinho iluminado com dois brinquedos e um amigo de pelucia ao fundo",
        "action": "A crianca oferece o brinquedo, generosa.",
    },
    "animais_sons": {
        "costume": "roupa de pequeno naturalista: camisa, shorts e binoculo",
        "setting": "fazenda ou bosque com animais amigaveis (cachorro, passaro, vaca) ao redor",
        "action": "A crianca imita o som de um animal, rindo.",
    },
    "transporte_ajudantes": {
        "costume": "traje de ajudante (bombeiro, piloto ou construtor infantil), capacete proporcional",
        "setting": "oficina ou pista com um veiculo amigavel (caminhao, aviao ou barco) ao fundo",
        "action": "A crianca acena de perto do veiculo, como um heroi cotidiano.",
    },
    "clima_estacoes": {
        "costume": "casaco e botas de chuva amarelos, ou equivalente de estacao, com guarda-chuva",
        "setting": "rua de bairro sob chuva dourada e sol rompendo as nuvens, pocoes no chao",
        "action": "A crianca salta numa pocoa, encantada com o clima.",
    },
}


def _style_hint(style: str) -> str:
    return _STYLE_HINT.get((style or "").strip().lower(), _STYLE_HINT["realistic"])


def theme_staging(theme: str | None) -> ThemeStaging:
    """Devolve figurino + cenario do tema; fallback de aventura se o tema for desconhecido."""
    key = (theme or "adventure").strip().lower()
    return THEME_STAGING.get(key, _DEFAULT_STAGING)


def character_prompt(*, prompt: str, style: str) -> str:
    """Prompt completo enviado ao modelo para gerar o personagem a partir da foto."""
    return (
        f"{STYLE_BIBLE} {_style_hint(style)} {IDENTITY_FROM_PHOTO} "
        f"Crie o personagem ilustrado a partir das fotos de referencia. {prompt}"
    )


def identity_refine_prompt(*, style: str = "realistic") -> str:
    """Segundo passe: corrige so o rosto contra a foto, preservando figurino e cena."""
    return (
        f"{STYLE_BIBLE} {_style_hint(style)} "
        "Voce recebe DUAS imagens: (1) a FOTO real de uma crianca e (2) uma ILUSTRACAO "
        "dela. Ajuste APENAS o ROSTO da ilustracao para ficar o mais fiel possivel a "
        "foto: mesmo formato de rosto e bochechas, mesmos olhos (cor, formato e "
        "espacamento), mesmo nariz, mesma boca e sorriso, mesmas sobrancelhas, mesmo "
        "cabelo (cor, textura, comprimento, franja e risca), mesmo tom de pele e a "
        "mesma idade. Preserve o figurino, a pose e o fundo da ILUSTRACAO — nao copie "
        "a roupa nem o cenario da foto. Nao torne a imagem uma fotografia. Devolva "
        "apenas a ilustracao corrigida."
    )


def scene_prompt(*, prompt: str, style: str) -> str:
    """Prompt completo para redesenhar o character_ref numa nova cena."""
    return (
        f"{STYLE_BIBLE} {_style_hint(style)} {IDENTITY_FROM_CHARACTER} "
        "O que PODE mudar: pose, expressao, acao, enquadramento e cenario, conforme a "
        "cena descrita. Ilustre no mesmo DNA artistico da referencia (pintura digital "
        f"de livro infantil). Cena: {prompt}"
    )


def scene_refine_prompt(*, style: str = "realistic") -> str:
    """Segundo passe de cena: identidade do character_ref, sem redesenhar o cenario."""
    return (
        f"{STYLE_BIBLE} {_style_hint(style)} "
        "Voce recebe DUAS imagens: (1) o PERSONAGEM de referencia e (2) uma ILUSTRACAO "
        "de cena de um livro infantil. Sua unica tarefa e corrigir a identidade: "
        "redesenhe o protagonista da cena para ficar identico ao personagem de "
        "referencia no ROSTO, cabelo, tom de pele, idade e no figurino-base da "
        "referencia. Se o rosto ou o cabelo estiverem diferentes, a referencia SEMPRE "
        "vence. NAO mude o cenario, a composicao, o enquadramento, a iluminacao, a "
        "pose nem a acao da cena. Devolva apenas a cena corrigida."
    )


def avatar_prompt(*, theme: str | None, name: str = "", extra: bool = False) -> str:
    """Retrato tematico (figurino + cenario), equivalente aos cards do Tell My Tale."""
    staging = theme_staging(theme)
    who = f"o personagem '{name}'" if name else "o personagem principal"
    role = "coadjuvante da mesma historia" if extra else "protagonista"
    return (
        f"Retrato quadrado (1:1), meio corpo em 3/4, de {who} ({role}). "
        f"Vista-o com este figurino (NAO use a roupa da foto): {staging['costume']}. "
        "Coloque-o neste cenario tematico (NAO use fundo neutro nem o fundo da foto): "
        f"{staging['setting']}. {staging['action']} "
        "Iluminacao suave e direcionada, qualidade profissional de livro infantil premium."
    )


def realistic_prompt(*, theme: str | None) -> str:
    """Referencia de video: mesmo DNA artistico e figurino do tema."""
    staging = theme_staging(theme)
    return (
        f"{STYLE_BIBLE} {IDENTITY_FROM_PHOTO} "
        "Transform the photo of the child into the same premium children's-book digital "
        "painting used for the story avatar. Square-ish 3/4 portrait, soft directional "
        "light, painterly brush texture, luminous illustrated eyes, wholesome and "
        "enchanting. "
        f"Dress them in this costume (do NOT keep the photo outfit): {staging['costume']}. "
        f"Place them in this setting (do NOT use a blank backdrop): {staging['setting']}. "
        f"{staging['action']}"
    )


REALISTIC_NEGATIVE = (
    "photorealistic skin, photo collage, vinyl-toy proportions, oversized head, "
    "harsh black outlines, distorted face, extra fingers, text, watermark, "
    "copying the photo clothing or photo background"
)


def ebook_scene_prompt(*, page_idx: int, excerpt: str) -> str:
    """Wrapper da pagina do ebook: cena 1:1 no mesmo DNA, area calma para o texto."""
    return (
        f"Pagina {page_idx} da historia. Ilustre exatamente esta cena (contexto "
        "completo), com o personagem principal da imagem de referencia como "
        "protagonista. Mantenha o rosto identico a referencia e o figurino-base da "
        "referencia. Composicao QUADRADA (1:1), pintura digital quente e luminosa de "
        "livro infantil premium, luz suave; deixe uma area mais calma/limpa (ceu, "
        f"campo, parede) para receber o texto impresso. Trecho: {excerpt[:900]}"
    )


def keyframe_scene_prompt(*, scene_n: int, prompt: str) -> str:
    return (
        f"Keyframe {scene_n} para video, composicao cinematografica 16:9, pintura "
        "digital de livro infantil no mesmo DNA da referencia, mesmo protagonista e "
        f"figurino-base: {prompt[:600]}"
    )
