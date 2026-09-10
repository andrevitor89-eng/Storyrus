"""Avalia historias no Opik (dataset + experimento).

Uso (com OPIK_API_KEY ou OPIK_URL_OVERRIDE e ANTHROPIC_API_KEY / GEMINI_API_KEY):

    cd backend && python scripts/eval_story_opik.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai_clients.text_anthropic import AnthropicTextProvider
from app.observability.opik_trace import configure, enabled
from app.observability.story_judge import SCORE_KEYS, score_story

DATASET_NAME = "story-r-us-briefs"
EXPERIMENT_NAME = "story-judge"

_SAMPLE_ITEMS = [
    {
        "brief": (
            "Invente uma historia ORIGINAL no tema 'oceano' para a crianca chamada "
            "Nina, 5 anos. Ela e curiosa e adora conchas. Ensine 2 ou 3 curiosidades "
            "reais do mar de forma ludica."
        ),
        "theme": "oceano",
        "age": 5,
        "language": "pt-BR",
        "pages": 8,
    },
    {
        "brief": (
            "Invent an original story in the theme 'forest' for a child named Leo, "
            "age 4. He is shy and loves birds. Teach 2 or 3 real forest facts playfully."
        ),
        "theme": "forest",
        "age": 4,
        "language": "en",
        "pages": 8,
    },
]


def _ensure_dataset(client: Any):
    try:
        dataset = client.get_dataset(name=DATASET_NAME)
    except Exception:  # noqa: BLE001 - dataset ainda nao existe
        dataset = client.create_dataset(
            name=DATASET_NAME,
            description="Briefs de historia infantil para o juiz Opik",
        )
        dataset.insert(_SAMPLE_ITEMS)
        print(f"[eval] dataset criado: {DATASET_NAME} ({len(_SAMPLE_ITEMS)} itens)")
        return dataset
    try:
        existing = list(dataset.get_items())
    except Exception:  # noqa: BLE001
        existing = []
    if not existing:
        dataset.insert(_SAMPLE_ITEMS)
        print(f"[eval] dataset vazio; inseridos {len(_SAMPLE_ITEMS)} itens")
    else:
        print(f"[eval] dataset {DATASET_NAME}: {len(existing)} itens")
    return dataset


def evaluation_task(item: dict[str, Any]) -> dict[str, Any]:
    async def _run() -> dict[str, Any]:
        provider = AnthropicTextProvider()
        pages = int(item.get("pages") or 8)
        language = item.get("language") or "pt-BR"
        age = item.get("age")
        theme = item.get("theme") or ""
        brief = item.get("brief") or ""
        result = await provider.generate_story(
            brief=brief,
            style="realistic storybook",
            pages=pages,
            language=language,
            age=age,
        )
        scores = await score_story(
            brief=brief,
            story=result.text,
            age=age,
            language=language,
            theme=theme,
        ) or {}
        return {
            "input": brief,
            "output": result.text,
            "coherence": scores.get("coherence"),
            "age_fit": scores.get("age_fit"),
            "education": scores.get("education"),
            "format": scores.get("format"),
            "reason": scores.get("reason") or "",
        }

    return asyncio.run(_run())


def _story_metric():
    from opik.evaluation.metrics import base_metric, score_result

    class StoryScoresMetric(base_metric.BaseMetric):
        def __init__(self) -> None:
            super().__init__(name="story_scores")

        def score(self, **kwargs: Any):
            reason = str(kwargs.get("reason") or "")
            results = []
            for key in SCORE_KEYS:
                value = kwargs.get(key)
                if value is None:
                    continue
                results.append(
                    score_result.ScoreResult(
                        name=key, value=float(value), reason=reason
                    )
                )
            return results

    return StoryScoresMetric()


def main() -> int:
    configure()
    if not enabled():
        print("Opik desligado. Defina OPIK_API_KEY (Cloud) ou OPIK_URL_OVERRIDE.")
        return 1

    from opik import Opik
    from opik.evaluation import evaluate

    client = Opik()
    dataset = _ensure_dataset(client)
    print(f"[eval] experimento {EXPERIMENT_NAME}…")
    evaluate(
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=[_story_metric()],
        experiment_name=EXPERIMENT_NAME,
    )
    print("[eval] concluido — veja o experimento no dashboard do Opik")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
