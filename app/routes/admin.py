from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, or_

from app import db
from app.models import Item, Match, User
from app.utils.access import admin_required, user_is_admin

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _delete_item_files(item: Item) -> None:
    if not item.image_path:
        return
    from flask import current_app

    p = Path(current_app.config["UPLOAD_FOLDER"]) / item.image_path
    try:
        if p.is_file():
            p.unlink()
    except OSError:
        pass


def _delete_item_graph(item_id: int) -> bool:
    item = db.session.get(Item, item_id)
    if item is None:
        return False
    Match.query.filter(
        or_(Match.lost_item_id == item_id, Match.found_item_id == item_id)
    ).delete(synchronize_session=False)
    _delete_item_files(item)
    db.session.delete(item)
    return True


@bp.route("/")
@admin_required
def index():
    n_users = db.session.scalar(func.count(User.id)) or 0
    n_items = db.session.scalar(func.count(Item.id)) or 0
    n_lost = Item.query.filter_by(type="lost").count()
    n_found = Item.query.filter_by(type="found").count()
    n_matches = db.session.scalar(func.count(Match.id)) or 0
    return render_template(
        "admin/dashboard.html",
        stats={
            "users": n_users,
            "items": n_items,
            "lost": n_lost,
            "found": n_found,
            "matches": n_matches,
        },
    )


@bp.route("/items")
@admin_required
def items_list():
    page = request.args.get("page", 1, type=int)
    per = 25
    q = Item.query.order_by(Item.created_at.desc())
    items = q.paginate(page=page, per_page=per, error_out=False)
    return render_template("admin/items.html", items=items)


@bp.route("/items/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_item(item_id):
    if _delete_item_graph(item_id):
        db.session.commit()
        flash("Item deleted.", "success")
    else:
        db.session.rollback()
        flash("Item not found.", "error")
    return redirect(url_for("admin.items_list"))


@bp.route("/items/<int:item_id>/toggle", methods=["POST"])
@admin_required
def toggle_resolved(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        flash("Item not found.", "error")
        return redirect(url_for("admin.items_list"))
    item.is_resolved = not item.is_resolved
    db.session.commit()
    flash("Listing updated.", "success")
    return redirect(url_for("admin.items_list"))


@bp.route("/users")
@admin_required
def users_list():
    page = request.args.get("page", 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template("admin/users.html", users=users)


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account from here.", "error")
        return redirect(url_for("admin.users_list"))
    user = db.session.get(User, user_id)
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("admin.users_list"))
    try:
        for item in Item.query.filter_by(user_id=user_id).all():
            _delete_item_graph(item.id)
        db.session.delete(user)
        db.session.commit()
        flash("User and their listings removed.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not delete user.", "error")
    return redirect(url_for("admin.users_list"))


@bp.context_processor
def inject_admin():
    return {"user_is_admin": lambda: user_is_admin(current_user)}
