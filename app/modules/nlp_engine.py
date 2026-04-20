"""spaCy NER + lightweight rules → structured tags."""

from __future__ import annotations

import re
from typing import Any

_COLOR_WORDS = frozenset(
    "red blue green yellow orange purple pink black white gray grey brown beige "
    "navy teal maroon gold silver tan ivory".split()
)
_ITEM_HINTS = frozenset(
    "phone wallet keys bag backpack laptop jacket coat umbrella hat glasses "
    "watch ring necklace earring bracelet purse suitcase bottle water bottle "
    "book notebook tablet airpods headphones charger cable".split()
)

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is False:
        return None
    if _nlp is not None:
        return _nlp
    try:
        import spacy

        _nlp = spacy.load("en_core_web_sm")
    except Exception:
        _nlp = False
    return _nlp if _nlp is not False else None


def _rule_colors(text: str) -> list[str]:
    words = re.findall(r"\b[a-z]+\b", text.lower())
    return sorted({w for w in words if w in _COLOR_WORDS})


def _rule_items(text: str) -> list[str]:
    words = re.findall(r"\b[a-z]+\b", text.lower())
    found = {w for w in words if w in _ITEM_HINTS}
    bigrams = re.findall(r"\b[a-z]+(?:\s+[a-z]+)?\b", text.lower())
    for bg in bigrams:
        if bg in _ITEM_HINTS:
            found.add(bg.replace(" ", "_"))
    return sorted(found)


def extract_tags(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    out: dict[str, Any] = {
        "entities": {"GPE": [], "DATE": [], "PERSON": []},
        "colors": [],
        "keywords": [],
        "tokens": [],
    }
    if not text:
        return out

    nlp = _get_nlp()
    if nlp:
        doc = nlp(text[:100000])
        for ent in doc.ents:
            if ent.label_ == "GPE":
                out["entities"]["GPE"].append(ent.text.strip())
            elif ent.label_ == "DATE":
                out["entities"]["DATE"].append(ent.text.strip())
            elif ent.label_ == "PERSON":
                out["entities"]["PERSON"].append(ent.text.strip())
        out["tokens"] = [t.text.lower() for t in doc if t.is_alpha]

    out["colors"] = _rule_colors(text)
    out["keywords"] = _rule_items(text)
    return out


def merge_tags(*tag_dicts: dict | None) -> dict[str, Any]:
    merged = extract_tags("")
    for d in tag_dicts:
        if not d:
            continue
        for k in ("GPE", "DATE", "PERSON"):
            merged["entities"][k].extend((d.get("entities") or {}).get(k) or [])
        merged["colors"].extend(d.get("colors") or [])
        merged["keywords"].extend(d.get("keywords") or [])
        merged["tokens"].extend(d.get("tokens") or [])

    for k in ("GPE", "DATE", "PERSON"):
        merged["entities"][k] = sorted({x for x in merged["entities"][k] if x})
    merged["colors"] = sorted({x for x in merged["colors"] if x})
    merged["keywords"] = sorted({x for x in merged["keywords"] if x})
    merged["tokens"] = sorted({x for x in merged["tokens"] if x})
    return merged


def jaccard_from_tags(a: dict | None, b: dict | None) -> float:
    if not a or not b:
        return 0.5

    def bag(d: dict) -> set[str]:
        s: set[str] = set()
        for k in ("GPE", "DATE", "PERSON"):
            for x in (d.get("entities") or {}).get(k) or []:
                s.add(f"{k}:{x.lower()}")
        for x in d.get("colors") or []:
            s.add(f"c:{x.lower()}")
        for x in d.get("keywords") or []:
            s.add(f"k:{x.lower()}")
        for t in (d.get("tokens") or [])[:80]:
            if len(t) > 2:
                s.add(f"t:{t.lower()}")
        return s

    sa, sb = bag(a), bag(b)
    if not sa and not sb:
        return 0.5
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.5
