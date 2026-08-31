import uuid
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def _token():
    return uuid.uuid4().hex


def _now():
    return datetime.now(timezone.utc)


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)
    collaborator_form_token = db.Column(db.String(32), unique=True, default=_token, nullable=False)
    help_form_token = db.Column(db.String(32), unique=True, default=_token, nullable=False)
    auto_match_enabled = db.Column(db.Boolean, default=False, nullable=False)

    users = db.relationship("User", backref="organization", cascade="all, delete-orphan")
    collaborators = db.relationship("Collaborator", backref="organization", cascade="all, delete-orphan")
    help_requests = db.relationship("HelpRequest", backref="organization", cascade="all, delete-orphan")
    catalog_items = db.relationship("CatalogItem", backref="organization", cascade="all, delete-orphan")
    offers = db.relationship("Offer", backref="organization", cascade="all, delete-orphan")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    theme = db.Column(db.String(10), default="claro", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Collaborator(db.Model):
    __tablename__ = "collaborators"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    area = db.Column(db.String(150))
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    offers = db.relationship("Offer", backref="collaborator", cascade="all, delete-orphan")


DEFAULT_CATALOG = [
    ("Alimento", "Arroz"),
    ("Alimento", "Feijão"),
    ("Alimento", "Óleo"),
    ("Alimento", "Leite"),
    ("Alimento", "Macarrão"),
    ("Roupa", "Roupa infantil"),
    ("Roupa", "Roupa adulto"),
    ("Roupa", "Calçado"),
    ("Higiene", "Sabonete"),
    ("Higiene", "Fralda"),
    ("Higiene", "Absorvente"),
    ("Higiene", "Papel higiênico"),
    ("Financeiro", "Doação em dinheiro"),
    ("Outro", "Outros itens"),
]


class CatalogItem(db.Model):
    __tablename__ = "catalog_items"
    __table_args__ = (db.UniqueConstraint("organization_id", "category", "name"),)

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    help_requests = db.relationship("HelpRequest", backref="item")
    offers = db.relationship("Offer", backref="item")


class HelpRequest(db.Model):
    __tablename__ = "help_requests"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("catalog_items.id"), nullable=False)
    requester_name = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(150))
    quantity = db.Column(db.Integer, default=1, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="pendente", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    fulfilled_by_offer = db.relationship(
        "Offer", back_populates="matched_help_request", uselist=False,
        foreign_keys="Offer.matched_help_request_id",
    )


class Offer(db.Model):
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    collaborator_id = db.Column(db.Integer, db.ForeignKey("collaborators.id"), nullable=False)
    offer_type = db.Column(db.String(20), nullable=False)  # "item" ou "tempo_voluntario"
    item_id = db.Column(db.Integer, db.ForeignKey("catalog_items.id"))
    quantity = db.Column(db.Integer)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="disponivel", nullable=False)
    matched_help_request_id = db.Column(db.Integer, db.ForeignKey("help_requests.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

    matched_help_request = db.relationship(
        "HelpRequest", back_populates="fulfilled_by_offer", foreign_keys=[matched_help_request_id]
    )
