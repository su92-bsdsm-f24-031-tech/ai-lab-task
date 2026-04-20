from functools import wraps

from flask import abort, current_app, redirect, url_for
from flask_login import current_user


def user_is_admin(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_admin", False):
        return True
    names = current_app.config.get("ADMIN_USERNAMES") or []
    return user.username in names


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=url_for("admin.index")))
        if not user_is_admin(current_user):
            abort(403)
        return f(*args, **kwargs)

    return wrapped
