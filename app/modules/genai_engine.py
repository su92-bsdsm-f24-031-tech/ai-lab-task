"""Gemini: image captioning and pairwise match score. Optional when API key missing."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from PIL import Image


class GenAIEngine:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        *,
        pair_scorer: Callable[[str, str, str, str], tuple[float, str]] | None = None,
    ):
        self._enabled = bool(api_key)
        self._model_name = model_name
        self._pair_scorer = pair_scorer
        self._api_key = api_key
        self._model = None

    def _ensure_model(self):
        if self._model is not None or not self._enabled:
            return
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        self._model = genai.GenerativeModel(self._model_name)

    def describe_image(self, image_path: str | Path) -> str | None:
        if not self._enabled:
            return None
        self._ensure_model()
        if self._model is None:
            return None
        path = Path(image_path)
        if not path.is_file():
            return None
        try:
            img = Image.open(path).convert("RGB")
            prompt = (
                "Describe this object for a lost-and-found listing in 2 short sentences. "
                "Focus on object type, color, material, and distinguishing marks. "
                "No preamble."
            )
            resp = self._model.generate_content([prompt, img])
            return (resp.text or "").strip() or None
        except Exception:
            return None

    def score_pair(
        self,
        text_a: str,
        text_b: str,
        tags_a: str = "",
        tags_b: str = "",
    ) -> tuple[float, str]:
        if self._pair_scorer:
            return self._pair_scorer(text_a, text_b, tags_a, tags_b)
        if not self._enabled:
            return 0.5, "GenAI disabled (no API key or error)."
        self._ensure_model()
        if self._model is None:
            return 0.5, "GenAI disabled (no API key or error)."

        prompt = f"""You compare two lost-and-found item descriptions.
Return ONLY valid JSON with keys "score" (number 0-1) and "reason" (one short sentence).

Item A:
{text_a or "(empty)"}
Tags A: {tags_a or "(none)"}

Item B:
{text_b or "(empty)"}
Tags B: {tags_b or "(none)"}

Score 1.0 if very likely the same item, 0.0 if clearly different."""
        try:
            resp = self._model.generate_content(prompt)
            raw = (resp.text or "").strip()
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return 0.5, "Could not parse model response."
            data = json.loads(m.group())
            score = float(data.get("score", 0.5))
            reason = str(data.get("reason", "")).strip() or "No reason given."
            return max(0.0, min(1.0, score)), reason
        except Exception:
            return 0.5, "GenAI scoring failed."


def tags_summary(tags: dict[str, Any] | None) -> str:
    if not tags:
        return ""
    parts = []
    ent = tags.get("entities") or {}
    if ent.get("GPE"):
        parts.append("places: " + ", ".join(ent["GPE"]))
    if ent.get("DATE"):
        parts.append("dates: " + ", ".join(ent["DATE"]))
    if tags.get("colors"):
        parts.append("colors: " + ", ".join(tags["colors"]))
    if tags.get("keywords"):
        parts.append("keywords: " + ", ".join(tags["keywords"]))
    return "; ".join(parts)
