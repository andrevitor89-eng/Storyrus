"""Contrato da DNA visual Tell My Tale: prompts sem hibrido foto+Funko."""
from app.ai_clients.storybook_style import (
    FORBIDDEN_STYLE_TOKENS,
    THEME_STAGING,
    avatar_prompt,
    character_prompt,
    ebook_scene_prompt,
    identity_refine_prompt,
    keyframe_scene_prompt,
    realistic_prompt,
    scene_prompt,
    scene_refine_prompt,
    theme_staging,
)


def _assert_storybook_dna(text: str) -> None:
    lowered = text.lower()
    for token in FORBIDDEN_STYLE_TOKENS:
        assert token not in lowered, f"token proibido ainda no prompt: {token!r}"
    assert "pintura digital" in lowered or "digital painting" in lowered
    assert "livro infantil" in lowered or "children's-book" in lowered or "children's book" in lowered


def test_forbidden_tokens_stay_out_of_every_builder():
    samples = [
        character_prompt(prompt=avatar_prompt(theme="dinosaurs"), style="realistic"),
        character_prompt(prompt=avatar_prompt(theme="princess"), style="cartoon"),
        character_prompt(prompt=avatar_prompt(theme="space", extra=True), style="anime"),
        identity_refine_prompt(style="realistic"),
        scene_prompt(prompt=ebook_scene_prompt(page_idx=1, excerpt="A heroína corre."), style="cartoon"),
        scene_refine_prompt(style="anime"),
        realistic_prompt(theme="superhero"),
        keyframe_scene_prompt(scene_n=2, prompt="A criança voa sobre a cidade."),
    ]
    for text in samples:
        _assert_storybook_dna(text)


def test_character_prompt_locks_identity_and_drops_photo_clothes():
    text = character_prompt(prompt=avatar_prompt(theme="adventure"), style="realistic")
    lowered = text.lower()
    assert "trave a identidade" in lowered
    assert "nao copie a roupa nem o fundo da foto" in lowered
    assert "nao use a roupa da foto" in lowered
    assert "fundo neutro" in lowered  # so como proibicao ("NAO use fundo neutro")
    assert "nao use fundo neutro" in lowered


def test_identity_refine_keeps_illustration_costume():
    text = identity_refine_prompt().lower()
    assert "preserve o figurino" in text
    assert "nao copie a roupa nem o cenario da foto" in text
    assert "fotografia" in text


def test_scene_prompt_allows_accessory_keeps_base_costume():
    text = scene_prompt(prompt="A criança atravessa a ponte.", style="realistic").lower()
    assert "figurino" in text
    assert "acessorio pontual" in text
    assert "character_ref" not in text  # nome interno nao vaza ao modelo


def test_theme_staging_maps_known_themes_and_falls_back():
    dino = theme_staging("dinosaurs")
    assert "paleontologo" in dino["costume"] or "explorador" in dino["costume"]
    assert "dinossauro" in dino["setting"]

    space = theme_staging("SPACE")
    assert "astronauta" in space["costume"]

    unknown = theme_staging("tema-que-nao-existe")
    default = theme_staging(None)
    assert unknown == default
    assert "explorador" in unknown["costume"]


def test_avatar_prompt_embeds_theme_costume_and_setting():
    text = avatar_prompt(theme="dinosaurs", name="Lila").lower()
    staging = theme_staging("dinosaurs")
    assert "lila" in text
    assert "protagonista" in text
    assert staging["costume"].split()[0] in text or "paleontologo" in text or "explorador" in text
    assert "jurassica" in text or "dinossauro" in text


def test_extra_character_is_supporting_cast_in_same_world():
    text = avatar_prompt(theme="princess", name="Vovó", extra=True).lower()
    assert "coadjuvante" in text
    assert "vovó" in text or "vovo" in text
    assert "castelo" in text or "palacio" in text or "principesca" in text


def test_realistic_prompt_uses_theme_not_photo_outfit():
    text = realistic_prompt(theme="space").lower()
    assert "astronauta" in text
    assert "do not keep the photo outfit" in text
    assert "same outfit" not in text


def test_ebook_and_keyframe_wrappers_keep_reference_costume():
    page = ebook_scene_prompt(page_idx=3, excerpt="Eles chegaram à ilha.").lower()
    assert "pagina 3" in page
    assert "figurino-base" in page
    assert "quadrada" in page

    kf = keyframe_scene_prompt(scene_n=4, prompt="A nave decola.").lower()
    assert "keyframe 4" in kf
    assert "16:9" in kf
    assert "figurino-base" in kf


def test_all_catalog_themes_have_staging():
    assert len(THEME_STAGING) >= 20
    for key, staging in THEME_STAGING.items():
        assert staging["costume"].strip()
        assert staging["setting"].strip()
        assert staging["action"].strip()
        _assert_storybook_dna(character_prompt(prompt=avatar_prompt(theme=key), style="realistic"))
