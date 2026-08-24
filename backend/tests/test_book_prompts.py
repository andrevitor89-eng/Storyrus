# -*- coding: utf-8 -*-
"""Testes do modulo de prompts do livro (avatar + expressao + cena)."""
from app.ai_clients.book_prompts import (
    AVATAR_PROMPT,
    REFINE_IDENTITY_PROMPT,
    REFINE_SCENE_PROMPT,
    SCENE_GEN_PREFIX,
    build_scene_prompt,
    expression_directive,
    infer_expression,
    normalize_expression,
)


def test_normalize_expression_aliases():
    assert normalize_expression("feliz") == "alegria"
    assert normalize_expression("medo") == "medo_gentil"
    assert normalize_expression("Tristeza") == "tristeza_leve"
    assert normalize_expression("empolgado") == "animacao"
    assert normalize_expression("timido") == "vergonha"
    assert normalize_expression("xyz") == "alegria"


def test_infer_expression_from_text():
    assert infer_expression("Matteo fica muito triste") == "tristeza_leve"
    assert infer_expression("olhar atento e surpreso") == "surpresa"
    assert infer_expression("decidem construir uma ponte") == "determinacao"
    assert infer_expression("ficou com vergonha e corado") == "vergonha"
    assert infer_expression("pulando de empolgacao") == "animacao"


def test_build_scene_prompt_includes_expression_and_identity_hooks():
    prompt = build_scene_prompt(
        page=3,
        text="Matteo abraca o porquinho.",
        scene="Matteo sorridente com o porquinho.",
        expression="alegria",
        child_name="Matteo",
    )
    assert "Pagina 3" in prompt
    assert "Matteo" in prompt
    assert "alegria" in prompt
    assert "EXPRESSAO FACIAL OBRIGATORIA" in prompt
    assert "NAO escrever na imagem" in prompt
    assert "NAO mude identidade" in prompt


def test_build_scene_prompt_infers_different_expressions():
    sad = build_scene_prompt(page=1, text="A menina ficou triste e sozinha.")
    happy = build_scene_prompt(page=2, text="Ela brinca feliz na festa.")
    surprise = build_scene_prompt(page=3, text="De repente, uau, que surpresa!")
    assert "tristeza_leve" in sad
    assert "alegria" in happy
    assert "surpresa" in surprise
    assert sad != happy


def test_avatar_prompt_face_fidelity_and_head():
    assert "character_ref" in AVATAR_PROMPT
    assert "mais proximo possivel" in AVATAR_PROMPT or "100% reconhecivel" in AVATAR_PROMPT
    assert "REINTERPRETADOS em CGI 3D" in AVATAR_PROMPT or "nao copiados como fotografia" in AVATAR_PROMPT
    assert "PROPORCAO DA CABECA" in AVATAR_PROMPT or "proporcao NATURAL" in AVATAR_PROMPT
    assert "sem aumentar" in AVATAR_PROMPT.lower() or "identica a da foto" in AVATAR_PROMPT.lower()
    assert "chibi" in AVATAR_PROMPT.lower() or "PROIBIDO" in AVATAR_PROMPT
    assert "NEUTRA-ALEGRE" in AVATAR_PROMPT or "neutra" in AVATAR_PROMPT.lower()
    assert "ESTILO CGI 3D DE FILME INFANTIL OBRIGATORIO" in AVATAR_PROMPT
    assert "CGI 3D" in AVATAR_PROMPT
    assert "PINTURA REALISTA" not in AVATAR_PROMPT
    assert "2D nitida" not in AVATAR_PROMPT
    assert "PROIBIDO Pixar" not in AVATAR_PROMPT
    assert "ESTILO PINTURA REALISTA OBRIGATORIO" not in AVATAR_PROMPT
    assert "ESTILO MISTO OBRIGATORIO" not in AVATAR_PROMPT
    assert "trate o rosto como uma FOTO" not in AVATAR_PROMPT
    assert "NAO copie a foto original" in AVATAR_PROMPT or "NAO cole o rosto" in AVATAR_PROMPT
    assert "PROIBIDO inventar franja" in AVATAR_PROMPT or "NAO invente" in AVATAR_PROMPT
    assert "tracos atipicos" in AVATAR_PROMPT
    assert "marca d'agua" in AVATAR_PROMPT.lower() or "marca d'agua" in AVATAR_PROMPT
    assert "ANTI-ROSTO-GENERICO" in AVATAR_PROMPT
    assert "IDENTITY LOCK" in AVATAR_PROMPT
    assert "Ignore adultos" in AVATAR_PROMPT
    assert "sorriso largo de banco de imagens" in AVATAR_PROMPT


def test_refine_identity_orders_photo_first():
    assert "FOTO" in REFINE_IDENTITY_PROMPT
    assert "fonte de verdade" in REFINE_IDENTITY_PROMPT.lower()
    assert "ESTILO CGI 3D DE FILME INFANTIL OBRIGATORIO" in REFINE_IDENTITY_PROMPT
    assert "NAO invente franja" in REFINE_IDENTITY_PROMPT
    assert "fotorealizar" in REFINE_IDENTITY_PROMPT or "PROIBIDO copiar a foto" in REFINE_IDENTITY_PROMPT
    assert "tracos atipicos" in REFINE_IDENTITY_PROMPT
    assert "ANTI-ROSTO-GENERICO" in REFINE_IDENTITY_PROMPT
    assert "Ignore adultos" in REFINE_IDENTITY_PROMPT
    assert "SUBSTITUA pela qualidade fotografica" not in REFINE_IDENTITY_PROMPT
    assert "2D nitida" not in REFINE_IDENTITY_PROMPT


def test_scene_and_style_are_cgi_3d_not_photo():
    assert "ESTILO CGI 3D DE FILME INFANTIL OBRIGATORIO" in SCENE_GEN_PREFIX
    assert "ESTILO CGI 3D DE FILME INFANTIL OBRIGATORIO" in REFINE_SCENE_PROMPT
    assert "ESTILO MISTO OBRIGATORIO" not in SCENE_GEN_PREFIX
    assert "PINTURA REALISTA" not in SCENE_GEN_PREFIX
    assert "2D nitida" not in SCENE_GEN_PREFIX
    assert "PROIBIDO Pixar" not in SCENE_GEN_PREFIX
    assert "CGI 3D" in SCENE_GEN_PREFIX


def test_scene_keeps_emotion_separate_from_identity():
    assert "expressao NEUTRA" in SCENE_GEN_PREFIX or "NAO a copie" in SCENE_GEN_PREFIX
    assert "PRESERVE a EXPRESSAO FACIAL" in REFINE_SCENE_PROMPT
    assert "neutra do avatar" in REFINE_SCENE_PROMPT.lower() or "emocao da pagina" in REFINE_SCENE_PROMPT.lower()


def test_expression_directive():
    d = expression_directive("curiosidade")
    assert "curiosidade" in d
    assert "sobrancelhas" in d
    assert "NAO mude identidade" in d
    assert "PROIBIDO copiar a expressao neutra" in d
