"""Combine NLP, vision, and GenAI sub-scores: 0.35 NLP + 0.30 CV + 0.35 GenAI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from app.modules.nlp_engine import jaccard_from_tags
from app.modules.vision_engine import histogram_similarity

if TYPE_CHECKING:
    from app.models import Item


@dataclass
class SubScores:
    nlp: float
    cv: float
    genai: float
    genai_reason: str


GenAIPairFn = Callable[[str, str, str, str], tuple[float, str]]


def final_score(nlp: float, cv: float, genai: float) -> float:
    return 0.35 * nlp + 0.30 * cv + 0.35 * genai


def score_items(
    anchor: Item,
    candidate: Item,
    *,
    genai_fn: GenAIPairFn | None = None,
) -> tuple[float, SubScores]:
    nlp = jaccard_from_tags(anchor.nlp_tags, candidate.nlp_tags)
    cv = histogram_similarity(anchor.vision_features, candidate.vision_features)

    text_a = " ".join(
        filter(
            None,
            [anchor.title, anchor.description, anchor.ai_description or ""],
        )
    ).strip()
    text_b = " ".join(
        filter(
            None,
            [candidate.title, candidate.description, candidate.ai_description or ""],
        )
    ).strip()

    tags_a = _tags_line(anchor.nlp_tags)
    tags_b = _tags_line(candidate.nlp_tags)

    if genai_fn:
        g, reason = genai_fn(text_a, text_b, tags_a, tags_b)
    else:
        g, reason = 0.5, "GenAI not configured."

    subs = SubScores(nlp=nlp, cv=cv, genai=g, genai_reason=reason)
    return final_score(nlp, cv, g), subs


def _tags_line(tags: dict[str, Any] | None) -> str:
    if not tags:
        return ""
    parts = []
    ent = tags.get("entities") or {}
    for k in ("GPE", "DATE"):
        if ent.get(k):
            parts.append(f"{k}: {', '.join(ent[k])}")
    if tags.get("colors"):
        parts.append("colors: " + ", ".join(tags["colors"]))
    if tags.get("keywords"):
        parts.append("keywords: " + ", ".join(tags["keywords"]))
    return "; ".join(parts)
