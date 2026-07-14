"""Handlers das etapas do pipeline.

Cada handler recebe (db, job), executa a etapa via ai_clients, persiste assets no
storage e avanca o estado do projeto. Exceptions ProviderError(transient=True)
sao reprocessadas pelo runner; demais erros -> FAILED + estorno.

Pre-condicoes entre etapas (ex.: ebook exige avatar+story) sao validadas aqui e,
quando faltam, levantam ProviderError(transient=False) -> falha definitiva clara.
"""  # pipeline v2 (livro estilo referencia)
from __future__ import annotations

import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.ai_clients import get_image_provider, get_text_provider, get_video_provider
from app.ai_clients.base import ProviderError
from app.config import settings
from app.models import Asset, AssetKind, Job, JobStatus, JobType, Project, ProjectStatus
from app.workers import ebook as ebook_builder


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
    provider = get_image_provider(job.provider)
    result = await provider.generate_character(
        prompt="Retrato do personagem principal, corpo inteiro, fundo neutro.",
        reference_images=refs,
        style=project.style or "realistic",
    )
    result = await _refine_identity(provider, refs[0], result, project.style or "realistic")

    key = storage.new_key(project.id, AssetKind.CHARACTER.value, _ext(result.mime_type))
    storage.put_bytes(key, result.image_bytes, result.mime_type)
    db.add(Asset(project_id=project.id, kind=AssetKind.CHARACTER.value, storage_key=key,
                 meta={"mime": result.mime_type}))
    project.character_ref = {"storage_key": key, "mime": result.mime_type}
    job.cost_usd = result.cost_usd
    _set_status(db, project, ProjectStatus.AVATAR_READY)


async def _refine_identity(provider, photo_bytes, result, style):
    """Passe opcional: corrige a ilustracao para ficar mais fiel a foto.

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    """
    refine = getattr(provider, "refine_identity", None)
    if refine is None or not photo_bytes:
        return result
    try:
        refined = await refine(
            photo=photo_bytes, illustration=result.image_bytes, style=style
        )
        if refined and getattr(refined, "image_bytes", None):
            return refined
    except Exception:  # noqa: BLE001 - refinamento e opcional
        pass
    return result


async def _refine_scene(provider, character_ref, result, style):
    """Passe opcional de cena: corrige o protagonista para bater com o personagem-base.

    Best-effort: se o provider nao tiver o metodo ou falhar, retorna o resultado original.
    """
    refine = getattr(provider, "refine_scene", None)
    if refine is None or not character_ref:
        return result
    try:
        refined = await refine(
            character_ref=character_ref, scene=result.image_bytes, style=style
        )
        if refined and getattr(refined, "image_bytes", None):
            return refined
    except Exception:  # noqa: BLE001 - refinamento e opcional
        pass
    return result


# Prompt fixo para a imagem realistica (usada como referencia do video).
REALISTIC_PROMPT = (
    "Transform this photo of a child into a semi-realistic children's book illustration, "
    "in the style of a warm painterly digital painting. Keep the child's exact facial features, "
    "expression, hair color and texture, skin tone, and the same outfit, so they remain fully "
    "recognizable. Render with soft golden \"magic hour\" lighting, gentle glow, delicate freckles "
    "and luminous eyes. Place them in a whimsical storybook setting (sunlit fields, soft clouds, "
    "distant castle, or cozy adventure scene) with painterly brush textures, rich warm colors, and "
    "a dreamy bokeh background. High detail, wholesome, enchanting, professional illustration "
    "quality. Portrait/3-4 view, soft focus background, vertical composition."
)
REALISTIC_NEGATIVE = (
    "photorealistic skin, distorted face, extra fingers, text, watermark, harsh lighting, "
    "changing the child's identity or clothing."
)


async def handle_realistic(db: Session, job: Job) -> None:
    """Gera a imagem realistica a partir da foto (prompt fixo) e guarda no banco.

    O asset (kind=realistic_avatar) e a referencia preferencial para o video.
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


def _video_reference_key(db: Session, project: Project) -> str:
    """Imagem usada como base do video: prioriza a realistica; senao o personagem."""
    realistic = db.scalar(
        select(Asset)
        .where(Asset.project_id == project.id, Asset.kind == AssetKind.REALISTIC.value)
        .order_by(Asset.created_at.desc())
    )
    if realistic:
        return realistic.storage_key
    if project.character_ref and project.character_ref.get("storage_key"):
        return project.character_ref["storage_key"]
    raise ProviderError(
        "Imagem de referencia ausente: gere o personagem ou a imagem realistica antes",
        transient=False,
    )


# --------------------------------------------------------------------------- #
# Etapa 5-8: historia
# --------------------------------------------------------------------------- #
async def handle_story(db: Session, job: Job) -> None:
    project = _project(db, job)
    _set_status(db, project, ProjectStatus.STORY_RUNNING)

    theme = project.theme or "adventure"
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

    # Guia educativo do tema: o que a história ensina + sequência lógica da jornada.
    guides = THEME_EDU["en" if is_en else "pt"]
    focus, sequence = guides.get(theme, guides["adventure"])
    if is_en:
        brief += (
            " LEARNING (essential): the story must playfully TEACH — " + focus +
            ". Weave 2 or 3 REAL, simple, age-appropriate facts about the theme into the "
            "action or dialogue (never lecture-like). MANDATORY LOGICAL SEQUENCE of the "
            "journey, adapted creatively: " + sequence +
            ". At the end, the hero happily realizes what they learned."
        )
    else:
        brief += (
            " APRENDIZADO (essencial): a história deve ENSINAR de forma lúdica — " + focus +
            ". Insira 2 ou 3 curiosidades REAIS, simples e adequadas à idade sobre o tema "
            "dentro da ação ou das falas (nunca em tom de aula). SEQUÊNCIA LÓGICA "
            "obrigatória da jornada, adaptada com criatividade: " + sequence +
            ". No final, o protagonista percebe com alegria o que aprendeu."
        )

    provider = get_text_provider(job.provider)
    result = await provider.generate_story(
        brief=brief, style=project.style or "realistic", pages=settings.ebook_pages,
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


# --------------------------------------------------------------------------- #
# Etapa 9-10: ebook (ilustracoes por pagina + montagem)
# --------------------------------------------------------------------------- #
async def handle_ebook(db: Session, job: Job) -> None:
    project = _project(db, job)
    if not project.story_text:
        raise ProviderError("Historia ausente: rode STORY antes", transient=False)
    if not project.character_ref:
        raise ProviderError("Personagem ausente: rode AVATAR antes", transient=False)
    _set_status(db, project, ProjectStatus.EBOOK_RUNNING)

    char_bytes = storage.get_bytes(project.character_ref["storage_key"])
    image_provider = get_image_provider()

    language = project.language or "pt-BR"

    # 1) Divide a historia em paginas (toda a historia, sem limite fixo).
    pages_text = _parse_pages(project.story_text)

    # 2) Texto impresso por pagina. Historias geradas pelo pipeline ja vem como
    #    estrofes curtas rimadas (estilo WonderWraps) -> imprime o verso integral.
    #    Historias importadas/longas -> resume em legenda curta.
    if all(len(p) <= 260 for p in pages_text):
        captions = list(pages_text)
    else:
        captions = _short_captions(pages_text)
        try:
            ai_caps = await get_text_provider().summarize_pages(
                pages=pages_text, style=project.style or "", language=language
            )
            if len(ai_caps) == len(pages_text) and all(c.strip() for c in ai_caps):
                captions = [c.strip() for c in ai_caps]
        except Exception:  # noqa: BLE001 - se o resumo falhar, usa o fallback local
            pass

    # 3) Uma pagina = ilustracao (contexto completo do trecho) + texto da pagina.
    pages: list[dict] = []
    for idx, (full_text, caption) in enumerate(zip(pages_text, captions), 1):
        scene = await image_provider.generate_scene(
            prompt=(
                f"Pagina {idx} da historia. Ilustre exatamente esta cena (contexto completo), "
                f"com o personagem principal (da imagem de referencia) como protagonista, "
                f"mantendo rosto/roupa identicos. Composicao QUADRADA (1:1), pintura digital "
                f"quente e luminosa de livro infantil premium, luz dourada suave; deixe uma "
                f"area mais calma/limpa (ceu, campo, parede) para receber o texto impresso. "
                f"Trecho: {full_text[:900]}"
            ),
            character_ref=char_bytes,
            style=project.style or "realistic",
        )
        scene = await _refine_scene(image_provider, char_bytes, scene, project.style or "realistic")
        img_key = storage.new_key(project.id, AssetKind.PAGE_IMAGE.value, _ext(scene.mime_type))
        storage.put_bytes(img_key, scene.image_bytes, scene.mime_type)
        db.add(Asset(project_id=project.id, kind=AssetKind.PAGE_IMAGE.value,
                     storage_key=img_key, meta={"page": idx}))
        pages.append({"text": caption, "image": scene.image_bytes, "mime": scene.mime_type})
    db.commit()

    name = (project.child_name or "").strip()
    is_en = (language or "").lower().startswith("en")
    title = _parse_title(project.story_text) or (
        (f"The Adventure of {name}" if name else "My Great Adventure") if is_en
        else (f"A Grande Aventura de {name}" if name else "A Minha Grande Aventura")
    )
    blob = ebook_builder.build_pdf(
        title=title,
        pages=pages,
        dedication=(project.dedication or None),
        portrait=char_bytes,
        child_name=(name or None),
        language=language,
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
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.S)
    m = re.search(r"\{.*\}", t, flags=re.S)
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
    """Gera o ROTEIRO COMPLETO do vídeo (JSON) e, se já houver personagem, os keyframes.

    O roteiro fica salvo como asset (kind=storyboard) para a etapa de vídeo usar depois.
    """
    project = _project(db, job)
    if not (project.story_text or "").strip():
        raise ProviderError("Historia ausente: rode STORY antes", transient=False)

    language = project.language or "pt-BR"
    theme = project.theme or "adventure"
    title = _parse_title(project.story_text) or ""
    pages = _parse_pages(project.story_text)

    # 1) Roteiro completo via IA; fallback local determinístico se indisponível/inválido.
    sb: dict | None = None
    text_provider = get_text_provider()
    gen = getattr(text_provider, "generate_storyboard", None)
    if gen is not None:
        try:
            result = await gen(
                story=project.story_text, theme=theme, title=title, language=language
            )
            sb = _parse_storyboard_json(result.text)
            job.cost_usd = result.cost_usd
        except ProviderError as exc:
            if exc.transient:
                raise  # deixa o runner reprocessar
            sb = None
    if not sb:
        sb = _fallback_storyboard(pages, title=title, theme=theme)

    sb.update({
        "version": 1,
        "theme": theme,
        "language": language,
        "title": sb.get("title") or title,
        "total_duration_s": sum(s.get("duration_s", 5) for s in sb["scenes"]),
    })
    key = storage.new_key(project.id, AssetKind.STORYBOARD.value, "json")
    storage.put_bytes(
        key, json.dumps(sb, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
    )
    db.add(Asset(project_id=project.id, kind=AssetKind.STORYBOARD.value, storage_key=key,
                 meta={"scenes": len(sb["scenes"]), "auto": bool(_payload(job).get("auto"))}))
    db.commit()

    # 2) Keyframes por cena (best-effort; só quando o personagem já existe).
    if project.character_ref and project.character_ref.get("storage_key"):
        char_bytes = storage.get_bytes(project.character_ref["storage_key"])
        image_provider = get_image_provider()
        style = project.style or "realistic"
        for sc in sb["scenes"][:6]:
            prompt = sc.get("image_prompt") or sc.get("narration") or ""
            if not prompt:
                continue
            try:
                kf = await image_provider.generate_scene(
                    prompt=(
                        f"Keyframe {sc['n']} para vídeo, composição cinematográfica 16:9, "
                        f"mesmo protagonista da referência: {prompt[:600]}"
                    ),
                    character_ref=char_bytes,
                    style=style,
                )
                kf = await _refine_scene(image_provider, char_bytes, kf, style)
                k = storage.new_key(project.id, AssetKind.PAGE_IMAGE.value, _ext(kf.mime_type))
                storage.put_bytes(k, kf.image_bytes, kf.mime_type)
                db.add(Asset(project_id=project.id, kind=AssetKind.PAGE_IMAGE.value,
                             storage_key=k, meta={"keyframe": sc["n"]}))
            except Exception:  # noqa: BLE001 - keyframe é opcional; o roteiro já está salvo
                continue
        db.commit()


# --------------------------------------------------------------------------- #
# Etapa 14-15: video (create + poll; pode tambem concluir via webhook)
# --------------------------------------------------------------------------- #
async def handle_video(db: Session, job: Job) -> None:
    import asyncio
    import time

    project = _project(db, job)
    ref_key = _video_reference_key(db, project)  # prioriza a imagem realistica
    _set_status(db, project, ProjectStatus.VIDEO_RUNNING)

    payload = _payload(job)
    base_image = storage.get_bytes(ref_key)
    provider = get_video_provider(payload.get("provider") or job.provider)

    # Usa o roteiro (storyboard) gerado em background, quando existir.
    prompt = "Anime o personagem com movimento suave e expressivo."
    sb = _latest_storyboard(db, project)
    if sb and sb.get("scenes"):
        first = sb["scenes"][0]
        prompt = first.get("video_prompt") or prompt

    task = await provider.create_video(
        image=base_image,
        prompt=prompt,
        duration_s=int(payload.get("duration_s", settings.default_video_duration_s)),
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
    # Baixa o video do provedor e republica no nosso storage (URL assinada propria).
    try:
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(task.video_url)
            resp.raise_for_status()
            storage.put_bytes(video_key, resp.content, "video/mp4")
            stored = video_key
    except Exception:  # noqa: BLE001 - se nao der para baixar, guarda a URL do provedor
        stored = task.video_url

    db.add(Asset(project_id=project.id, kind=AssetKind.VIDEO.value, storage_key=stored,
                 meta={"source": task.video_url}))
    project.video_url = stored
    job.cost_usd = task.cost_usd
    _set_status(db, project, ProjectStatus.VIDEO_READY)


def _ext(mime: str) -> str:
    return {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "png")


HANDLERS = {
    "AVATAR": handle_avatar,
    "REALISTIC": handle_realistic,
    "STORY": handle_story,
    "EBOOK": handle_ebook,
    "STORYBOARD": handle_storyboard,
    "VIDEO": handle_video,
}
