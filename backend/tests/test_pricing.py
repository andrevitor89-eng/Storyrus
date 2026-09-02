"""Tabela de preço: imagem, tokens Claude e vídeo."""
from app.services import pricing


def test_image_cost_flat_without_usage():
    assert pricing.image_cost(None) == 0.039
    assert pricing.image_cost({}) == 0.039


def test_image_cost_from_gemini_tokens():
    # 1290 output tokens * $30 / 1M = $0.0387
    usd = pricing.image_cost({"promptTokenCount": 0, "candidatesTokenCount": 1290})
    assert abs(usd - 0.0387) < 1e-6


def test_text_cost_claude_tokens():
    # 1M in + 1M out = 15 + 75
    assert pricing.text_cost({"input_tokens": 1_000_000, "output_tokens": 1_000_000}) == 90.0
    assert pricing.text_cost({}) == 0.0


def test_video_cost_per_second():
    assert pricing.video_cost(10) == 1.0
    assert pricing.video_cost(0) == 0.0
    assert pricing.video_cost(None) == 0.0


def test_add_usd_ignores_none():
    assert pricing.add_usd(0.039, None, 0.039) == 0.078
