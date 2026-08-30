"""Handlers das etapas do pipeline.

Cada handler recebe (db, job), executa a etapa via ai_clients, persiste assets no
storage e avanca o estado do projeto. Exceptions ProviderError(transient=True)
sao reprocessadas pelo runner; demais erros -> FAILED + estorno.

Pre-condicoes entre etapas (ex.: ebook exige avatar+story) sao validadas aqui e,
quando faltam, levantam ProviderError(transient=False) -> falha definitiva clara.
"""  # pipeline v2 (livro estilo referencia)
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from io import BytesIO
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.ai_clients import get_image_provider, get_text_provider, get_video_provider
from app.ai_clients.base import ImageResult, ProviderError
from app.ai_clients.book_prompts import (
    AVATAR_PROMPT,
    CHARACTER_SHEET_PROMPT,
    EXPRESSION_SHEET_KEYS,
    EXPRESSION_SHEET_PROMPT,
    build_scene_prompt,
    costume_extras_for_template,
    costume_extras_for_theme,
    costume_lock_prompt,
    infer_expression,
    name_scene_extras_for_template,
    normalize_expression,
    normalize_shot,
    normalize_text_band,
    scene_extras_for_template,
)
from app.ai_clients.book_prompts import (
    STYLE as BOOK_STYLE,
)
from app.ai_clients.face_detect import face_reference, identity_images
from app.ai_clients.face_match import score_face_match
from app.ai_clients.identity_lock import (
    IDENTITY_MISMATCH_ERROR,
    FaceVerdict,
    IdentityLock,
    build_identity_lock,
    judge_identity,
    prefer_verdict,
    require_character_ref,
)
from app.config import settings
from app.models import Asset, AssetKind, Job, JobStatus, JobType, Project, ProjectStatus, UserVoice
from app.story_templates import (
    illustration_notes,
    page_layouts,
)
from app.workers import ebook as ebook_builder

logger = logging.getLogger("worker")


def _offline_png(label: str, *, palette: tuple[tuple[int, int, int], tuple[int, int, int]]) -> bytes:
    """Gera uma imagem local simples para fallback offline/demonstração.

    O objetivo não é reproduzir a qualidade do provedor, apenas manter o fluxo
    funcional quando a IA externa estiver indisponivel.
    """
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1024, 1024
    image = Image.new("RGB", (width, height), palette[0])
    draw = ImageDraw.Draw(image)

    # fundo com bloco suave e decoracoes simples
    draw.rounded_rectangle((64, 64, width - 64, height - 64), radius=48, fill=palette[1])
    draw.ellipse((120, 120, 420, 420), fill=(255, 255, 255))
    draw.ellipse((604, 120, 904, 420), fill=(255, 255, 255))
    draw.ellipse((260, 430, 764, 934), fill=(255, 255, 255))

    # personagem/ilustracao abstrata
    draw.ellipse((350, 260, 674, 584), fill=(246, 214, 170), outline=(80, 60, 50), width=6)
    draw.ellipse((410, 330, 470, 390), fill=(42, 42, 42))
    draw.ellipse((554, 330, 614, 390), fill=(42, 42, 42))
    draw.arc((460, 410, 564, 500), start=10, end=170, fill=(120, 60, 60), width=8)
    draw.rounded_rectangle((430, 600, 594, 820), radius=40, fill=(255, 232, 207))
    draw.line((430, 684, 360, 792), fill=(80, 60, 50), width=18)
    draw.line((594, 684, 664, 792), fill=(80, 60, 50), width=18)
    draw.line((470, 820, 430, 940), fill=(80, 60, 50), width=18)
    draw.line((554, 820, 594, 940), fill=(80, 60, 50), width=18)

    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except Exception:
        font = ImageFont.load_default()
    draw.rounded_rectangle((168, 854, 856, 948), radius=28, fill=(255, 255, 255))
    draw.text((192, 874), label[:44], fill=(30, 30, 30), font=font)

    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _offline_gif(label: str) -> bytes:
    """Video fallback local em GIF animado para exibição no navegador."""
    from PIL import Image, ImageDraw, ImageFont

    frames = []
    colors = [
        ((221, 236, 255), (255, 250, 240)),
        ((255, 237, 222), (255, 248, 244)),
        ((234, 245, 228), (250, 250, 245)),
    ]
    try:
        font = ImageFont.truetype("arial.ttf", 38)
    except Exception:
        font = ImageFont.load_default()

    for idx, (bg, panel) in enumerate(colors):
        frame = Image.new("RGB", (960, 540), bg)
        draw = ImageDraw.Draw(frame)
        draw.rounded_rectangle((40, 40, 920, 500), radius=36, fill=panel)
        draw.ellipse((110 + idx * 30, 135, 350 + idx * 30, 375), fill=(246, 214, 170))
        draw.ellipse((210 + idx * 30, 230, 255 + idx * 30, 275), fill=(40, 40, 40))
        draw.ellipse((285 + idx * 30, 230, 330 + idx * 30, 275), fill=(40, 40, 40))
        draw.arc((235 + idx * 30, 280, 305 + idx * 30, 345), start=15, end=165, fill=(120, 60, 60), width=6)
        draw.rounded_rectangle((530, 170, 840, 330), radius=28, fill=(255, 255, 255), outline=(170, 180, 190), width=4)
        draw.text((560, 205), label[:24], fill=(34, 42, 54), font=font)
        draw.text((560, 255), f"Cena {idx + 1}", fill=(84, 98, 112), font=font)
        frames.append(frame)

    buf = BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=700,
        loop=0,
        disposal=2,
    )
    return buf.getvalue()


def _offline_video_bytes(label: str) -> bytes:
    """Retorno de fallback para video offline.

    Mantem o fluxo funcionando sem depender de codificadores externos.
    O UI trata a URL assinada normal; aqui retornamos um pequeno placeholder
    textual em vez de um mp4 real quando o ambiente nao consegue gerar video.
    """
    return (
        f"Fallback offline do video indisponivel para: {label}\n"
        "Use o provedor configurado para gerar o mp4 real quando houver acesso.\n"
    ).encode()


# --------------------------------------------------------------------------- #
# Guias educativos por tema: (o que a história ensina, sequência lógica da jornada)
# --------------------------------------------------------------------------- #
THEME_EDU: dict[str, dict[str, tuple[str, str]]] = {
    "pt": {
        "adventure": (
            "exploração e orientação: como usar um mapa, os pontos cardeais e o respeito à natureza",
            "preparar a mochila e o mapa → seguir a trilha lendo o mapa → atravessar um obstáculo "
            "da natureza (rio, colina) com uma ideia inteligente → a grande descoberta → voltar "
            "para casa e contar o que aprendeu",
        ),
        "princess": (
            "empatia, gentileza e cuidado com os outros: um reino funciona quando todos se ajudam",
            "um pedido de ajuda chega ao castelo → a jornada pelos jardins e vilarejos → ajudar "
            "dois moradores com gentileza (cada um ensina algo) → resolver o problema do reino no "
            "clímax → festa no castelo e a lição de cuidar dos outros",
        ),
        "superhero": (
            "responsabilidade, hábitos saudáveis e trabalho em equipe: herói de verdade treina, "
            "ajuda e também pede ajuda",
            "descobrir um talento especial → treinar com dedicação (comer bem, dormir, praticar) → "
            "surgir um problema na vizinhança → resolver com inteligência e trabalho em equipe → "
            "celebração e a lição de que ajudar é o maior superpoder",
        ),
        "space": (
            "astronomia para crianças: a Lua, os planetas, as estrelas e a gravidade (tudo flutua!)",
            "preparar o foguete e a contagem regressiva → chegar à Lua e flutuar (gravidade "
            "fraquinha) → visitar um planeta colorido (com um fato real sobre ele) → admirar as "
            "estrelas → voltar à Terra com saudade e conhecimento novo",
        ),
        "underwater": (
            "vida marinha: recifes de coral são casas de peixinhos, tartarugas sobem para "
            "respirar, golfinhos conversam por sons",
            "o mergulho começa na praia → conhecer o recife de corais e seus moradores → um "
            "amiguinho marinho em apuros → travessia da correnteza com uma ideia esperta → "
            "resgate e festa no recife → volta à praia ao entardecer",
        ),
        "dinosaurs": (
            "paleontologia para crianças: espécies reais e suas características (braquiossauro de "
            "pescoço comprido come plantas, tricerátopo tem três chifres, pterossauro plana no "
            "vento) e o que são fósseis",
            "encontrar uma pegada ou fóssil misterioso → chegar ao vale dos dinossauros → conhecer "
            "três espécies (um fato divertido sobre cada uma) → ajudar um filhote perdido a voltar "
            "ao ninho → despedida e volta para casa guardando um tesourinho da aventura",
        ),
        "fantasy": (
            "segredos da natureza com um toque de magia: vaga-lumes brilham para conversar, "
            "cogumelos ajudam a floresta, plantas precisam de cuidado para crescer",
            "a entrada na floresta encantada → um ser mágico pede ajuda → duas boas ações no "
            "caminho (cada uma revela um segredo da natureza) → a floresta inteira se ilumina no "
            "clímax → a lição de que a gentileza ilumina o mundo",
        ),
        # ---- Datas comemorativas ----
        "birthday": (
            "celebração, gratidão e o valor de crescer: cada ano novo é uma página em branco "
            "para preencher com aventuras e boas memórias",
            "acordar no dia especial e sentir a magia no ar → preparar surpresas para os amigos → "
            "uma aventura divertida com obstáculos engraçados → a festa surpresa no clímax → "
            "aprender que o melhor presente é ter quem a gente ama por perto",
        ),
        "christmas": (
            "generosidade, união familiar e espírito natalino: dar é melhor que receber, "
            "e a magia está nas pequenas coisas",
            "ajudar a decorar a casa e a árvore → uma aventura para encontrar o presente "
            "perfeito → encontrar alguém que precisa de ajuda → a ceia de Natal reunindo "
            "todos → a lição de que o espírito do Natal está no coração",
        ),
        "easter": (
            "esperança, renascimento e alegria de descobrir coisas novas: como os "
            "pintinhos nascem e as flores voltam a brotar",
            "pela manhã, encontrar os primeiros ovos escondidos → seguir pistas pelo "
            "jardim → ajudar um filhote perdido a encontrar o ninho → a grande festa "
            "de Páscoa com todos os amigos → aprender que depois do inverno sempre vem "
            "a primavera",
        ),
        "childrens_day": (
            "a importância de ser criança: brincar, imaginar e sonhar são os "
            "superpoderes mais poderosos do mundo",
            "acordar sabendo que hoje é o dia especial → escolher a brincadeira "
            "perfeita → uma aventura onde a imaginação se torna realidade → compartilhar "
            "alegria com todos os amigos → aprender que ser criança é o maior presente",
        ),
        "mothers_day": (
            "gratidão, amor incondicional e o valor de cuidar uns dos outros: "
            "mamãe é quem nos ensina a amar",
            "acordar cedo para preparar uma surpresa → uma aventura para encontrar "
            "o presente perfeito → ajudar alguém no caminho → entregar o presente "
            "com um abraço → aprender que o melhor presente é o amor",
        ),
        "fathers_day": (
            "gratidão, coragem e o valor de ter um herói ao nosso lado: papai "
            "nos ensina a ser fortes e gentis",
            "acordar com uma ideia especial para o papai → uma aventura onde "
            "aprendemos algo que ele adora → encontrar um presente que representa "
            "nossa admiração → entregar com orgulho → aprender que papai é nosso "
            "maior herói",
        ),
        "new_year": (
            "novos começos, esperança e o poder de sonhar alto: cada ano novo "
            "é uma página em branco para escrever nossa história",
            "contar os últimos segundos do ano → fazer um pedido especial → "
            "uma aventura simbólica representando o novo ano → compartilhar "
            "alegria com a família → aprender que novos sonhos trazem "
            "novas possibilidades",
        ),
    },
    "en": {
        "adventure": (
            "exploration and orientation: how to read a map, the cardinal directions and respect for nature",
            "pack the backpack and map → follow the trail reading the map → cross a natural "
            "obstacle (river, hill) with a clever idea → the big discovery → return home and share "
            "what was learned",
        ),
        "princess": (
            "empathy, kindness and caring for others: a kingdom works when everyone helps",
            "a call for help reaches the castle → a journey through gardens and villages → help two "
            "villagers with kindness (each teaches something) → solve the kingdom's problem at the "
            "climax → castle celebration and the lesson of caring for others",
        ),
        "superhero": (
            "responsibility, healthy habits and teamwork: a real hero trains, helps and also asks for help",
            "discover a special talent → train with dedication (eat well, sleep, practice) → a "
            "problem appears in the neighborhood → solve it with cleverness and teamwork → "
            "celebration and the lesson that helping is the greatest superpower",
        ),
        "space": (
            "astronomy for kids: the Moon, the planets, the stars and gravity (everything floats!)",
            "prepare the rocket and the countdown → reach the Moon and float (weak gravity) → visit "
            "a colorful planet (with one real fact about it) → admire the stars → return to Earth "
            "with new knowledge",
        ),
        "underwater": (
            "marine life: coral reefs are homes for fish, turtles surface to breathe, dolphins talk "
            "through sounds",
            "the dive starts at the beach → meet the coral reef and its residents → a little sea "
            "friend in trouble → cross the current with a clever idea → rescue and reef celebration "
            "→ back to the beach at sunset",
        ),
        "dinosaurs": (
            "paleontology for kids: real species and their traits (long-necked Brachiosaurus eats "
            "plants, Triceratops has three horns, Pterosaurs glide on the wind) and what fossils are",
            "find a mysterious footprint or fossil → arrive at the dinosaur valley → meet three "
            "species (one fun fact about each) → help a lost hatchling back to its nest → farewell "
            "and journey home keeping a little treasure from the adventure",
        ),
        "fantasy": (
            "nature's secrets with a touch of magic: fireflies glow to talk, mushrooms help the "
            "forest, plants need care to grow",
            "enter the enchanted forest → a magical creature asks for help → two good deeds along "
            "the way (each reveals a secret of nature) → the whole forest lights up at the climax → "
            "the lesson that kindness lights up the world",
        ),
        # ---- Special dates ----
        "birthday": (
            "celebration, gratitude and the value of growing up: each new year is a blank page "
            "to fill with adventures and happy memories",
            "wake up on the special day and feel the magic in the air → prepare surprises for "
            "friends → a fun adventure with silly obstacles → the surprise party at the climax → "
            "learn that the best gift is having loved ones around",
        ),
        "christmas": (
            "generosity, family unity and the Christmas spirit: giving is better than receiving, "
            "and magic lives in small things",
            "help decorate the house and tree → an adventure to find the perfect gift → find "
            "someone who needs help → the Christmas dinner bringing everyone together → the "
            "lesson that the Christmas spirit lives in the heart",
        ),
        "easter": (
            "hope, renewal and the joy of discovering new things: how chicks hatch and flowers "
            "bloom again",
            "wake up to find the first hidden eggs → follow clues through the garden → help a "
            "lost chick find its nest → the big Easter celebration with all friends → learn that "
            "after winter always comes spring",
        ),
        "childrens_day": (
            "the importance of being a child: playing, imagining and dreaming are the most "
            "powerful superpowers in the world",
            "wake up knowing today is the special day → choose the perfect game → an adventure "
            "where imagination becomes reality → share joy with all friends → learn that being "
            "a child is the greatest gift",
        ),
        "mothers_day": (
            "gratitude, unconditional love and the value of caring for each other: mom teaches "
            "us how to love",
            "wake up early to prepare a surprise → an adventure to find the perfect gift → help "
            "someone along the way → deliver the gift with a hug → learn that the best gift is love",
        ),
        "fathers_day": (
            "gratitude, courage and the value of having a hero by our side: dad teaches us to "
            "be strong and kind",
            "wake up with a special idea for dad → an adventure where we learn something he loves "
            "→ find a gift that represents our admiration → deliver it with pride → learn that dad "
            "is our greatest hero",
        ),
        "new_year": (
            "new beginnings, hope and the power of dreaming big: each new year is a blank page "
            "to write our story",
            "count down the last seconds of the year → make a special wish → a symbolic adventure "
            "representing the new year → share joy with family → learn that new dreams bring "
            "new possibilities",
        ),
    },
}


# --------------------------------------------------------------------------- #
# Objetivos educacionais estruturados: foco, vilão, cenário e sequência da jornada.
# Usado por handle_story() para compor o brief com informações granulares.
# --------------------------------------------------------------------------- #
LEARNING_GOALS: dict[str, dict[str, dict[str, str]]] = {
    "pt": {
        # ---- Linguagem & Conceitos Fundamentais ----
        "alfabetizacao_inicial": {
            "foco": "consciência fonêmica: o alfabeto, rimas e a leitura da esquerda para a direita",
            "vilao": "a Timidez, que faz a criança guardar as palavras só para si",
            "espaco": "um cantinho de leitura cheio de livros e letras coloridas",
            "sequencia": (
                "encontrar uma letra ou palavra misteriosa → seguir pistas rimadas pela "
                "casa → a Timidez tenta calar a criança bem na hora de dizer a palavra em "
                "voz alta → a criança usa a curiosidade para soletrar e ler mesmo com medo "
                "→ celebrar lendo a palavra inteira para todos"
            ),
        },
        "pensamento_matematico": {
            "foco": "contar de 1 a 5, separar por tamanho e reconhecer círculo, quadrado e triângulo",
            "vilao": "a Pressa, que faz contar errado e pular números",
            "espaco": "um quarto ou quintal cheio de blocos, brinquedos e formas para organizar",
            "sequencia": (
                "objetos espalhados pedem para ser organizados → contar um a um devagar → "
                "a Pressa tenta atropelar a contagem → a criança respira e conta de novo, "
                "com calma → tudo organizado por tamanho e forma, missão cumprida"
            ),
        },
        "cores": {
            "foco": "cores primárias e secundárias, reconhecidas em objetos do mundo real",
            "vilao": "a Confusão, que embaralha as cores na cabeça da criança",
            "espaco": "um jardim ou caixa de tintas cheio de cores para nomear",
            "sequencia": (
                "algo perdeu a cor certa e precisa ser combinado → percorrer o espaço "
                "nomeando cores em objetos conhecidos → a Confusão troca as cores de lugar "
                "→ a criança usa o que já sabe (o que é amarelo? o que é azul?) para desfazer "
                "a troca → tudo com a cor certa de novo"
            ),
        },
        "opostos_espacial": {
            "foco": "grande/pequeno, em cima/embaixo, dentro/fora",
            "vilao": "o Embolado, um sentimento de estar perdido no espaço",
            "espaco": "uma casa ou parquinho com cantos altos, baixos, dentro e fora bem marcados",
            "sequencia": (
                "algo precisa ser guardado ou encontrado no lugar certo → explorar o "
                "espaço nomeando opostos a cada passo → o Embolado confunde as direções → a "
                "criança usa os opostos como mapa (não é embaixo, é em cima!) → encontra o "
                "caminho certo"
            ),
        },
        # ---- Habilidades de Vida & Rotinas Diárias ----
        "higiene_desfralde": {
            "foco": "a transição do banheiro, lavar as mãos e escovar os dentes em passos previsíveis",
            "vilao": "a Vergonha, que faz esconder quando precisa ir ao banheiro",
            "espaco": "o banheiro de casa, arrumado e acolhedor",
            "sequencia": (
                "a criança sente que precisa ir ao banheiro → a Vergonha sussurra para "
                "esconder o sinal → a criança nomeia o que sente e pede ajuda → consegue "
                "sozinha, passo a passo (calça, sentar, papel, descarga, lavar as mãos) → "
                "orgulho de ter conseguido"
            ),
        },
        "rotina_dormir": {
            "foco": "a ansiedade de separação e uma rotina calma antes de dormir",
            "vilao": "o Medo-do-Escuro, que aparece quando a luz apaga",
            "espaco": "o quarto da criança à noite, com uma luminária e um brinquedo favorito",
            "sequencia": (
                "o dia termina e chega a hora de dormir → passos da rotina (banho, pijama, "
                "escovar os dentes, história) → o Medo-do-Escuro aparece quando a luz apaga "
                "→ a criança nomeia o medo e acende a luminária/abraça o brinquedo → "
                "adormece tranquila"
            ),
        },
        "alimentacao_saudavel": {
            "foco": "grupos de alimentos, frutas e verduras, coragem para experimentar texturas novas",
            "vilao": "o Enjoo, que faz recusar tudo que é novo no prato",
            "espaco": "a cozinha ou horta de casa, colorida com frutas e legumes",
            "sequencia": (
                "aparece um alimento novo e diferente no prato ou na horta → o Enjoo "
                "encolhe o nariz da criança → a criança usa a curiosidade (cheirar, tocar, "
                "provar um pouquinho) para vencer o Enjoo → descobre um sabor novo → orgulho "
                "de ter experimentado"
            ),
        },
        "vestir_autonomia": {
            "foco": "identificar peças de roupa, botões, zíperes e sapatos, e vestir-se sozinho",
            "vilao": "a Impaciência, que quer que outra pessoa faça tudo",
            "espaco": "o guarda-roupa ou quarto, com roupas espalhadas para escolher",
            "sequencia": (
                "a criança precisa se vestir para algo especial → a Impaciência tenta fazer "
                "desistir no primeiro botão emperrado → a criança tenta de novo, devagar, "
                "peça por peça → consegue se vestir sozinha → orgulho de ter feito por "
                "conta própria"
            ),
        },
        # ---- Autoconsciência & Aprendizagem Socioemocional ----
        "literacia_emocional": {
            "foco": "nomear sentimentos grandes — raiva, tristeza, frustração, alegria",
            "vilao": "o sentimento grande do dia (Raiva, Tristeza ou Frustração), como personagem",
            "espaco": "um lugar familiar e calmo, como a sala de casa ou o pátio da escola",
            "sequencia": (
                "algo não sai como a criança queria → o sentimento grande aparece e cresce "
                "→ a criança tenta ignorá-lo, mas ele só cresce mais → a criança para, nomeia "
                "o que sente e respira fundo → o sentimento fica pequeno e vira aprendizado"
            ),
        },
        "consciencia_corporal": {
            "foco": "nomes das partes do corpo, o que elas fazem e limites espaciais básicos",
            "vilao": "o Desatento, que faz a criança não perceber o próprio corpo",
            "espaco": "um espaço de brincar livre, como o quintal ou a sala",
            "sequencia": (
                "uma brincadeira de imitação ou dança começa → cada parte do corpo entra em "
                "ação (mãos, pés, cabeça) → o Desatento tenta bagunçar os movimentos → a "
                "criança presta atenção no próprio corpo e acerta o ritmo → brincadeira "
                "concluída com orgulho"
            ),
        },
        "compartilhar_revezar": {
            "foco": "brincar em paralelo, dividir e esperar a vez com gentileza",
            "vilao": "o Ciúme, que não quer soltar o brinquedo",
            "espaco": "um parquinho ou sala de brincar com outra criança por perto",
            "sequencia": (
                "um amiguinho quer brincar com o mesmo brinquedo → o Ciúme aperta o brinquedo "
                "contra o peito → a criança sente o Ciúme, mas lembra como é bom brincar junto "
                "→ propõe revezar ou dividir → os dois brincam juntos e se divertem mais ainda"
            ),
        },
        # ---- Descoberta & Exploração do Mundo ----
        "animais_sons": {
            "foco": "nomes e sons de animais, e seus habitats (fazenda, oceano, selva)",
            "vilao": "o Silêncio-Enroscado, que embaralha os sons dos animais",
            "espaco": "uma fazenda, floresta ou aquário para visitar",
            "sequencia": (
                "um som de animal escapa e ninguém sabe de quem é → seguir o som até o "
                "habitat certo → o Silêncio-Enroscado tenta confundir o som com outro animal "
                "→ a criança escuta com atenção e acerta o animal e seu som → o habitat "
                "inteiro canta junto"
            ),
        },
        "transporte_ajudantes": {
            "foco": "veículos (caminhão, trem, avião) e figuras da comunidade (bombeiro, médico, carteiro)",
            "vilao": "a Pressa-Perdida, que atrapalha o caminho até o ajudante certo",
            "espaco": "uma rua ou cidade pequena com diferentes veículos passando",
            "sequencia": (
                "algo precisa ser entregue ou resolvido rápido → a criança escolhe o veículo "
                "certo para o trajeto → a Pressa-Perdida embaralha o caminho → a criança para, "
                "pensa e escolhe a rota certa com a ajuda de um profissional da comunidade → "
                "missão entregue com sucesso"
            ),
        },
        "clima_estacoes": {
            "foco": "padrões de clima (chuva, sol, neve) e a roupa certa para cada estação",
            "vilao": "o Friozinho-Sem-Aviso (ou Solzão-Repentino), que muda o tempo de repente",
            "espaco": "o quintal ou uma janela que mostra o tempo mudando",
            "sequencia": (
                "a criança se prepara para sair de um jeito → o tempo muda de repente → o "
                "vilão do clima brinca de confundir a roupa certa → a criança observa o céu e "
                "escolhe a roupa certa para a nova estação/clima → sai para brincar preparada "
                "e feliz"
            ),
        },
    },
    "en": {
        # ---- Language & Fundamental Concepts ----
        "alfabetizacao_inicial": {
            "foco": "phonemic awareness: the alphabet, rhymes and reading left to right",
            "vilao": "Shyness, who makes the child keep words to herself",
            "espaco": "a cozy reading corner full of books and colorful letters",
            "sequencia": (
                "a mysterious letter or word appears → follow rhyming clues around the house "
                "→ Shyness tries to silence the child right when it's time to say the word "
                "out loud → the child uses curiosity to spell and read despite the fear → "
                "celebrate by reading the whole word to everyone"
            ),
        },
        "pensamento_matematico": {
            "foco": "counting from 1 to 5, sorting by size and recognizing circles, squares and triangles",
            "vilao": "Hurry, who makes counting go wrong and skip numbers",
            "espaco": "a room or backyard full of blocks, toys and shapes to organize",
            "sequencia": (
                "scattered objects need organizing → count them one by one, slowly → Hurry "
                "tries to rush the counting → the child breathes and counts again, calmly → "
                "everything sorted by size and shape, mission complete"
            ),
        },
        "cores": {
            "foco": "primary and secondary colors, recognized in real-world objects",
            "vilao": "Confusion, who scrambles the colors in the child's mind",
            "espaco": "a garden or paint box full of colors to name",
            "sequencia": (
                "something lost its right color and needs matching → move through the space "
                "naming colors on familiar objects → Confusion swaps the colors around → the "
                "child uses what she already knows to undo the swap → everything has the "
                "right color again"
            ),
        },
        "opostos_espacial": {
            "foco": "big/small, up/down, inside/outside",
            "vilao": "the Muddle, a feeling of being lost in space",
            "espaco": "a house or playground with clearly marked high, low, inside and outside corners",
            "sequencia": (
                "something needs to be put away or found in the right spot → explore the "
                "space naming opposites at each step → the Muddle confuses the directions → "
                "the child uses opposites as a map → finds the right way"
            ),
        },
        # ---- Life Skills & Daily Routines ----
        "higiene_desfralde": {
            "foco": "the bathroom transition, handwashing and toothbrushing in predictable steps",
            "vilao": "Shame, who makes the child hide when she needs the bathroom",
            "espaco": "the home bathroom, tidy and welcoming",
            "sequencia": (
                "the child feels she needs the bathroom → Shame whispers to hide the signal "
                "→ the child names what she feels and asks for help → manages alone, step by "
                "step → pride in having done it"
            ),
        },
        "rotina_dormir": {
            "foco": "separation anxiety and a calm routine before sleep",
            "vilao": "Fear-of-the-Dark, who shows up when the light goes off",
            "espaco": "the child's bedroom at night, with a nightlight and a favorite toy",
            "sequencia": (
                "the day ends and bedtime arrives → routine steps (bath, pajamas, brushing "
                "teeth, story) → Fear-of-the-Dark appears when the light goes off → the "
                "child names the fear and turns on the nightlight or hugs the toy → falls "
                "asleep peacefully"
            ),
        },
        "alimentacao_saudavel": {
            "foco": "food groups, fruits and vegetables, courage to try new textures",
            "vilao": "Queasy, who makes the child refuse anything new on the plate",
            "espaco": "the kitchen or garden at home, colorful with fruits and vegetables",
            "sequencia": (
                "a new, different food appears on the plate or in the garden → Queasy "
                "scrunches up the child's nose → the child uses curiosity to overcome Queasy "
                "→ discovers a new flavor → pride in having tried it"
            ),
        },
        "vestir_autonomia": {
            "foco": "identifying clothing items, buttons, zippers and shoes, and dressing independently",
            "vilao": "Impatience, who wants someone else to do it all",
            "espaco": "the closet or bedroom, with clothes spread out to choose from",
            "sequencia": (
                "the child needs to get dressed for something special → Impatience tries to "
                "make her give up at the first stuck button → the child tries again, slowly, "
                "piece by piece → manages to dress herself → pride in doing it on her own"
            ),
        },
        # ---- Self-Awareness & Social-Emotional Learning ----
        "literacia_emocional": {
            "foco": "naming big feelings — anger, sadness, frustration, joy",
            "vilao": "the day's big feeling itself, as a character (Anger, Sadness or Frustration)",
            "espaco": "a familiar, calm place, like the living room or the school yard",
            "sequencia": (
                "something doesn't go as the child wanted → the big feeling appears and grows "
                "→ the child tries to ignore it, but it only grows more → the child stops, "
                "names what she feels and takes a deep breath → the feeling shrinks and "
                "becomes a lesson"
            ),
        },
        "consciencia_corporal": {
            "foco": "names of body parts, what they do and basic spatial limits",
            "vilao": "the Absent-Minded, who makes the child not notice her own body",
            "espaco": "a free-play space, like the backyard or living room",
            "sequencia": (
                "an imitation game or dance begins → each body part comes into action (hands, "
                "feet, head) → the Absent-Minded tries to mess up the movements → the child "
                "pays attention to her own body and gets the rhythm right → the game ends "
                "with pride"
            ),
        },
        "compartilhar_revezar": {
            "foco": "parallel play, sharing and waiting your turn with kindness",
            "vilao": "Jealousy, who won't let go of the toy",
            "espaco": "a playground or playroom with another child nearby",
            "sequencia": (
                "a friend wants to play with the same toy → Jealousy clutches the toy close "
                "→ the child feels Jealousy, but remembers how fun it is to play together → "
                "offers to take turns or share → the two play together and have even more fun"
            ),
        },
        # ---- Discovery & Exploring the World ----
        "animais_sons": {
            "foco": "animal names and sounds, and their habitats (farm, ocean, jungle)",
            "vilao": "the Tangled Silence, who scrambles the animal sounds",
            "espaco": "a farm, forest or aquarium to visit",
            "sequencia": (
                "an animal sound escapes and no one knows whose it is → follow the sound to "
                "the right habitat → the Tangled Silence tries to mix it up with another "
                "animal → the child listens carefully and matches the animal to its sound → "
                "the whole habitat sings along"
            ),
        },
        "transporte_ajudantes": {
            "foco": "vehicles (truck, train, plane) and community figures (firefighter, doctor, mail carrier)",
            "vilao": "Lost-in-a-Hurry, who muddles the way to the right helper",
            "espaco": "a street or small town with different vehicles passing by",
            "sequencia": (
                "something needs to be delivered or solved quickly → the child picks the "
                "right vehicle for the trip → Lost-in-a-Hurry scrambles the route → the "
                "child stops, thinks and picks the right path with a community helper's "
                "guidance → mission delivered successfully"
            ),
        },
        "clima_estacoes": {
            "foco": "weather patterns (rain, sun, snow) and the right clothing for each season",
            "vilao": "Sudden-Chill (or Sudden-Sun), who changes the weather without warning",
            "espaco": "the backyard or a window showing the weather changing",
            "sequencia": (
                "the child gets ready to go out one way → the weather suddenly changes → the "
                "weather villain plays tricks on the right outfit → the child looks at the "
                "sky and picks the right clothing for the new season → heads out to play, "
                "ready and happy"
            ),
        },
    },
}


def _project(db: Session, job: Job) -> Project:
    project = db.get(Project, job.project_id)
    if project is None:
        raise ProviderError("Projeto inexistente", transient=False)
    return project


def _set_status(db: Session, project: Project, status: ProjectStatus) -> None:
    project.status = status.value
    db.commit()


def _payload(job: Job) -> dict:
    return (job.result or {}).get("payload", {}) if job.result else {}


def _parse_title(story: str) -> str | None:
    """Extrai o título gerado pela IA (linha 'Título: ...' no começo da história)."""
    m = re.match(r"(?is)\s*t[íi]tulo\s*[:\-]\s*(.+?)\s*(?:\n|$)", story or "")
    if not m:
        return None
    title = m.group(1).strip().strip('"“”')
    return title[:120] or None


def _strip_title(story: str) -> str:
    """Remove a linha 'Título: ...' para que não vire página."""
    return re.sub(r"(?is)^\s*t[íi]tulo\s*[:\-].*?(?:\n+|$)", "", story or "", count=1)


def _parse_pages(story: str, limit: int = 200) -> list[str]:
    """Interpreta o texto enviado e divide em paginas para o e-book (sem limite fixo).

    Ordem:
      1) marcadores explicitos 'Pagina N:';
      2) paragrafos (linhas em branco) -> uma pagina por paragrafo;
      3) bloco unico -> agrupa ~2 frases por pagina.
    Usa TODA a historia (limite alto so como protecao). Cada item retornado e o
    TEXTO INTEGRAL daquele trecho (contexto completo para a ilustracao).
    """
    story = _strip_title((story or "").strip())
    # remove blocos de sugestao de imagem que a IA possa ter incluido,
    # ex.: "*(Imagem sugerida: ...)*" — nao devem virar pagina nem texto impresso
    story = re.sub(r"(?is)\*?\(\s*imagem[^)]*\)\*?", "", story).strip()
    if not story:
        return []

    # 1) marcadores "Pagina N:"
    parts = re.split(r"(?im)^\s*p[áa]gina\s*\d+\s*[:\-]", story)
    pages = [p.strip() for p in parts if p.strip()]

    # 2) paragrafos -> uma pagina por paragrafo
    if len(pages) <= 1:
        paras = [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip()]
        if len(paras) > 1:
            pages = paras

    # 3) bloco unico -> agrupa ~2 frases por pagina (sem forcar numero fixo)
    if len(pages) <= 1 and len(story) > 220:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", story) if s.strip()]
        if len(sentences) > 1:
            group = 2
            pages = [
                " ".join(sentences[i : i + group]) for i in range(0, len(sentences), group)
            ]

    return pages[:limit] or [story]


def _short_captions(pages: list[str]) -> list[str]:
    """Fallback local de resumo: 1a frase (ou trecho curto) de cada pagina."""
    out: list[str] = []
    for p in pages:
        p = (p or "").strip()
        first = re.split(r"(?<=[.!?])\s+", p)[0].strip() if p else ""
        if len(first) > 160:
            first = first[:157].rstrip() + "..."
        out.append(first or p[:120])
    return out


async def _project_photo_bytes(db: Session, project: Project) -> bytes | None:
    """Recorte do rosto da primeira foto do projeto, se existir.

    E a verdade do rosto em TODA pagina do livro, nao so no avatar: por isso usa
    a caixa detectada, e nao a janela geometrica que cortava a boca fora.
    """
    photos = db.scalars(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
        .order_by(Asset.created_at.desc())
    ).all()
    if not photos:
        return None
    try:
        raw = storage.get_bytes(photos[0].storage_key)
    except Exception:  # noqa: BLE001
        return None
    return await face_reference(raw)


# --------------------------------------------------------------------------- #
# Etapa 2-4: personagem
# --------------------------------------------------------------------------- #
async def handle_avatar(db: Session, job: Job) -> None:
    project = _project(db, job)
    _set_status(db, project, ProjectStatus.AVATAR_RUNNING)

    photos = db.scalars(
        select(Asset).where(
            Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value
        )
    ).all()
    if not photos:
        raise ProviderError("Sem fotos para gerar o personagem", transient=False)

    refs = [storage.get_bytes(a.storage_key) for a in photos]
    if settings.offline_fallback:
        result = ImageResult(
            image_bytes=_offline_png(
                f"Personagem de {project.child_name or 'demonstracao'}",
                palette=((245, 239, 229), (255, 247, 240)),
            ),
            mime_type="image/png",
            cost_usd=0.0,
        )
    else:
        # Personagem hibrido: generate_character + refine de identidade.
        provider = get_image_provider(job.provider)
        style = BOOK_STYLE
        gen_refs = (await identity_images(refs[0])) + refs[1:]
        face = gen_refs[0]
        try:
            result = await provider.generate_character(
                prompt=AVATAR_PROMPT,
                reference_images=gen_refs,
                style=style,
            )
        except ProviderError:
            result = await provider.generate_realistic(
                photo=face, prompt=AVATAR_PROMPT, style=style
            )
        result = await _refine_identity(provider, face, result, style, passes=2)

    key = storage.new_key(project.id, AssetKind.CHARACTER.value, _ext(result.mime_type))
    storage.put_bytes(key, result.image_bytes, result.mime_type)
    db.add(Asset(project_id=project.id, kind=AssetKind.CHARACTER.value, storage_key=key,
                 meta={"mime": result.mime_type}))
    project.character_ref = {"storage_key": key, "mime": result.mime_type}
    project.character_approved_at = None
    project.book_approved_at = None
    job.cost_usd = result.cost_usd
    _set_status(db, project, ProjectStatus.AVATAR_READY)


async def _refine_identity(
    provider, photo_bytes, result, style, *, retries: int = 0, passes: int = 1
):
    """Passe opcional: corrige o rosto para ficar mais fiel a foto, preservando o corpo desenhado.

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    `passes` = correcoes em sequencia (avatar usa 2).
    `retries` = tentativas extras apos falha em cada passe.
    """
    refine = getattr(provider, "refine_identity", None)
    if refine is None or not photo_bytes:
        return result
    extra = max(0, retries)
    for _ in range(max(1, passes)):
        attempt = 0
        while True:
            try:
                refined = await refine(
                    photo=photo_bytes, illustration=result.image_bytes, style=style
                )
                if refined and getattr(refined, "image_bytes", None):
                    result = refined
                break
            except Exception:  # noqa: BLE001 - refinamento e opcional
                if attempt < extra:
                    attempt += 1
                    continue
                break
    return result


async def _refine_scene(provider, character_ref, result, style, *, photo: bytes | None = None):
    """Passe opcional de cena: corrige o protagonista (foto = rosto, se houver).

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    `EBOOK_REFINE_SCENE=false` corta o segundo passe (nunca refina).
    Com o juiz ligado, quem dispara o refine e a nota de identidade — esta funcao
    so executa o passe quando o caller pede.
    """
    if not settings.ebook_refine_scene:
        return result
    refine = getattr(provider, "refine_scene", None)
    if refine is None or not character_ref:
        return result
    try:
        refined = await refine(
            character_ref=character_ref,
            scene=result.image_bytes,
            style=style,
            photo=photo,
        )
        if refined and getattr(refined, "image_bytes", None):
            return refined
    except TypeError:
        try:
            refined = await refine(
                character_ref=character_ref, scene=result.image_bytes, style=style
            )
            if refined and getattr(refined, "image_bytes", None):
                return refined
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001 - refinamento e opcional
        pass
    return result


async def handle_extra_character(db: Session, job: Job) -> None:
    """Gera o personagem ilustrado para cada foto de personagem extra enviada."""
    project = _project(db, job)
    extras = project.extra_characters or []
    if not extras:
        raise ProviderError("Sem personagens extras para gerar", transient=False)

    provider = get_image_provider(job.provider)
    updated = False

    for idx, ec in enumerate(extras):
        if ec.get("character_storage_key"):
            continue  # ja gerado
        photo_key = ec.get("storage_key")
        if not photo_key:
            continue
        photo_bytes = storage.get_bytes(photo_key)
        if settings.offline_fallback:
            result = ImageResult(
                image_bytes=_offline_png(
                    f"Personagem extra: {ec.get('name', idx + 1)}",
                    palette=((245, 239, 229), (255, 247, 240)),
                ),
                mime_type="image/png",
                cost_usd=0.0,
            )
        else:
            refs = await identity_images(photo_bytes)
            result = await provider.generate_character(
                prompt=f"Retrato do personagem '{ec.get('name', '')}', corpo inteiro, fundo neutro.",
                reference_images=refs,
                style=BOOK_STYLE,
            )
            result = await _refine_identity(provider, refs[0], result, BOOK_STYLE)
            extra_lock = build_identity_lock(
                character_ref=result.image_bytes,
                face_crop=refs[0],
                photo=photo_bytes,
            )
            verdict = await _judge_page(extra_lock, result.image_bytes)
            if not verdict.accepted(settings.ebook_face_match_min):
                result = await _refine_identity(
                    provider, refs[0], result, BOOK_STYLE, retries=1, passes=1
                )
                verdict = await _judge_page(extra_lock, result.image_bytes)
                if not verdict.accepted(settings.ebook_face_match_min):
                    raise ProviderError(
                        f"Personagem extra '{ec.get('name', idx + 1)}': "
                        f"{IDENTITY_MISMATCH_ERROR}",
                        transient=False,
                    )

        char_key = storage.new_key(project.id, "extra_character", _ext(result.mime_type))
        storage.put_bytes(char_key, result.image_bytes, result.mime_type)
        extras[idx]["character_storage_key"] = char_key
        extras[idx]["character_mime"] = result.mime_type
        updated = True

    if updated:
        project.extra_characters = extras
        db.commit()

    job.cost_usd = sum(
        e.get("cost_usd", 0.0) for e in extras if not e.get("character_storage_key")
    )


# Prompt fixo para a imagem hibrida (usada como referencia do video).
REALISTIC_PROMPT = (
    "Tell My Tale (TMT) style: transform this photo of a child into a hybrid "
    "children's-book character. FACE: photoreal digital painting of THIS child, "
    "camera quality with a slight painterly finish — more real than drawn "
    "(natural skin, lashes, iris, lips, hair strands; not a raw photo cutout, "
    "not cartoon). BODY: 3D storybook illustration (drawn neck, shoulders, arms). "
    "CLOTHES: illustrated story costume matching the scene (explorer, doctor, "
    "sailor, etc.) — do NOT copy the photo outfit. Identity from the photo "
    "wins over stylization: keep the child's exact facial features, eye size as the same "
    "fraction of the face as in the photo (if unsure, make eyes smaller, never larger), "
    "hair color and texture, skin tone, so they remain fully recognizable. "
    "Natural head proportions; no chibi; no doll eyes; no giant iris; "
    "no lens-flare covering the eye. Cinematic warm light, soft glow, rim light, "
    "magical atmosphere without enlarging the eyes for cuteness. Place "
    "them in a rich painterly storybook setting with depth, saturated color, and a "
    "dreamy bokeh background. High detail, wholesome, professional illustration "
    "quality. Portrait/3-4 view, vertical composition."
)
REALISTIC_NEGATIVE = (
    "photo collage, pasted face, fully cartoon face, raw unstyled photo face, "
    "heavy airbrush, same illustrated look on face and body, copying the photo outfit, "
    "overalls from the source photo, distorted face, extra fingers, "
    "text, watermark, harsh lighting, plastic doll skin, enlarged cartoon eyes, "
    "giant iris, doll eyes, cute oversized eyes, Pixar CGI, "
    "changing the child's facial identity."
)


async def handle_realistic(db: Session, job: Job) -> None:
    """Gera a imagem realistica a partir da foto (prompt fixo) e guarda no banco.

    Endpoint legado. O vídeo usa o avatar 3D (character_ref) ou o keyframe da cena.
    """
    project = _project(db, job)
    photos = db.scalars(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.PHOTO.value)
        .order_by(Asset.created_at.desc())
    ).all()
    if not photos:
        raise ProviderError("Sem foto para gerar a imagem realistica", transient=False)

    photo_bytes = storage.get_bytes(photos[0].storage_key)
    provider = get_image_provider(job.provider)
    result = await provider.generate_realistic(
        photo=photo_bytes, prompt=REALISTIC_PROMPT, negative=REALISTIC_NEGATIVE, style="realistic"
    )
    result = await _refine_identity(provider, photo_bytes, result, "realistic")

    key = storage.new_key(project.id, AssetKind.REALISTIC.value, _ext(result.mime_type))
    storage.put_bytes(key, result.image_bytes, result.mime_type)
    db.add(
        Asset(
            project_id=project.id,
            kind=AssetKind.REALISTIC.value,
            storage_key=key,
            meta={"mime": result.mime_type, "use": "video_reference"},
        )
    )
    job.cost_usd = result.cost_usd
    db.commit()


def _kling_configured() -> bool:
    return bool(settings.kling_access_key and settings.kling_secret_key)


def _use_video_offline() -> bool:
    """GIF offline quando não há chaves Kling; com chaves, sempre usa o provedor real."""
    return not _kling_configured()


def _clamp_kling_duration(duration_s: int) -> int:
    """Kling aceita apenas 5s ou 10s."""
    return 10 if int(duration_s) >= 8 else 5


def _video_reference_key(db: Session, project: Project, *, scene_n: int = 1) -> str:
    """Imagem base da animação: keyframe da cena, senão o avatar 3D (character_ref)."""
    page_assets = db.scalars(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.PAGE_IMAGE.value)
        .order_by(Asset.created_at.desc())
    ).all()
    for asset in page_assets:
        meta = asset.meta or {}
        if meta.get("keyframe") == scene_n:
            return asset.storage_key

    if project.character_ref and project.character_ref.get("storage_key"):
        return project.character_ref["storage_key"]
    raise ProviderError(
        "Imagem de referencia ausente: gere e aprove o personagem antes",
        transient=False,
    )


# --------------------------------------------------------------------------- #
# Etapa 5-8: historia
# --------------------------------------------------------------------------- #
async def handle_story(db: Session, job: Job) -> None:
    project = _project(db, job)
    _set_status(db, project, ProjectStatus.STORY_RUNNING)

    theme = project.theme or "adventure"
    extra_theme = (project.extra_theme or "").strip() or None
    if extra_theme == theme:
        extra_theme = None
    name = (project.child_name or "").strip()
    language = project.language or "pt-BR"
    is_en = (language or "").lower().startswith("en")
    if is_en:
        who = f"the child named {name}" if name else "the child from the photo"
        brief = (_payload(job).get("brief")
                 or f"Invent an ORIGINAL, coherent story in the theme '{theme}': give {who} "
                    "a small goal or problem, a journey with one or two obstacles and friends "
                    "who help, a gentle climax and a warm ending with a subtle lesson (courage, "
                    f"friendship or kindness). {who} is the hero from beginning to end."
                    + (f" Use the name '{name}' for the hero throughout the whole story." if name else ""))
    else:
        who = f"a crianca chamada {name}" if name else "o personagem da foto"
        brief = (_payload(job).get("brief")
                 or f"Invente uma historia ORIGINAL e coerente no tema '{theme}': de a {who} "
                    "um pequeno objetivo ou problema, uma jornada com um ou dois obstaculos e "
                    "amiguinhos que ajudam, um climax gentil e um final acolhedor com uma licao "
                    f"sutil (coragem, amizade ou gentileza). {who} e o protagonista do inicio ao fim."
                    + (f" Use o nome '{name}' como protagonista ao longo de toda a historia." if name else ""))

    # Guia educativo do tema: foco, vilão, cenário e sequência da jornada.
    # Prioriza LEARNING_GOALS (temas educacionais estruturados); senão usa THEME_EDU
    # (aventura/datas comemorativas — foco e sequência embutidos nas strings).
    lang_key = "en" if is_en else "pt"
    goals = LEARNING_GOALS.get(lang_key, {}).get(theme)
    guides = THEME_EDU[lang_key]
    if goals:
        # Tema educacional estruturado: campos separados
        focus = goals["foco"]
        vilao = goals.get("vilao", "")
        espaco = goals.get("espaco", "")
        sequence = goals["sequencia"]
        if is_en:
            brief += (
                " LEARNING (essential): the story must playfully TEACH — " + focus + "."
            )
            if vilao:
                brief += f" The villain is {vilao}."
            if espaco:
                brief += f" Setting: {espaco}."
            brief += (
                " Weave 2 or 3 REAL, simple, age-appropriate facts about the theme into "
                "the action or dialogue (never lecture-like). MANDATORY LOGICAL SEQUENCE "
                "of the journey, adapted creatively: " + sequence +
                ". At the end, the hero happily realizes what they learned."
            )
        else:
            brief += (
                " APRENDIZADO (essencial): a história deve ENSINAR de forma lúdica — "
                + focus + "."
            )
            if vilao:
                brief += f" O vilão da jornada é {vilao}."
            if espaco:
                brief += f" Cenário: {espaco}."
            brief += (
                " Insira 2 ou 3 curiosidades REAIS, simples e adequadas à idade sobre "
                "o tema dentro da ação ou das falas (nunca em tom de aula). SEQUÊNCIA "
                "LÓGICA obrigatória da jornada, adaptada com criatividade: " + sequence +
                ". No final, o protagonista percebe com alegria o que aprendeu."
            )
    else:
        # Aventura/datas comemorativas: foco e sequência embutidos na string
        focus, sequence = guides.get(theme, guides["adventure"])
        if is_en:
            brief += (
                " LEARNING (essential): the story must playfully TEACH — " + focus +
                ". Weave 2 or 3 REAL, simple, age-appropriate facts about the theme into "
                "the action or dialogue (never lecture-like). MANDATORY LOGICAL SEQUENCE "
                "of the journey, adapted creatively: " + sequence +
                ". At the end, the hero happily realizes what they learned."
            )
        else:
            brief += (
                " APRENDIZADO (essencial): a história deve ENSINAR de forma lúdica — "
                + focus +
                ". Insira 2 ou 3 curiosidades REAIS, simples e adequadas à idade sobre "
                "o tema dentro da ação ou das falas (nunca em tom de aula). SEQUÊNCIA "
                "LÓGICA obrigatória da jornada, adaptada com criatividade: " + sequence +
                ". No final, o protagonista percebe com alegria o que aprendeu."
            )

    # Segundo tema opcional (máx. 2 por história): o tema principal continua com o
    # vilão/cenário/arco (sequência acima); o segundo tema só soma um objetivo de
    # aprendizado extra tecido na mesma jornada — nunca uma jornada paralela.
    if extra_theme:
        extra_goals = LEARNING_GOALS.get(lang_key, {}).get(extra_theme)
        extra_edu = guides.get(extra_theme)
        if extra_goals:
            extra_focus = extra_goals["foco"]
        elif extra_edu:
            extra_focus, _ = extra_edu
        else:
            extra_focus = None

        if extra_focus:
            if is_en:
                brief += (
                    " SECOND THEME (blend into the same journey, never a separate plot): "
                    "also playfully teach — " + extra_focus + ". Keep the primary theme's "
                    "setting, sequence and pace as the backbone; weave this second learning "
                    "goal into an existing beat of that same journey (a detail of the "
                    "setting, something a friend says or does, a small moment inside the "
                    "obstacle already planned) instead of adding a new scene. If each theme "
                    "implies a different villain, pick whichever fits this specific journey "
                    "better, or merge them into one coherent antagonist — never two separate "
                    "villains in the same story."
                )
            else:
                brief += (
                    " SEGUNDO TEMA (funda com a mesma jornada, nunca um enredo à parte): "
                    "ensine também, de forma lúdica — " + extra_focus + ". Mantenha o "
                    "espaço, a sequência e o ritmo do tema principal como espinha dorsal; "
                    "teça esse segundo objetivo de aprendizado dentro de um momento já "
                    "previsto dessa mesma jornada (um detalhe do cenário, algo que um "
                    "amiguinho diz ou faz, um instante dentro do obstáculo já planejado) "
                    "em vez de criar uma cena nova. Se cada tema sugerir um vilão "
                    "diferente, escolha o que fizer mais sentido para essa jornada "
                    "específica, ou funda os dois num só antagonista coerente — nunca dois "
                    "vilões separados na mesma história."
                )

    # Perfil educativo da criança: o traço central (o que a história transforma) e o
    # interesse/talento (a ferramenta que o herói usa para superar o vilão no clímax).
    trait = (project.child_trait or "").strip()
    interest = (project.child_interest or "").strip()
    if trait or interest:
        if is_en:
            brief += (
                " CHILD PROFILE (use it to shape the plot): "
                + (f"the hero's starting trait is '{trait}' — this is the story's starting "
                   f"point, exactly what the journey transforms into growth. " if trait else "")
                + (f"the hero's talent/interest is '{interest}' — this is the tool the hero "
                   f"uses to name, calm or overcome the villain at the climax; never let an "
                   f"adult or luck solve it instead. " if interest else "")
            )
        else:
            brief += (
                " PERFIL DA CRIANÇA (use para moldar o enredo): "
                + (f"o traço inicial do herói é '{trait}' — esse é o ponto de partida da "
                   f"história, exatamente o que a jornada transforma em crescimento. " if trait else "")
                + (f"o talento/interesse do herói é '{interest}' — é a ferramenta que ele usa "
                   f"para nomear, acalmar ou superar o vilão no clímax; nunca deixe um adulto "
                   f"ou a sorte resolverem por ele. " if interest else "")
            )

    provider = get_text_provider(job.provider)
    result = await provider.generate_story(
        brief=brief, style=BOOK_STYLE, pages=settings.ebook_pages,
        language=language, age=project.child_age,
    )
    project.story_text = result.text
    job.cost_usd = result.cost_usd
    _set_status(db, project, ProjectStatus.STORY_READY)

    # Em background: agenda o roteiro completo (storyboard) para o vídeo futuro.
    _enqueue_auto_storyboard(db, project, job)


def _enqueue_auto_storyboard(db: Session, project: Project, source_job: Job) -> None:
    """Agenda em background (sem custo) o roteiro completo do vídeo para este projeto.

    Idempotente por job de história: reprocessar o STORY não duplica o storyboard.
    """
    key = f"auto-storyboard-{source_job.id}"
    if db.scalar(select(Job).where(Job.idempotency_key == key)):
        return
    db.add(
        Job(
            project_id=project.id,
            type=JobType.STORYBOARD.value,
            status=JobStatus.PENDING.value,
            provider=settings.text_provider,
            idempotency_key=key,
            cost_credits=0,
            result={"payload": {"auto": True}},
        )
    )
    db.commit()


def _catalog_template_id(db: Session, project: Project) -> str | None:
    """template_id se a história veio do catálogo (último job STORY)."""
    job = db.scalar(
        select(Job)
        .where(
            Job.project_id == project.id,
            Job.type == JobType.STORY.value,
            Job.status == JobStatus.DONE.value,
        )
        .order_by(Job.created_at.desc())
    )
    if job is None or not isinstance(job.result, dict):
        return None
    if job.result.get("source") != "template":
        return None
    tid = (job.result.get("template_id") or "").strip()
    return tid or None


def _book_costume_line(
    briefs: list[dict], template_id: str | None, theme: str | None
) -> str:
    for brief in briefs:
        line = (brief.get("costume") or "").strip()
        if line:
            return line
    return costume_extras_for_template(template_id) or costume_extras_for_theme(theme)


def _scene_to_brief(sc: dict, page_text: str, *, page_index: int = 0) -> dict:
    """Normaliza uma cena de storyboard num brief de pagina do ebook."""
    scene = (
        str(sc.get("scene") or "").strip()
        or str(sc.get("action") or "").strip()
        or str(sc.get("setting") or "").strip()
        or str(sc.get("image_prompt") or "").strip()
        or page_text
    )
    expression = normalize_expression(
        sc.get("expression") or sc.get("mood") or infer_expression(page_text, scene)
    )
    band = sc.get("text_band") or ("top" if page_index % 2 == 0 else "bottom")
    return {
        "n": int(sc.get("n") or page_index + 1),
        "scene": scene,
        "expression": expression,
        "shot": normalize_shot(sc.get("shot")),
        "costume": str(sc.get("costume") or "").strip(),
        "text_band": normalize_text_band(band),
    }


def _fallback_page_briefs(
    pages: list[str],
    *,
    notes: list[str] | None = None,
    costume: str = "",
    layouts: list[str] | None = None,
) -> list[dict]:
    briefs = []
    for i, page in enumerate(pages):
        note = notes[i] if notes and i < len(notes) else ""
        scene = (note or page).strip()
        layout = layouts[i] if layouts and i < len(layouts) else "story"
        briefs.append({
            "n": i + 1,
            "scene": scene,
            "expression": infer_expression(page, note),
            "shot": "wide" if layout == "name" else "medium",
            "costume": costume,
            "text_band": "left" if layout == "name" else (
                "top" if i % 2 == 0 else "bottom"
            ),
        })
    return briefs


def _save_storyboard_asset(
    db: Session, project: Project, sb: dict, *, auto: bool
) -> None:
    key = storage.new_key(project.id, AssetKind.STORYBOARD.value, "json")
    storage.put_bytes(
        key, json.dumps(sb, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
    )
    db.add(Asset(
        project_id=project.id,
        kind=AssetKind.STORYBOARD.value,
        storage_key=key,
        meta={"scenes": len(sb.get("scenes") or []), "auto": auto},
    ))
    db.commit()


async def _compose_storyboard(
    db: Session,
    project: Project,
    pages: list[str],
    *,
    title: str,
    theme_combined: str,
    language: str,
    auto: bool = False,
    require_ai: bool = False,
) -> dict:
    """Carrega o storyboard se bater com as paginas; senao gera (Claude ou fallback)."""
    existing = _latest_storyboard(db, project)
    if existing and len(existing.get("scenes") or []) == len(pages):
        return existing

    sb: dict | None = None
    text_provider = get_text_provider()
    gen = getattr(text_provider, "generate_storyboard", None)
    if gen is not None:
        try:
            result = await gen(
                story=project.story_text,
                theme=theme_combined,
                title=title,
                language=language,
            )
            sb = _parse_storyboard_json(result.text)
        except ProviderError as exc:
            if require_ai and exc.transient:
                raise
            sb = None
    if not sb:
        sb = _fallback_storyboard(pages, title=title, theme=theme_combined)

    extra_theme = (project.extra_theme or "").strip() or None
    theme = project.theme or "adventure"
    if extra_theme == theme:
        extra_theme = None
    sb.update({
        "version": 1,
        "theme": theme,
        "extra_theme": extra_theme,
        "language": language,
        "title": sb.get("title") or title,
        "total_duration_s": sum(s.get("duration_s", 5) for s in sb["scenes"]),
    })
    _save_storyboard_asset(db, project, sb, auto=auto)
    return sb


async def ensure_page_briefs(
    db: Session,
    project: Project,
    pages: list[str],
    *,
    template_id: str | None,
    notes: list[str],
    layouts: list[str] | None,
    language: str,
) -> list[dict]:
    """Roteiro visual por pagina: catálogo preserva illustration_notes na scene."""
    costume = (
        costume_extras_for_template(template_id)
        if template_id
        else costume_extras_for_theme(project.theme)
    )
    if template_id:
        briefs = _fallback_page_briefs(
            pages, notes=notes, costume=costume, layouts=layouts
        )
        for i, brief in enumerate(briefs):
            if i < len(notes) and (notes[i] or "").strip():
                brief["scene"] = notes[i].strip()
        return briefs

    title = _parse_title(project.story_text) or ""
    theme = project.theme or "adventure"
    extra_theme = (project.extra_theme or "").strip() or None
    if extra_theme == theme:
        extra_theme = None
    theme_combined = f"{theme} + {extra_theme}" if extra_theme else theme
    sb = await _compose_storyboard(
        db, project, pages, title=title, theme_combined=theme_combined,
        language=language, auto=True,
    )
    scenes = sb.get("scenes") or []
    briefs = []
    for i, page in enumerate(pages):
        sc = scenes[i] if i < len(scenes) else {}
        brief = _scene_to_brief(sc, page, page_index=i)
        if not brief.get("costume"):
            brief["costume"] = costume
        briefs.append(brief)
    return briefs


async def _store_bible_asset(
    db: Session, project: Project, kind: AssetKind, result: ImageResult
) -> bytes:
    key = storage.new_key(project.id, kind.value, _ext(result.mime_type))
    storage.put_bytes(key, result.image_bytes, result.mime_type)
    db.add(Asset(
        project_id=project.id,
        kind=kind.value,
        storage_key=key,
        meta={"mime": result.mime_type},
    ))
    return result.image_bytes


async def _generate_character_bible(
    db: Session,
    project: Project,
    provider,
    *,
    photo: bytes | None,
    avatar: bytes,
    costume: str,
    style: str,
) -> dict[str, bytes]:
    """3 folhas (turnaround, expressoes, figurino). Best-effort: falha nao aborta o livro."""
    bible: dict[str, bytes] = {}
    refs = [img for img in (photo, avatar) if img]

    async def _one(kind: AssetKind, prompt: str, extra: list[bytes]) -> None:
        try:
            result = await provider.generate_character(
                prompt=prompt,
                reference_images=refs + extra,
                style=style,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Ficha %s falhou; ebook segue sem ela", kind.value)
            return
        if not result or not result.image_bytes:
            return
        bible[kind.value] = await _store_bible_asset(db, project, kind, result)

    await _one(AssetKind.CHARACTER_SHEET, CHARACTER_SHEET_PROMPT, [])
    sheet = bible.get(AssetKind.CHARACTER_SHEET.value)
    extra_sheet = [sheet] if sheet else []
    await _one(AssetKind.EXPRESSION_SHEET, EXPRESSION_SHEET_PROMPT, extra_sheet)
    await _one(
        AssetKind.COSTUME_LOCK, costume_lock_prompt(costume), extra_sheet
    )
    db.commit()
    return bible


def _scene_extra_refs(
    bible: dict[str, bytes], expression: str, *, style_ref: bytes | None = None
) -> list[bytes]:
    extras: list[bytes] = []
    costume = bible.get(AssetKind.COSTUME_LOCK.value)
    sheet = bible.get(AssetKind.CHARACTER_SHEET.value)
    expr_sheet = bible.get(AssetKind.EXPRESSION_SHEET.value)
    if costume:
        extras.append(costume)
    if sheet:
        extras.append(sheet)
    if expr_sheet and normalize_expression(expression) in EXPRESSION_SHEET_KEYS:
        extras.append(expr_sheet)
    if style_ref:
        extras.append(style_ref)
    return extras


async def _judge_page(lock: IdentityLock, scene: bytes) -> FaceVerdict:
    """Nota de identidade; None com juiz ligado e unverified (fail-closed)."""
    return await judge_identity(lock, scene, scorer=score_face_match)


async def _illustrate_page(
    provider,
    *,
    idx: int,
    caption: str,
    brief: dict,
    extras: str,
    child_name: str,
    lock: IdentityLock,
    bible: dict[str, bytes],
    style_lock: asyncio.Lock,
    good_style: list[bytes],
) -> ImageResult:
    """Gera uma pagina com o lock obrigatorio; recusa se o rosto nao bater."""
    refs = lock.scene_kwargs()
    prompt = build_scene_prompt(
        page=idx,
        text=caption,
        scene=(brief.get("scene") or caption)[:900],
        expression=brief.get("expression"),
        extras=extras,
        child_name=child_name,
        shot=brief.get("shot") or "",
        text_band=brief.get("text_band") or "",
    )
    extra_refs = _scene_extra_refs(bible, brief.get("expression") or "")

    async def _generate(page_extra_refs: list[bytes] | None = extra_refs) -> ImageResult:
        return await provider.generate_scene(
            prompt=prompt,
            style=BOOK_STYLE,
            extra_refs=page_extra_refs or None,
            **refs,
        )

    scene = await _generate()
    threshold = settings.ebook_face_match_min
    best = scene
    best_verdict = await _judge_page(lock, scene.image_bytes)

    async def _consider(candidate: ImageResult) -> None:
        nonlocal best, best_verdict
        verdict = await _judge_page(lock, candidate.image_bytes)
        if prefer_verdict(verdict, best_verdict, threshold):
            best = candidate
            best_verdict = verdict

    if not best_verdict.accepted(threshold):
        if settings.ebook_refine_scene:
            refined = await _refine_scene(
                provider, refs["character_ref"], best, BOOK_STYLE, photo=refs["photo"]
            )
            if refined is not best:
                await _consider(refined)
        if not best_verdict.accepted(threshold):
            style_ref = None
            async with style_lock:
                if good_style:
                    style_ref = good_style[0]
            retry_refs = _scene_extra_refs(
                bible, brief.get("expression") or "", style_ref=style_ref
            )
            retried = await _generate(retry_refs)
            await _consider(retried)

    if not best_verdict.accepted(threshold):
        note = (
            f"{best_verdict.score:.2f}" if best_verdict.score is not None else "sem nota"
        )
        raise ProviderError(
            f"Pagina {idx}: {IDENTITY_MISMATCH_ERROR} (nota={note})",
            transient=False,
        )

    async with style_lock:
        if best.image_bytes not in good_style:
            good_style.append(best.image_bytes)
    return best


# --------------------------------------------------------------------------- #
# Etapa 9-10: ebook (ilustracoes por pagina + montagem)
# --------------------------------------------------------------------------- #
async def handle_ebook(db: Session, job: Job) -> None:
    project = _project(db, job)
    if not project.story_text:
        raise ProviderError("Historia ausente: rode STORY antes", transient=False)
    if not project.character_ref:
        raise ProviderError("Personagem ausente: rode AVATAR antes", transient=False)
    project.book_approved_at = None
    project.print_requested_at = None
    project.print_status = None
    _set_status(db, project, ProjectStatus.EBOOK_RUNNING)

    char_bytes = require_character_ref(
        storage.get_bytes(project.character_ref["storage_key"])
    )
    photo_bytes = await _project_photo_bytes(db, project)
    lock = build_identity_lock(
        character_ref=char_bytes, face_crop=photo_bytes, photo=photo_bytes
    )
    image_provider = get_image_provider()

    language = project.language or "pt-BR"
    child_name = (project.child_name or "").strip()
    template_id = _catalog_template_id(db, project)
    notes = illustration_notes(template_id, child_name) if template_id else []
    layouts = page_layouts(template_id) if template_id else []
    extras = (
        scene_extras_for_template(template_id)
        if template_id
        else costume_extras_for_theme(project.theme)
    )

    # 1) Divide a historia em paginas (toda a historia, sem limite fixo).
    pages_text = _parse_pages(project.story_text)
    briefs = await ensure_page_briefs(
        db, project, pages_text,
        template_id=template_id, notes=notes, layouts=layouts, language=language,
    )

    # 2) Texto impresso por pagina. Historias geradas pelo pipeline ja vem como
    #    estrofes curtas rimadas (estilo WonderWraps) -> imprime o verso integral.
    #    Historias importadas/longas -> resume em legenda curta.
    #    Dedicatoria de catalogo pode passar de 260 caracteres; nao dispara o
    #    resumo das demais paginas e nunca e resumida.
    story_too_long = any(
        (layouts[i] if i < len(layouts) else "story") != "dedication" and len(p) > 260
        for i, p in enumerate(pages_text)
    )
    if not story_too_long:
        captions = list(pages_text)
    else:
        captions = _short_captions(pages_text)
        try:
            ai_caps = await get_text_provider().summarize_pages(
                pages=pages_text, style=BOOK_STYLE, language=language
            )
            if len(ai_caps) == len(pages_text) and all(c.strip() for c in ai_caps):
                captions = [c.strip() for c in ai_caps]
        except Exception:  # noqa: BLE001 - se o resumo falhar, usa o fallback local
            pass
        for i, p in enumerate(pages_text):
            if i < len(captions) and (layouts[i] if i < len(layouts) else "story") == "dedication":
                captions[i] = p

    bible: dict[str, bytes] = {}
    if not settings.offline_fallback:
        bible = await _generate_character_bible(
            db, project, image_provider,
            photo=photo_bytes,
            avatar=char_bytes,
            costume=_book_costume_line(briefs, template_id, project.theme),
            style=BOOK_STYLE,
        )

    # 3) Uma pagina = ilustracao (brief visual) + texto. Dedicatoria = so texto.
    work: list[tuple[int, str, dict, str]] = []
    for idx, (full_text, caption) in enumerate(zip(pages_text, captions), 1):
        layout = layouts[idx - 1] if idx - 1 < len(layouts) else "story"
        brief = briefs[idx - 1] if idx - 1 < len(briefs) else _scene_to_brief({}, full_text, page_index=idx - 1)
        if layout != "dedication":
            work.append((idx, caption, brief, layout))

    generated: dict[int, ImageResult] = {}
    if settings.offline_fallback:
        for idx, caption, _brief, _layout in work:
            generated[idx] = ImageResult(
                image_bytes=_offline_png(
                    f"Pagina {idx}: {caption[:28]}",
                    palette=((233, 242, 255), (255, 255, 255)),
                ),
                mime_type="image/png",
                cost_usd=0.0,
            )
    else:
        sem = asyncio.Semaphore(max(1, settings.ebook_page_concurrency))
        style_lock = asyncio.Lock()
        good_style: list[bytes] = []

        async def _one(item: tuple[int, str, dict, str]) -> tuple[int, ImageResult]:
            idx, caption, brief, layout = item
            page_extras = (
                name_scene_extras_for_template(template_id)
                if layout == "name"
                else extras
            )
            async with sem:
                result = await _illustrate_page(
                    image_provider,
                    idx=idx,
                    caption=caption,
                    brief=brief,
                    extras=page_extras,
                    child_name=child_name,
                    lock=lock,
                    bible=bible,
                    style_lock=style_lock,
                    good_style=good_style,
                )
            return idx, result

        done = await asyncio.gather(*[_one(item) for item in work])
        generated = {idx: result for idx, result in done}

    pages: list[dict] = []
    for idx, (full_text, caption) in enumerate(zip(pages_text, captions), 1):
        layout = layouts[idx - 1] if idx - 1 < len(layouts) else "story"
        if layout == "dedication":
            pages.append({"text": caption, "image": None, "layout": "dedication"})
            continue
        scene = generated[idx]
        img_key = storage.new_key(project.id, AssetKind.PAGE_IMAGE.value, _ext(scene.mime_type))
        storage.put_bytes(img_key, scene.image_bytes, scene.mime_type)
        db.add(Asset(
            project_id=project.id,
            kind=AssetKind.PAGE_IMAGE.value,
            storage_key=img_key,
            meta={"page": idx},
        ))
        pages.append({
            "text": caption,
            "image": scene.image_bytes,
            "mime": scene.mime_type,
            "layout": layout,
        })
    db.commit()

    name = (project.child_name or "").strip()
    is_en = (language or "").lower().startswith("en")
    title = _parse_title(project.story_text) or (
        (f"The Adventure of {name}" if name else "My Great Adventure") if is_en
        else (f"A Grande Aventura de {name}" if name else "A Minha Grande Aventura")
    )

    extra_chars = []
    for ec in (project.extra_characters or []):
        char_key = ec.get("character_storage_key")
        if char_key:
            try:
                extra_chars.append({
                    "name": ec.get("name", ""),
                    "image_bytes": storage.get_bytes(char_key),
                })
            except Exception:  # noqa: BLE001
                pass

    blob = ebook_builder.build_pdf(
        title=title,
        pages=pages,
        dedication=(project.dedication or None),
        portrait=char_bytes,
        child_name=(name or None),
        language=language,
        extra_characters=extra_chars or None,
        preview_pages=3,
    )
    mime = "application/pdf"
    ebook_key = storage.new_key(project.id, AssetKind.EBOOK.value, "pdf")
    storage.put_bytes(ebook_key, blob, mime)
    db.add(Asset(project_id=project.id, kind=AssetKind.EBOOK.value, storage_key=ebook_key,
                 meta={"mime": mime}))
    project.ebook_url = ebook_key
    _set_status(db, project, ProjectStatus.EBOOK_READY)


# --------------------------------------------------------------------------- #
# Etapa 12-13: storyboard (roteiro completo em JSON + keyframes para o video)
# --------------------------------------------------------------------------- #
_CAMERA_FALLBACK = [
    "aproximação lenta (push-in)",
    "panorâmica suave da esquerda para a direita",
    "travelling lateral acompanhando o protagonista",
    "zoom out revelando o cenário",
]


def _fallback_storyboard(pages: list[str], *, title: str, theme: str) -> dict:
    """Roteiro determinístico local (sem IA): uma cena por página da história."""
    scenes = []
    for i, page in enumerate(pages, 1):
        flat = page.replace("\n", " ").strip()
        first = re.split(r"(?<=[.!?])\s+", flat)[0] if flat else ""
        scenes.append({
            "n": i,
            "narration": page.strip(),
            "setting": "",
            "action": first[:220],
            "scene": flat[:400],
            "expression": infer_expression(page),
            "shot": "medium",
            "costume": costume_extras_for_theme(theme.split(" + ")[0] if theme else None),
            "text_band": "top" if (i - 1) % 2 == 0 else "bottom",
            "camera": _CAMERA_FALLBACK[(i - 1) % len(_CAMERA_FALLBACK)],
            "mood": "",
            "duration_s": 5,
            "image_prompt": f"Cena {i} da história (tema {theme}): {flat[:400]}",
            "video_prompt": f"Anime a cena com movimento suave e expressivo: {first[:200]}",
        })
    return {"title": title, "logline": "", "moral": "", "scenes": scenes}


def _parse_storyboard_json(text: str) -> dict | None:
    """Extrai e normaliza o JSON do roteiro (tolerante a cercas de código e texto extra)."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:  # noqa: BLE001 - JSON inválido -> caller usa fallback
        return None
    raw_scenes = data.get("scenes")
    if not isinstance(raw_scenes, list):
        return None
    scenes = []
    for i, sc in enumerate(raw_scenes, 1):
        if not isinstance(sc, dict):
            continue
        try:
            dur = int(sc.get("duration_s") or 5)
        except (TypeError, ValueError):
            dur = 5
        scenes.append({
            "n": i,
            "narration": str(sc.get("narration") or "").strip(),
            "setting": str(sc.get("setting") or "").strip(),
            "action": str(sc.get("action") or "").strip(),
            "scene": str(sc.get("scene") or sc.get("action") or sc.get("setting") or "").strip(),
            "expression": normalize_expression(sc.get("expression") or sc.get("mood")),
            "shot": normalize_shot(sc.get("shot")),
            "costume": str(sc.get("costume") or "").strip(),
            "text_band": normalize_text_band(sc.get("text_band")),
            "camera": str(sc.get("camera") or "").strip(),
            "mood": str(sc.get("mood") or "").strip(),
            "duration_s": min(8, max(4, dur)),
            "image_prompt": str(sc.get("image_prompt") or "").strip(),
            "video_prompt": str(sc.get("video_prompt") or "").strip(),
        })
    if not scenes:
        return None
    return {
        "title": str(data.get("title") or "").strip(),
        "logline": str(data.get("logline") or "").strip(),
        "moral": str(data.get("moral") or "").strip(),
        "scenes": scenes,
    }


def _latest_storyboard(db: Session, project: Project) -> dict | None:
    """Carrega o roteiro mais recente do projeto (ou None)."""
    asset = db.scalar(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.STORYBOARD.value)
        .order_by(Asset.created_at.desc())
    )
    if not asset:
        return None
    try:
        return json.loads(storage.get_bytes(asset.storage_key).decode("utf-8"))
    except Exception:  # noqa: BLE001 - roteiro corrompido não deve travar o vídeo
        return None


async def handle_storyboard(db: Session, job: Job) -> None:
    """Gera o ROTEIRO COMPLETO (JSON) para o ebook e o vídeo.

    Não gera mais keyframes: o vídeo usa as page_image do ebook.
    """
    project = _project(db, job)
    if not (project.story_text or "").strip():
        raise ProviderError("Historia ausente: rode STORY antes", transient=False)

    language = project.language or "pt-BR"
    theme = project.theme or "adventure"
    extra_theme = (project.extra_theme or "").strip() or None
    if extra_theme == theme:
        extra_theme = None
    theme_combined = f"{theme} + {extra_theme}" if extra_theme else theme
    title = _parse_title(project.story_text) or ""
    pages = _parse_pages(project.story_text)
    await _compose_storyboard(
        db, project, pages,
        title=title,
        theme_combined=theme_combined,
        language=language,
        auto=bool(_payload(job).get("auto")),
        require_ai=True,
    )


# --------------------------------------------------------------------------- #
# Etapa 14-15: video (create + poll; pode tambem concluir via webhook)
# --------------------------------------------------------------------------- #
async def handle_video(db: Session, job: Job) -> None:
    """Animação curta (Kling image2video) — não é o vídeo narrado longo."""
    import asyncio
    import time

    project = _project(db, job)
    payload = _payload(job)
    sb = _latest_storyboard(db, project)
    ref_key = _video_reference_key(db, project, scene_n=1)
    _set_status(db, project, ProjectStatus.VIDEO_RUNNING)

    base_image = storage.get_bytes(ref_key)
    source_url: str | None = None
    task = None
    if _use_video_offline():
        video_key = storage.new_key(project.id, AssetKind.VIDEO.value, "gif")
        video_label = "Animacao offline"
        if sb and sb.get("scenes"):
            video_label = (sb["scenes"][0].get("video_prompt") or video_label)[:32]
        storage.put_bytes(video_key, _offline_gif(video_label), "image/gif")
        stored = video_key
        source_url = "offline:local"
    else:
        provider = get_video_provider(payload.get("provider") or job.provider)

        prompt = "Anime o personagem com movimento suave e expressivo."
        if sb and sb.get("scenes"):
            first = sb["scenes"][0]
            prompt = first.get("video_prompt") or prompt

        duration_s = _clamp_kling_duration(
            int(payload.get("duration_s", settings.default_video_duration_s))
        )
        task = await provider.create_video(
            image=base_image,
            prompt=prompt,
            duration_s=duration_s,
        )
        job.result = {**(job.result or {}), "provider_task_id": task.provider_task_id}
        db.commit()

        deadline = time.monotonic() + settings.video_poll_timeout_s
        while task.status not in ("DONE", "FAILED"):
            if time.monotonic() > deadline:
                raise ProviderError("Timeout aguardando video", transient=True)
            await asyncio.sleep(settings.video_poll_interval_s)
            task = await provider.poll_video(provider_task_id=task.provider_task_id)

        if task.status == "FAILED" or not task.video_url:
            raise ProviderError("Provedor de video falhou", transient=True)

        video_key = storage.new_key(project.id, AssetKind.VIDEO.value, "mp4")
        try:
            import httpx

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.get(task.video_url)
                resp.raise_for_status()
                storage.put_bytes(video_key, resp.content, "video/mp4")
                stored = video_key
                source_url = task.video_url
        except Exception:  # noqa: BLE001 - se nao der para baixar, guarda a URL do provedor
            stored = task.video_url
            source_url = task.video_url

    db.add(Asset(project_id=project.id, kind=AssetKind.VIDEO.value, storage_key=stored,
                 meta={"source": source_url, "kind": "animation"}))
    project.video_url = stored
    job.cost_usd = 0.0 if _use_video_offline() else getattr(task, "cost_usd", None)
    _set_status(db, project, ProjectStatus.VIDEO_READY)


def _scene_image_bytes(db: Session, project: Project, scene_n: int) -> bytes:
    """Imagem da cena: keyframe, senão page_image por ordem, senão character."""
    try:
        key = _video_reference_key(db, project, scene_n=scene_n)
        return storage.get_bytes(key)
    except ProviderError:
        pass
    pages = db.scalars(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.PAGE_IMAGE.value)
        .order_by(Asset.created_at.asc())
    ).all()
    # Páginas sem meta keyframe (ebook) — usa índice 0-based
    non_kf = [a for a in pages if not (a.meta or {}).get("keyframe")]
    if non_kf:
        idx = max(0, min(scene_n - 1, len(non_kf) - 1))
        return storage.get_bytes(non_kf[idx].storage_key)
    if pages:
        idx = max(0, min(scene_n - 1, len(pages) - 1))
        return storage.get_bytes(pages[idx].storage_key)
    if project.character_ref and project.character_ref.get("storage_key"):
        return storage.get_bytes(project.character_ref["storage_key"])
    raise ProviderError("Sem imagens para montar o video narrado", transient=False)


def _resolve_elevenlabs_voice_id(db: Session, user_id: uuid.UUID, payload: dict) -> str | None:
    """Resolve voice_id interno do payload (ou default do usuário) para ID ElevenLabs."""
    voice_uuid = None
    raw = (payload or {}).get("voice_id")
    if raw:
        try:
            voice_uuid = uuid.UUID(str(raw))
        except (ValueError, TypeError):
            voice_uuid = None
    if voice_uuid is not None:
        voice = db.get(UserVoice, voice_uuid)
        if voice and voice.user_id == user_id:
            return voice.elevenlabs_voice_id
    default = db.scalar(
        select(UserVoice).where(UserVoice.user_id == user_id, UserVoice.is_default.is_(True))
    )
    if default:
        return default.elevenlabs_voice_id
    return None


async def handle_narrated_video(db: Session, job: Job) -> None:
    """Vídeo narrado multi-cena: TTS + Ken Burns (ffmpeg) a partir do storyboard."""
    from app.media.assemble import (
        AssembleError,
        SceneClip,
        assemble_narrated_video,
        assemble_slideshow_gif,
        ffmpeg_available,
    )
    from app.media.tts import TtsError, get_tts_provider

    project = _project(db, job)
    sb = _latest_storyboard(db, project)
    if not sb or not sb.get("scenes"):
        raise ProviderError(
            "Storyboard ausente: aguarde a geracao do roteiro ou rode STORYBOARD",
            transient=False,
        )

    _set_status(db, project, ProjectStatus.VIDEO_RUNNING)
    language = project.language or sb.get("language") or "pt-BR"
    el_voice_id = _resolve_elevenlabs_voice_id(db, project.user_id, _payload(job))
    tts = get_tts_provider(voice_id=el_voice_id)
    clips: list[SceneClip] = []

    for sc in sb["scenes"]:
        n = int(sc.get("n") or len(clips) + 1)
        narration = (sc.get("narration") or "").strip() or f"Cena {n}."
        try:
            audio = await tts.synthesize(narration, language=language)
        except TtsError as exc:
            if not settings.offline_fallback:
                raise ProviderError(str(exc), transient=exc.transient) from exc
            # Tom curto silencioso via edge falhou — usa beep mínimo (áudio vazio gera GIF)
            audio = b""
        image = _scene_image_bytes(db, project, n)
        if not audio:
            # Sem áudio: ainda entra no fallback GIF
            clips.append(SceneClip(image_bytes=image, audio_bytes=b"\x00" * 0, image_ext="png"))
        else:
            clips.append(SceneClip(image_bytes=image, audio_bytes=audio, image_ext="png"))

    # Descarta cenas sem áudio válido se ffmpeg estiver disponível
    usable = [c for c in clips if c.audio_bytes]
    music = None
    music_path = Path(__file__).resolve().parent.parent / "assets" / "audio" / "bed.mp3"
    if music_path.is_file():
        music = music_path.read_bytes()

    try:
        if ffmpeg_available() and usable:
            video_bytes = assemble_narrated_video(usable, music_bytes=music)
            ext, mime = "mp4", "video/mp4"
        else:
            video_bytes = assemble_slideshow_gif(clips or usable)
            ext, mime = "gif", "image/gif"
    except AssembleError as exc:
        if settings.offline_fallback:
            video_bytes = assemble_slideshow_gif(clips)
            ext, mime = "gif", "image/gif"
        else:
            raise ProviderError(str(exc), transient=False) from exc

    key = storage.new_key(project.id, AssetKind.NARRATED_VIDEO.value, ext)
    storage.put_bytes(key, video_bytes, mime)
    db.add(
        Asset(
            project_id=project.id,
            kind=AssetKind.NARRATED_VIDEO.value,
            storage_key=key,
            meta={"scenes": len(sb["scenes"]), "mime": mime},
        )
    )
    project.narrated_video_url = key
    job.cost_usd = 0.0
    # Não sobrescreve VIDEO_READY da animação se já existir — usa status genérico pronto
    if project.status != ProjectStatus.VIDEO_READY.value:
        _set_status(db, project, ProjectStatus.VIDEO_READY)
    else:
        db.commit()


def _ext(mime: str) -> str:
    return {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "png")


HANDLERS = {
    "AVATAR": handle_avatar,
    "REALISTIC": handle_realistic,
    "STORY": handle_story,
    "EBOOK": handle_ebook,
    "STORYBOARD": handle_storyboard,
    "VIDEO": handle_video,
    "NARRATED_VIDEO": handle_narrated_video,
    "EXTRA_CHARACTER": handle_extra_character,
}
