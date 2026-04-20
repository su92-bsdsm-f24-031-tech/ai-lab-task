from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    items = db.relationship("Item", backref="owner", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(16), nullable=False, index=True)  # "lost" | "found"
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    location = db.Column(db.String(200), nullable=False, default="")
    category = db.Column(db.String(100), nullable=False, default="")
    contact_phone = db.Column(db.String(11), nullable=True)
    image_path = db.Column(db.String(512), nullable=True)
    nlp_tags = db.Column(db.JSON, nullable=True)
    vision_features = db.Column(db.JSON, nullable=True)
    ai_description = db.Column(db.Text, nullable=True)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    matches_as_lost = db.relationship(
        "Match",
        foreign_keys="Match.lost_item_id",
        backref="lost_item",
        lazy="dynamic",
    )
    matches_as_found = db.relationship(
        "Match",
        foreign_keys="Match.found_item_id",
        backref="found_item",
        lazy="dynamic",
    )


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    found_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    genai_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "lost_item_id", "found_item_id", name="uq_match_lost_found"
        ),
    )
