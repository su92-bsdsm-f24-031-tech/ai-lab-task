import importlib
from pathlib import Path

from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    instance_path = Path(app.root_path).parent / "instance"
    instance_path.mkdir(parents=True, exist_ok=True)
    upload_dir = Path(app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    importlib.import_module("app.models")

    with app.app_context():
        db.create_all()
        _migrate_sqlite_schema(app)
        _sync_admin_users(app)

    from app.routes.admin import bp as admin_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.items import bp as items_bp
    from app.routes.match import bp as match_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(match_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    return app


def _migrate_sqlite_schema(app):
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        return
    engine = db.engine
    insp = inspect(engine)
    try:
        user_cols = {c["name"] for c in insp.get_columns("users")}
    except Exception:
        user_cols = set()
    try:
        item_cols = {c["name"] for c in insp.get_columns("items")}
    except Exception:
        item_cols = set()
    with engine.connect() as conn:
        if "is_admin" not in user_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
        if "contact_phone" not in item_cols:
            conn.execute(text("ALTER TABLE items ADD COLUMN contact_phone VARCHAR(11)"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_items_created_at ON items (created_at)"
            )
        )
        conn.commit()


def _sync_admin_users(app):
    from app.models import User

    names = app.config.get("ADMIN_USERNAMES") or []
    if not names:
        return
    changed = False
    for username in names:
        u = User.query.filter_by(username=username).first()
        if u and not u.is_admin:
            u.is_admin = True
            changed = True
    if changed:
        db.session.commit()
