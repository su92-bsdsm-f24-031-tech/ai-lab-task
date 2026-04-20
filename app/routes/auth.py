from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app import db
from app.models import User

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("items.index"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        password2 = request.form.get("password_confirm") or ""
        if not username or not email or len(password) < 6:
            flash("Username, email, and password (6+ chars) required.", "error")
            return render_template("auth/register.html")
        if password != password2:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html")
        user = User(username=username, email=email)
        user.set_password(password)
        if username in (current_app.config.get("ADMIN_USERNAMES") or []):
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome! Your account is ready.", "success")
        return redirect(url_for("items.index"))
    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("items.index"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("auth/login.html")
        login_user(user, remember=True)
        flash("Welcome back! You're signed in.", "success")
        next_url = request.args.get("next") or request.form.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        return redirect(url_for("items.index"))
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("items.index"))
