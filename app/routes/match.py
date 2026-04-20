from flask import Blueprint, abort, current_app, render_template
from flask_login import login_required

from app import db
from app.models import Item, Match
from app.modules.genai_engine import GenAIEngine, tags_summary
from app.modules.match_scorer import SubScores, score_items
from app.modules.nlp_engine import jaccard_from_tags
from app.modules.vision_engine import histogram_similarity

bp = Blueprint("match", __name__)

STRONG_THRESHOLD = 0.75
GENAI_TOP_K = 25
# Cap opposite-type rows loaded from DB (prefilter + score); keeps match page fast at scale.
MAX_OPPOSITE_CANDIDATES = 300


def _prefilter(anchor: Item, candidate: Item) -> float:
    nlp = jaccard_from_tags(anchor.nlp_tags, candidate.nlp_tags)
    cv = histogram_similarity(anchor.vision_features, candidate.vision_features)
    return 0.35 * nlp + 0.30 * cv + 0.35 * 0.5


def _ordered_pair(anchor: Item, other: Item) -> tuple[int, int]:
    if anchor.type == "lost" and other.type == "found":
        return anchor.id, other.id
    if anchor.type == "found" and other.type == "lost":
        return other.id, anchor.id
    raise ValueError("Mismatched item types for match row")


def _persist_strong(anchor: Item, candidate: Item, final: float, reason: str) -> None:
    if final < STRONG_THRESHOLD:
        return
    lost_id, found_id = _ordered_pair(anchor, candidate)
    existing = Match.query.filter_by(
        lost_item_id=lost_id, found_item_id=found_id
    ).first()
    if existing:
        if final > existing.match_score:
            existing.match_score = final
            existing.genai_reason = reason
    else:
        m = Match(
            lost_item_id=lost_id,
            found_item_id=found_id,
            match_score=final,
            genai_reason=reason,
        )
        db.session.add(m)


@bp.route("/results/<int:item_id>")
@login_required
def results(item_id):
    anchor = db.session.get(Item, item_id)
    if anchor is None:
        abort(404)

    opposite = "found" if anchor.type == "lost" else "lost"
    candidates = (
        Item.query.filter(
            Item.type == opposite,
            Item.is_resolved.is_(False),
            Item.id != anchor.id,
        )
        .order_by(Item.created_at.desc())
        .limit(MAX_OPPOSITE_CANDIDATES)
        .all()
    )

    scored_pref = [( _prefilter(anchor, c), c) for c in candidates]
    scored_pref.sort(key=lambda x: -x[0])
    shortlist = [c for _, c in scored_pref[:GENAI_TOP_K]]

    engine = GenAIEngine(
        current_app.config.get("GEMINI_API_KEY", ""),
        current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash"),
    )

    def genai_fn(a, b, ta, tb):
        return engine.score_pair(a, b, ta, tb)

    rows = []
    for c in shortlist:
        final, subs = score_items(anchor, c, genai_fn=genai_fn)
        _persist_strong(anchor, c, final, subs.genai_reason)
        rows.append(
            {
                "item": c,
                "final": final,
                "subs": subs,
            }
        )
    db.session.commit()

    rows.sort(key=lambda r: -r["final"])

    rest = [c for _, c in scored_pref[GENAI_TOP_K:]]
    for c in rest:
        nlp = jaccard_from_tags(anchor.nlp_tags, c.nlp_tags)
        cv = histogram_similarity(anchor.vision_features, c.vision_features)
        final = 0.35 * nlp + 0.30 * cv + 0.35 * 0.5
        rows.append(
            {
                "item": c,
                "final": final,
                "subs": SubScores(
                    nlp=nlp,
                    cv=cv,
                    genai=0.5,
                    genai_reason="Not scored with GenAI (outside top candidates).",
                ),
            }
        )
    rows.sort(key=lambda r: -r["final"])

    return render_template(
        "match/results.html",
        anchor=anchor,
        rows=rows,
        tags_summary=tags_summary,
    )
