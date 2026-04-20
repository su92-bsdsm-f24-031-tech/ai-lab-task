import uuid
from datetime import datetime, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import and_, func, or_
from werkzeug.utils import secure_filename

from app import db
from app.models import Item, Match, User
from app.modules.item_pipeline import enrich_item
from app.modules.nlp_engine import extract_tags
from app.utils.phone import is_valid_contact_phone, normalize_contact_phone

bp = Blueprint("items", __name__)

ITEMS_PER_PAGE = 15
DASHBOARD_LISTINGS_LIMIT = 25
DASHBOARD_MATCHES_LIMIT = 30


def _viewer_can_see_item_contact_phone(viewer_id: int, item_id: int) -> bool:
    """Owner always; others only if a Match links this item to one of the viewer's items."""
    if (
        db.session.query(Item.id)
        .filter(Item.id == item_id, Item.user_id == viewer_id)
        .first()
        is not None
    ):
        return True
    if Item.query.filter_by(user_id=viewer_id).first() is None:
        return False
    my_item_ids = db.session.query(Item.id).filter(Item.user_id == viewer_id)
    return (
        Match.query.filter(
            or_(
                and_(Match.lost_item_id == item_id, Match.found_item_id.in_(my_item_ids)),
                and_(Match.found_item_id == item_id, Match.lost_item_id.in_(my_item_ids)),
            )
        ).first()
        is not None
    )


def _allowed_file(name: str) -> bool:
    return "." in name and name.rsplit(".", 1)[1].lower() in {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
    }


def _item_listing_query(q: str, item_type: str | None, category: str | None):
    query = Item.query.filter_by(is_resolved=False)
    if item_type in ("lost", "found"):
        query = query.filter_by(type=item_type)
    if category:
        c = category.strip()
        if c:
            query = query.filter(Item.category.ilike(f"%{c}%"))
    if q:
        terms = [t for t in q.split() if len(t) > 1]
        tags = extract_tags(q)
        extra = []
        for k in ("colors", "keywords"):
            extra.extend(tags.get(k) or [])
        all_terms = list({*terms, *[e for e in extra if len(e) > 1]})
        if all_terms:
            term_filters = []
            for t in all_terms[:12]:
                like = f"%{t}%"
                term_filters.append(
                    or_(
                        Item.title.ilike(like),
                        Item.description.ilike(like),
                        Item.location.ilike(like),
                        Item.category.ilike(like),
                        Item.ai_description.ilike(like),
                    )
                )
            query = query.filter(or_(*term_filters))
    return query.order_by(Item.created_at.desc())


def _distinct_categories():
    rows = (
        db.session.query(Item.category)
        .filter(Item.category != "")
        .filter(Item.is_resolved.is_(False))
        .distinct()
        .limit(40)
        .all()
    )
    return sorted({r[0] for r in rows if r[0]})


def _listing_url_kwargs(
    *,
    q: str,
    category: str,
    item_type: str | None,
    listing_endpoint: str,
) -> dict:
    """Query args to preserve across pagination (omit empty)."""
    d: dict = {}
    if q:
        d["q"] = q
    if category:
        d["category"] = category
    if listing_endpoint == "items.index" and item_type in ("lost", "found"):
        d["type"] = item_type
    return d


def _render_listing(
    *,
    q: str,
    item_type: str | None,
    category: str,
    show_hero: bool,
    page_title: str,
    listing_endpoint: str,
):
    page = request.args.get("page", 1, type=int) or 1
    if page < 1:
        page = 1

    query = _item_listing_query(q, item_type, category)
    pagination = query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    categories = _distinct_categories()
    url_kwargs = _listing_url_kwargs(
        q=q,
        category=category,
        item_type=item_type,
        listing_endpoint=listing_endpoint,
    )
    return render_template(
        "index.html",
        items=pagination.items,
        pagination=pagination,
        list_url_kwargs=url_kwargs,
        q=q,
        category_filter=category,
        type_filter=item_type,
        categories=categories,
        show_hero=show_hero,
        page_title=page_title,
        listing_endpoint=listing_endpoint,
    )


@bp.route("/")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    t = request.args.get("type")
    if t not in (None, "", "lost", "found"):
        t = None
    if t == "":
        t = None
    return _render_listing(
        q=q,
        item_type=t,
        category=category,
        show_hero=True,
        page_title="Home",
        listing_endpoint="items.index",
    )


@bp.route("/lost-items")
@login_required
def lost_items():
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    return _render_listing(
        q=q,
        item_type="lost",
        category=category,
        show_hero=False,
        page_title="Lost items",
        listing_endpoint="items.lost_items",
    )


@bp.route("/found-items")
@login_required
def found_items():
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    return _render_listing(
        q=q,
        item_type="found",
        category=category,
        show_hero=False,
        page_title="Found items",
        listing_endpoint="items.found_items",
    )


@bp.route("/report/lost", methods=["GET", "POST"])
@login_required
def report_lost():
    if request.method == "POST":
        return _save_item("lost")
    return render_template("items/report_lost.html")


@bp.route("/report/found", methods=["GET", "POST"])
@login_required
def report_found():
    if request.method == "POST":
        return _save_item("found")
    return render_template("items/report_found.html")


def _save_item(kind: str):
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    location = (request.form.get("location") or "").strip()
    category = (request.form.get("category") or "").strip()
    phone_raw = request.form.get("contact_phone")
    if not title:
        flash("Title is required.", "error")
        tpl = (
            "items/report_lost.html"
            if kind == "lost"
            else "items/report_found.html"
        )
        return render_template(tpl)
    if not is_valid_contact_phone(phone_raw):
        flash("Contact phone must be up to 11 digits (numbers only).", "error")
        tpl = (
            "items/report_lost.html"
            if kind == "lost"
            else "items/report_found.html"
        )
        return render_template(tpl)

    item = Item(
        user_id=current_user.id,
        type=kind,
        title=title,
        description=description,
        location=location,
        category=category,
        contact_phone=normalize_contact_phone(phone_raw),
    )
    db.session.add(item)
    db.session.flush()

    f = request.files.get("image")
    if f and f.filename and _allowed_file(f.filename):
        ext = secure_filename(f.filename).rsplit(".", 1)[-1].lower()
        unique = f"{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"
        path = current_app.config["UPLOAD_FOLDER"] / unique
        f.save(path)
        item.image_path = unique

    enrich_item(item)
    db.session.commit()
    flash(
        "Item saved. You can view possible matches from the item page or dashboard.",
        "success",
    )
    return redirect(url_for("items.item_detail", item_id=item.id))


@bp.route("/item/<int:item_id>")
@login_required
def item_detail(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        abort(404)
    owner = db.session.get(User, item.user_id)
    show_contact = bool(
        item.contact_phone
        and _viewer_can_see_item_contact_phone(current_user.id, item.id)
    )
    return render_template(
        "items/detail.html",
        item=item,
        owner=owner,
        show_contact_phone=show_contact,
    )


@bp.route("/dashboard")
@login_required
def dashboard():
    uid = current_user.id
    stat_n_items = Item.query.filter_by(user_id=uid).count()
    stat_n_lost = Item.query.filter_by(user_id=uid, type="lost").count()
    stat_n_found = Item.query.filter_by(user_id=uid, type="found").count()

    my_ids_sq = db.session.query(Item.id).filter(Item.user_id == uid)
    # Align with match engine “strong” threshold (see match.STRONG_THRESHOLD)
    stat_n_matches = (
        db.session.query(func.count(Match.id))
        .filter(
            Match.match_score >= 0.75,
            or_(
                Match.lost_item_id.in_(my_ids_sq),
                Match.found_item_id.in_(my_ids_sq),
            ),
        )
        .scalar()
        or 0
    )

    my_items = (
        Item.query.filter_by(user_id=uid)
        .order_by(Item.created_at.desc())
        .limit(DASHBOARD_LISTINGS_LIMIT)
        .all()
    )

    matches = (
        Match.query.filter(
            or_(
                Match.lost_item_id.in_(my_ids_sq),
                Match.found_item_id.in_(my_ids_sq),
            )
        )
        .order_by(Match.match_score.desc())
        .limit(DASHBOARD_MATCHES_LIMIT)
        .all()
    )

    return render_template(
        "items/dashboard.html",
        items=my_items,
        matches=matches,
        stat_n_items=stat_n_items,
        stat_n_matches=stat_n_matches,
        stat_n_lost=stat_n_lost,
        stat_n_found=stat_n_found,
    )
