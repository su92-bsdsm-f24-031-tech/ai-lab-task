"""Run vision, GenAI description, and NLP extraction after an item is saved."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flask import current_app

from app import db
from app.modules.genai_engine import GenAIEngine, tags_summary
from app.modules.nlp_engine import extract_tags, merge_tags
from app.modules.vision_engine import extract_features

if TYPE_CHECKING:
    from app.models import Item


def enrich_item(item: Item) -> None:
    """Populate vision_features, ai_description, nlp_tags on ``item``."""
    texts_for_nlp: list[str] = [item.title, item.description]

    if item.image_path:
        upload_root = Path(current_app.config["UPLOAD_FOLDER"])
        abs_path = upload_root / item.image_path
        item.vision_features = extract_features(abs_path)

        engine = GenAIEngine(
            current_app.config.get("GEMINI_API_KEY", ""),
            current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash"),
        )
        desc = engine.describe_image(abs_path)
        if desc:
            item.ai_description = desc
            texts_for_nlp.append(desc)

    base = extract_tags("\n".join(texts_for_nlp))
    item.nlp_tags = base
    if item.ai_description:
        item.nlp_tags = merge_tags(base, extract_tags(item.ai_description))

    db.session.add(item)
